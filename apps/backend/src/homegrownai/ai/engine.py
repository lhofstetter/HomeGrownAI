from vllm import LLM
from huggingface_hub import HfApi, ModelInfo
from homegrownai.exceptions import ModelNotFoundError, AIAppError
from pathlib import Path
from loguru import logger
from sys import stderr

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

        f = open(Path(PROMPT_DIRECTORY, "generic.md.jinja"), 'r')
        self.system_prompt = f.read()
        f.close()
        
        model_id = model_results[0].id.split("/") # split the model id so that the lab/individual (provider) identifier is first, which is the directory name
        if model_id[0] in model_prompts.keys() and Path(PROMPT_DIRECTORY, model_id[0]).is_dir():
            for prompt_file in Path(PROMPT_DIRECTORY, model_id[0]).iterdir(): # this loop is designed to find the prompt associated with this particular model
                if prompt_file.name.removesuffix(".md.jinja") == model_id[1]:
                    if model_results[0].pipeline_tag == None or (model_results[0].pipeline_tag != None and model_results[0].pipeline_tag != "text-generation"):
                        with logger.contextualize(model=model_results[0].id):
                            logger.warning("model is not listed with text-generation as one of it's abilities!")
                    f = open(prompt_file, 'r')
                    self.system_prompt = f.read()
                    f.close()
            if len(self.system_prompt) == 0: # if no such prompt exists (see above comment), insert a generic one that should apply for all models released by that provider
                f = open(Path(PROMPT_DIRECTORY, model_id[0], "generic.md.jinja"), 'r')
                self.system_prompt = f.read()
                f.close()
        else: # if we don't have a prompt for ANY models offered by that provider, then use a generic prompt
            # WARNING: Generic prompts perform badly for lots of reasons, the primary one being that models vary wildly by architecture, parameter count and capabilities. Generally, this should
            # only be executed as a last resort

            # TODO: Add logging so that we know when a specific model that isn't supported yet is used frequently so a specific prompt can be designed as soon as possible
            f = open(Path(PROMPT_DIRECTORY, "generic.md.jinja"), 'r')
            self.system_prompt = f.read()
            f.close()

        assert len(self.system_prompt) != 0
        
        self.engine = LLM(
            model=model_path_on_hf,
            dtype="auto",
            enable_prefix_caching=True,
            trust_remote_code=True,
            quantization="bitsandbytes",
            load_format="bitsandbytes",
            hf_token=True
        )

        self.model_id = model_results[0].id 
        self.quantization_method = "bitsandbytes"
        self.conversations = {}
        
        
   
