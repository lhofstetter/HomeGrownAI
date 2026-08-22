from pathlib import Path
from sys import stderr

from homegrownai.exceptions import AIAppError, ModelNotFoundError
from huggingface_hub import HfApi, ModelInfo
from loguru import logger
from vllm import LLM

logger.add(stderr, format="{time:MMMM D, YYYY > HH:mm:ss} | {extra} | {message}")
PROMPT_DIRECTORY = Path("system_prompts")

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

        model_results: list[ModelInfo] = self.api.list_models(search=model_path_on_hf)

        if len(model_results) == 0:
            raise ModelNotFoundError

        with open(Path(PROMPT_DIRECTORY, "generic.md.jinja"), "r") as f:
            self.system_prompt = f.read()

        model_id = model_results[
            0
        ].id.split(
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
                    if model_results[0].pipeline_tag == None or (
                        model_results[0].pipeline_tag != None
                        and model_results[0].pipeline_tag != "text-generation"
                    ):
                        with logger.contextualize(model=model_results[0].id):
                            logger.warning(
                                "model is not listed with text-generation as one of it's abilities!"
                            )
                    with open(prompt_file, "r") as f:
                        self.system_prompt += "\n" + f.read()

        assert len(self.system_prompt) != 0

        self.engine = LLM(
            model=model_path_on_hf,
            dtype="auto",
            enable_prefix_caching=True,
            trust_remote_code=True,
            quantization="bitsandbytes",
            load_format="bitsandbytes",
            hf_token=True,
        )

        self.model_id = model_results[0].id
        self.quantization_method = "bitsandbytes"
        self.conversations = {}
        self.reasoning_effort = "med"
