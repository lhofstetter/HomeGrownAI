import os
import sys
from collections.abc import AsyncGenerator, Iterable
from pathlib import Path
from sysconfig import get_path
from uuid import uuid4

if sys.platform == "darwin":
    os.environ["VLLM_LOGGING_LEVEL"] = "ERROR"
    os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"

if sys.platform == "linux":
    amd_smi_directory = Path(get_path("purelib")) / "_rocm_sdk_core/share/amd_smi"
    if amd_smi_directory.is_dir():
        # Update this interpreter and the environment inherited by subprocesses.
        amd_smi_path = str(amd_smi_directory)
        if amd_smi_path not in sys.path:
            sys.path.insert(0, amd_smi_path)
        python_paths = os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if amd_smi_path not in python_paths:
            os.environ["PYTHONPATH"] = os.pathsep.join(
                [amd_smi_path, *(path for path in python_paths if path)]
            )
    os.environ["FLASH_ATTENTION_TRITON_AMD_ENABLE"] = "TRUE"
    os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
    os.environ["VLLM_LOGGING_LEVEL"] = "ERROR"

import pymupdf4llm
from huggingface_hub import HfApi, ModelInfo
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from markitdown import MarkItDown
from torch import cuda, mps, version, xpu
from vllm import (
    AsyncEngineArgs,
    AsyncLLMEngine,
    PoolingParams,
    SamplingParams,
    TextPrompt,
    TokensPrompt,
)
from vllm.config import CompilationConfig, CUDAGraphMode
from vllm.sampling_params import RequestOutputKind
from wenmode import Wenmode

from homegrownai.database.user import User
from homegrownai.exceptions import (
    AIAppError,
    EmptyConversationAttachmentsError,
    EmptyModelPathError,
    FileTypeMismatchError,
    InferenceEngineNotStartedError,
    ModelNotFoundError,
    WrongParameterEmbeddings,
)
from homegrownai.schemas.user import Conversation

PROMPT_DIRECTORY = Path(
    "/".join(str(Path(__file__).resolve()).split("/")[:-1]), "prompts", "system_prompts"
)
UTILITY_PROMPT_DIRECTORY = Path(
    "/".join(str(Path(__file__).resolve()).split("/")[:-1]), "prompts"
)


if not PROMPT_DIRECTORY.is_dir():
    raise AIAppError("system_prompts is not a directory!")
else:
    model_prompts = {}
    for directory in PROMPT_DIRECTORY.iterdir():
        if directory.is_dir():
            model_prompts[directory] = Path(PROMPT_DIRECTORY, directory)
        else:
            model_prompts["default"] = directory


