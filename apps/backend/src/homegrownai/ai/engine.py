from collections.abc import Iterable
from pathlib import Path
from sys import stderr

from homegrownai.database.user import User
from homegrownai.exceptions import AIAppError
from homegrownai.schemas.user import Conversation
from huggingface_hub import HfApi, ModelInfo
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from torch import cuda, mps, version, xpu
from vllm import LLM

logger.add(stderr, format="{time:MMMM D, YYYY > HH:mm:ss} | {extra} | {message}")
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
            self.engine = LLM(
                model=model_path_on_hf,
                dtype="auto",
                enable_prefix_caching=True,
                trust_remote_code=True,
                kv_cache_dtype=self.supported_kv_quantization[-1],
                calculate_kv_scales=True,
                hf_token=True,
                max_model_len=32768,
                max_num_seqs=2,
            )
            self.quantization_method = "native/none"
        else:
            self.engine = LLM(
                model=model_path_on_hf,
                dtype="auto",
                enable_prefix_caching=True,
                trust_remote_code=True,
                kv_cache_dtype=self.supported_kv_quantization[-1],
                quantization="bitsandbytes",
                load_format="bitsandbytes",
                calculate_kv_scales=True,
                hf_token=True,
            )
            self.quantization_method = "bitsandbytes"
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

    def new_conversation(self, user: User, conversation: Conversation):
        template_items: dict[str, str] = {}

        if len(user.custom_model_name) > 0:
            template_items["name"] = user.custom_model_name
        else:
            template_items["name"] = "Nova"

        if len(user.human_name) > 0:
            template_items["human_name"] = user.human_name
        else:
            template_items["human_name"] = "User"

        if len(user.custom_model_instructions) > 0:
            template_items["user_instructions"] = user.custom_model_instructions
        else:
            template_items["user_instructions"] = "The user has no custom instructions."

        system_prompt = self.template.render(
            name=template_items["name"],
            human_name=template_items["human_name"],
            user_instructions=template_items["user_instructions"],
            tools=self.tools,
        )

        if conversation.attachments == None:
            raise AIAppError("No attachments in the conversation to produce text!")

        conversation.attachments = [
            {"role": "system", "content": system_prompt},
            conversation.attachments[-1],
        ]

        outputs = self.engine.chat(conversation.attachments)  # ty: ignore

        conversation.attachments.append(
            {"role": "assistant", "content": outputs[0].outputs[0].text}
        )

        return conversation.attachments

    def reply(self, user: User, conversation: Conversation):
        pass
