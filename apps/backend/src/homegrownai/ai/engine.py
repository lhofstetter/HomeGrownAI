import os
from collections.abc import AsyncGenerator, Iterable
from pathlib import Path
from platform import system
from typing import Literal
from uuid import uuid4

if "darwin" in system().lower():
    os.environ["VLLM_LOGGING_LEVEL"] = "ERROR"
    os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
    os.environ["VLLM_METAL_USE_PAGED_ATTENTION"] = "1"


import pymupdf4llm
from anyio import open_file
from huggingface_hub import HfApi, ModelInfo
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from markdownify import markdownify as md
from markitdown import MarkItDown
from md2docx_python.src.docx2md_python import word_to_markdown
from torch import cuda, mps, version, xpu
from vllm import (
    AsyncEngineArgs,
    AsyncLLMEngine,
    PoolingParams,
    SamplingParams,
    TextPrompt,
    TokensPrompt,
)
from vllm.sampling_params import RequestOutputKind
from wenmode import Wenmode

from homegrownai.database.user import User
from homegrownai.exceptions import AIAppError, FileTypeMismatchError
from homegrownai.schemas.user import Conversation

PROMPT_DIRECTORY = Path(
    "/".join(str(Path(__file__).resolve()).split("/")[:-1]), "system_prompts"
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
    def __init__(self, model_path_on_hf: str):
        self.api = HfApi()
        self.system_prompt = ""

        model_results: Iterable[ModelInfo] = self.api.list_models(
            search=model_path_on_hf
        )
        model_results = iter(model_results)
        first_model_result = next(model_results)

        file_loader = FileSystemLoader(PROMPT_DIRECTORY)
        self.env = Environment(loader=file_loader)
        self.template = self.env.get_template("generic.md.jinja")
        self.markitdown_converter = MarkItDown(enable_plugins=False)
        self.ast_parser = Wenmode(positions=True)

        model_id = first_model_result.id.split(
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
                    if first_model_result.pipeline_tag == None or (
                        first_model_result.pipeline_tag != None
                        and first_model_result.pipeline_tag != "text-generation"
                    ):
                        with logger.contextualize(model=first_model_result.id):
                            logger.warning(
                                "model is not listed with text-generation as one of it's abilities!"
                            )
                    self.additional_system_prompt_template = self.env.get_template(
                        str(prompt_file)
                    )

        if mps.is_available() or xpu.is_available():
            logger.info("Server is using a Metal or XPU backend!")
            self.supported_kv_quantization = ["fp8"]
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

        if (
            first_model_result.config == None
        ):  # hacky workaround, should check both if config is none OR if it doesn't specify bitsandbytes quantization in the config
            self.engine_args = AsyncEngineArgs(
                model=model_path_on_hf,
                dtype="auto",
                enable_prefix_caching=True,
                trust_remote_code=True,
                kv_cache_dtype=self.supported_kv_quantization[-1],  # ty: ignore
                hf_token=True,
                max_model_len=16384,
                max_num_seqs=4,
                disable_log_stats=True,
                language_model_only=True,
            )
            self.engine = AsyncLLMEngine.from_engine_args(self.engine_args)
            self.quantization_method = "native/none"
        else:
            self.engine_args = AsyncEngineArgs(
                model=model_path_on_hf,
                dtype="auto",
                enable_prefix_caching=True,
                trust_remote_code=True,
                kv_cache_dtype=self.supported_kv_quantization[-1],  # ty: ignore
                quantization="bitsandbytes",
                load_format="bitsandbytes",
                hf_token=True,
                max_model_len=16384,
                max_num_seqs=4,
                language_model_only=True,
            )
            self.engine = AsyncLLMEngine.from_engine_args(self.engine_args)
            self.quantization_method = "bitsandbytes"

        self.tokenizer = self.engine.get_tokenizer()
        self.engine_sampling_args = SamplingParams(
            temperature=1.0,
            top_p=0.95,
            top_k=20,
            min_p=0.0,
            presence_penalty=0.0,
            repetition_penalty=1.0,
            output_kind=RequestOutputKind.DELTA,
        )  # this is for Qwen/Qwen3.8-27B in particular

        if "darwin" in system().lower():
            self.embedding_engine_args = AsyncEngineArgs(
                model="mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ",
                runner="pooling",
                dtype="auto",
                trust_remote_code=True,
                hf_token=True,
                max_model_len=3072,
                max_num_seqs=4,
            )
            self.embedding_engine = AsyncLLMEngine.from_engine_args(
                self.embedding_engine_args
            )
        elif "linux" in system().lower():
            self.embedding_engine_args = AsyncEngineArgs(
                model="Qwen/Qwen3-Embedding-0.6B",
                runner="pooling",
                dtype="auto",
                trust_remote_code=True,
                hf_token=True,
                max_model_len=3072,
                max_num_seqs=4,
            )
            self.embedding_engine = AsyncLLMEngine.from_engine_args(
                self.embedding_engine_args
            )

        self.embedding_tokenizer = self.embedding_engine.get_tokenizer()
        self.embedding_pooling_args = PoolingParams(task="embed", use_activation=True)
        self.converted_documents_directory = Path("converted_documents")
        if not self.converted_documents_directory.exists():
            self.converted_documents_directory.mkdir()
        self.model_id = first_model_result.id
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

    def shutdown(self):
        self.engine.shutdown()
        self.embedding_engine.shutdown()

    async def new_conversation(
        self, message: str, user: User
    ) -> AsyncGenerator[str | tuple[Conversation, str], None]:
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

        stage = 0

        async for output in self.engine.generate(
            TokensPrompt(prompt_token_ids=token_ids),
            self.engine_sampling_args,
            conversation.conversationID,
        ):
            if stage == 0:
                stage += 1
                yield (conversation, output.outputs[0].text)
            else:
                yield output.outputs[0].text

    async def reply(self, message: str, conversation: Conversation):
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

            stage = 0

            async for output in self.engine.generate(
                TokensPrompt(prompt_token_ids=token_ids),
                self.engine_sampling_args,
                conversation.conversationID,
            ):
                if stage == 0:
                    stage += 1
                    yield (conversation, output.outputs[0].text)
                else:
                    yield output.outputs[0].text

    async def generate_embeddings(
        self,
        file_path_or_text: Path | str,
        type_of_file: Literal["pdf", "word_document", "webpage", "plaintext"],
    ):
        if type_of_file == "pdf" and isinstance(file_path_or_text, Path):
            if file_path_or_text.exists() and file_path_or_text.is_file():
                markdown_txt = self.markitdown_converter.convert(file_path_or_text)
                if len(markdown_txt.markdown) == 0:
                    markdown_txt = pymupdf4llm.to_markdown(file_path_or_text)

                if isinstance(markdown_txt, str):
                    ast = self.ast_parser.parse(markdown_txt).to_ast()
                else:
                    ast = self.ast_parser.parse(markdown_txt.markdown).to_ast()
            else:
                raise FileTypeMismatchError
        elif type_of_file == "word_document" and isinstance(file_path_or_text, Path):
            if file_path_or_text.exists() and file_path_or_text.is_file():
                markdown_txt = self.markitdown_converter.convert(file_path_or_text)

                if len(markdown_txt.markdown) == 0:
                    _path = str(file_path_or_text).split(".")[0] + ".md"
                    word_to_markdown(
                        file_path_or_text,
                        Path(
                            file_path_or_text.parent,
                            str(file_path_or_text).split(".")[0] + ".md",
                        ),
                    )

                    async with await open_file(_path, "r") as f:
                        markdown_txt = await f.read()

                    ast = self.ast_parser.parse(markdown_txt).to_ast()
                else:
                    ast = self.ast_parser.parse(markdown_txt.markdown).to_ast()
            else:
                raise FileTypeMismatchError
        elif type_of_file == "webpage" and isinstance(file_path_or_text, Path):
            if file_path_or_text.exists() and file_path_or_text.is_file():
                markdown_txt = self.markitdown_converter.convert(file_path_or_text)

                if len(markdown_txt.markdown) == 0:
                    async with await open_file(file_path_or_text, "r") as f:
                        markdown_txt = md(await f.read(), strip=["img"])

                    ast = self.ast_parser.parse(markdown_txt).to_ast()
                else:
                    ast = self.ast_parser.parse(markdown_txt.markdown).to_ast()
            else:
                raise FileNotFoundError
        else:
            if isinstance(file_path_or_text, str):
                ast = self.ast_parser.parse(file_path_or_text).to_ast()
            else:
                raise FileTypeMismatchError

        for i, child in enumerate(ast["children"]):
            if child["type"] == "paragraph":
                paragraph_text = ""
                for sentences in child["children"]:
                    paragraph_text += sentences["value"]
                yield (
                    self.embedding_engine.encode(
                        TextPrompt(paragraph_text),  # ty: ignore
                        pooling_params=self.embedding_pooling_args,
                        request_id=str(uuid4()),
                    ),
                    child["position"],
                    i == len(ast["children"]) - 1,
                )