class InferenceEngine:
    def __init__(
        self,
        model_path_on_hf: str,
        context_window_len: int = 16384,
        fast_startup: bool = True,
    ):
        self.model = self.__hf_lookup(model_path_on_hf)
        self.system_prompt = ""
        file_loader = FileSystemLoader(PROMPT_DIRECTORY)
        utility_prompt_loader = FileSystemLoader(UTILITY_PROMPT_DIRECTORY)
        self.env = Environment(loader=file_loader)
        self.utility_env = Environment(loader=utility_prompt_loader)
        self.template = self.env.get_template("generic.md.jinja")
        self.summary_template = self.utility_env.get_template(
            "summarization_prompt.md.jinja"
        )
        self.markitdown_converter = MarkItDown(enable_plugins=True)
        self.ast_parser = Wenmode(positions=True)

        if sys.platform == "darwin":
            self.embedding_model = "mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ"
        else:
            self.embedding_model = "Qwen/Qwen3-Embedding-0.6B"

        if self.model.config == None:
            quantization_method = None
        else:
            quantization_method = "bitsandbytes"

        self.__check_system_prompt_and_configure_quantization()

        self.engine_args = AsyncEngineArgs(
            model=model_path_on_hf,
            dtype="auto",
            enable_prefix_caching=True,
            trust_remote_code=False,
            kv_cache_dtype=self.supported_kv_quantization[-1],  # ty: ignore
            hf_token=True,
            quantization=quantization_method,
            max_model_len=context_window_len,
            max_num_seqs=2,
            disable_log_stats=True,
            language_model_only=True,
            compilation_config=CompilationConfig(
                cudagraph_mode=CUDAGraphMode.NONE,
            ),
            gpu_memory_utilization=0.84,
        )

        self.embedding_engine_args = AsyncEngineArgs(
            model=self.embedding_model,
            runner="pooling",
            dtype="auto",
            trust_remote_code=False,
            hf_token=True,
            max_model_len=2048,
            enable_prefix_caching=True,
            kv_cache_dtype=self.supported_kv_quantization[-1],  # ty: ignore
            max_num_seqs=1,
            gpu_memory_utilization=0.08,
        )

        if quantization_method is not None:
            self.engine_args.load_format = quantization_method

        self.engine_sampling_args = SamplingParams(
            temperature=1.0,
            top_p=0.95,
            top_k=20,
            min_p=0.0,
            presence_penalty=0.0,
            repetition_penalty=1.0,
            output_kind=RequestOutputKind.DELTA,
            max_tokens=None,
        )  # this is for Qwen/Qwen3.8-27B in particular

        self.embedding_pooling_args = PoolingParams(task="embed", use_activation=True)
        self.started = False

        if fast_startup:  # defers actual engine initialization to start() parameter
            return

        self.start()

    def __hf_lookup(self, model_path: str) -> ModelInfo:
        if len(model_path) == 0:
            raise EmptyModelPathError

        api = HfApi()

        model_results: Iterable[ModelInfo] = list(
            iter(api.list_models(search=model_path))
        )

        if len(model_results) == 0:
            raise ModelNotFoundError

        return model_results[0]

    def __check_system_prompt_and_configure_quantization(self) -> None:
        model_id = self.model.id.split(
            "/"
        )  # split the model id so that the lab/individual (provider) identifier is first, which is the directory name
        if (
            model_id[0] in model_prompts
            and Path(PROMPT_DIRECTORY, model_id[0]).is_dir()
        ):
            for prompt_file in Path(
                PROMPT_DIRECTORY, model_id[0]
            ).iterdir():  # this loop is designed to find the specific prompt override associated with this model (if needed/one exists)
                if prompt_file.name.removesuffix(".md.jinja") == model_id[1]:
                    self.additional_system_prompt_template = self.env.get_template(
                        str(prompt_file)
                    )
        if mps.is_available() or xpu.is_available():
            logger.info("Server is using a Metal or XPU backend!")
            self.supported_kv_quantization = ["fp8", "auto"]
        elif cuda.is_available() and version.hip:
            logger.info("Server is using a ROCm/HIP backend!")
            self.supported_kv_quantization = ["fp8", "fp8_e4m3"]
        elif cuda.is_available() and version.cuda:
            logger.info("Server is using a CUDA backend!")
            self.supported_kv_quantization = [
                "fp8",
                "fp8_e5m2",
                "fp8_e4m3",
            ]

    def start(self):
        self.engine = AsyncLLMEngine.from_engine_args(self.engine_args)
        self.embedding_engine = AsyncLLMEngine.from_engine_args(
            self.embedding_engine_args
        )
        self.tokenizer = self.engine.get_tokenizer()
        self.embedding_tokenizer = self.embedding_engine.get_tokenizer()

        self.converted_documents_directory = Path("converted_documents")
        if not self.converted_documents_directory.exists():
            self.converted_documents_directory.mkdir()
        self.conversations = {}
        self.reasoning_effort = "med"
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Query a live search browser for information. Returns a JSON-formatted list of results, ranked in order from highest to lowest.",
                    "parameters": {
                        "type": "string",
                        "description": "Search term(s) to search for. Search terms should be given as a normal, space seperated string without specific browser formatting.",
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "navigate_to_site",
                    "description": "Navigate to webpage. Returns the HTML of the webpage.",
                    "parameters": {
                        "type": "URL",
                        "description": "URL of website to navigate to.",
                    },
                },
            },
        ]
        self.started = True

    def shutdown(self):
        self.engine.shutdown()
        self.embedding_engine.shutdown()

    async def new_conversation(
        self, message: str, user: User
    ) -> AsyncGenerator[str | tuple[Conversation, str], None]:
        if not self.started:
            raise InferenceEngineNotStartedError

        template_items: dict[str, str] = {}

        if user.custom_model_name is not None:
            template_items["name"] = user.custom_model_name
        else:
            template_items["name"] = "Nova"

        if user.human_name is not None:
            template_items["human_name"] = user.human_name
        else:
            template_items["human_name"] = "User"

        if user.custom_model_instructions is not None:
            template_items["user_instructions"] = user.custom_model_instructions
        else:
            template_items["user_instructions"] = "The user has no custom instructions."

        system_prompt = self.template.render(
            name=template_items["name"],
            human_name=template_items["human_name"],
            user_instructions=template_items["user_instructions"],
            tools=self.tools,
        )

        if len(message) == 0:
            raise AIAppError("No message to produce text!")

        attachments = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        conversation = Conversation(
            conversationTitle="New Conversation",
            conversationID=str(uuid4()),
            modelID=self.engine.model_config.model,
            attachments=attachments,
        )

        formatted_conversation = self.tokenizer.apply_chat_template(
            attachments,  # ty: ignore
            tokenize=True,
            add_generation_prompt=True,
        )

        token_ids = formatted_conversation["input_ids"]  # ty: ignore

        if (
            self.engine.model_config.max_model_len - len(token_ids) <= 200
        ):  # compress/summarize the request as much as possible
            await self.summarize_conversation(conversation)
            attachments = conversation.attachments

            formatted_conversation = self.tokenizer.apply_chat_template(
                attachments,  # ty: ignore
                tokenize=True,
                add_generation_prompt=True,
            )
            token_ids = formatted_conversation["input_ids"]  # ty: ignore

        stage = 0

        async for output in self.engine.generate(
            TokensPrompt(prompt_token_ids=token_ids),
            self.engine_sampling_args,
            str(conversation.conversationID),
        ):
            if stage == 0:
                stage += 1
                yield (conversation, output.outputs[0].text)
            else:
                yield output.outputs[0].text

    async def reply(self, message: str, conversation: Conversation):
        if not self.started:
            raise InferenceEngineNotStartedError

        if len(message) == 0:
            raise AIAppError("No message to produce text!")
        elif conversation.attachments == None:
            raise AIAppError("No existing conversation to respond to!")
        else:
            conversation.attachments.append({"user": message})

            formatted_conversation = self.tokenizer.apply_chat_template(
                conversation.attachments,  # ty:ignore
                tokenize=True,
                add_generation_prompt=True,
            )

            token_ids = formatted_conversation["input_ids"]  # ty: ignore

            if (
                self.engine.model_config.max_model_len - len(token_ids) <= 200
            ):  # compress/summarize the request as much as possible
                await self.summarize_conversation(conversation)
                attachments = conversation.attachments

                formatted_conversation = self.tokenizer.apply_chat_template(
                    attachments,  # ty: ignore
                    tokenize=True,
                    add_generation_prompt=True,
                )
                token_ids = formatted_conversation["input_ids"]  # ty: ignore

            stage = 0

            async for output in self.engine.generate(
                TokensPrompt(prompt_token_ids=token_ids),
                self.engine_sampling_args,
                conversation.conversationID,  # ty: ignore
            ):
                if stage == 0:
                    stage += 1
                    yield (conversation, output.outputs[0].text)
                else:
                    yield output.outputs[0].text

    async def generate_embeddings(
        self,
        file_path_or_text: Path | str,
    ):
        if not self.started:
            raise InferenceEngineNotStartedError

        if not (isinstance(file_path_or_text, Path | str)):
            raise WrongParameterEmbeddings

        if (
            isinstance(file_path_or_text, Path)
            and file_path_or_text.exists()
            and file_path_or_text.is_file()
        ):
            markdown_txt = self.markitdown_converter.convert(file_path_or_text).markdown

            if len(markdown_txt) == 0:
                markdown_txt = pymupdf4llm.to_markdown(file_path_or_text)

            ast = self.ast_parser.parse(markdown_txt).to_ast()
        elif isinstance(file_path_or_text, str):
            ast = self.ast_parser.parse(file_path_or_text).to_ast()
        else:
            raise FileTypeMismatchError

        for i, child in enumerate(ast["children"]):
            text = " ".join(self.__unpack_child_ast(child))

            yield (
                text,
                self.embedding_engine.encode(
                    TextPrompt(prompt=text),
                    pooling_params=self.embedding_pooling_args,
                    request_id=str(uuid4()),
                ),
                child["position"],
                i == len(ast["children"]) - 1,
            )

    async def summarize_conversation(self, conversation: Conversation) -> Conversation:
        if conversation.attachments == None:
            raise EmptyConversationAttachmentsError

        conversation_str = ""

        for i in range(1, len(conversation.attachments)):
            if conversation.attachments[i]["role"] == "user":
                conversation_str += "User:\n" + conversation.attachments[i]["content"]
            elif conversation.attachments[i]["role"] == "system":
                conversation_str += "System:\n" + conversation.attachments[i]["content"]
            else:
                conversation_str += (
                    "Assistant:\n" + conversation.attachments[i]["content"]
                )

        summarize_conversation = [
            {
                "role": "system",
                "content": self.summary_template.render(message=conversation_str),
            },
        ]
        summarized_user_input_formatted = self.tokenizer.apply_chat_template(
            summarize_conversation,  # ty: ignore
            tokenize=True,
            add_generation_prompt=True,
        )

        summary = ""

        async for output in self.engine.generate(
            TokensPrompt(
                prompt_token_ids=summarized_user_input_formatted["input_ids"]  # ty: ignore
            ),
            self.engine_sampling_args,
            str(uuid4()),
        ):
            summary += output.outputs[0].text

        new_conversation_attachments = [
            {
                "role": "system",
                "content": conversation.attachments[0]["content"],
            },
            {
                "role": "system",
                "content": 'This is a summary of the conversation thus far. Do not refer to the conversation history as a summary or imply it has been summarized - simply use the summary as a way to "recall" the conversation and respond to the user\'s most recent query:\n'
                + summary,
            },
        ]
        conversation.attachments = new_conversation_attachments

        return conversation

    def __unpack_child_ast(self, node: dict) -> list:
        if "children" not in node:
            return [node["value"].strip()]

        children = []

        for child in node["children"]:
            if "children" in child:
                children.extend(self.__unpack_child_ast(child))
            else:
                children.append(child["value"].strip())

        return children
