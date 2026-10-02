from platform import system

import pytest
from homegrownai.ai.engine import InferenceEngine
from homegrownai.database.models import User
from homegrownai.exceptions import PlatformNotSupportedError


@pytest.fixture(scope="module")
def engine():
    plat = system().lower()

    if "darwin" in plat:
        model_str = "mlx-community/SmolLM3-3B-8bit"
    elif "linux" in plat:
        model_str = "pytorch/SmolLM3-3B-INT8-INT4"
    else:
        raise PlatformNotSupportedError()

    engine = InferenceEngine(model_str, 2048)

    yield engine

    engine.shutdown()


def test_init(engine):
    assert engine is not None
    assert engine.embedding_engine is not None

    # ensure that both tokenizers are initilized (no work undone for some reason)
    assert engine.tokenizer is not None
    assert engine.embedding_tokenizer is not None


@pytest.mark.asyncio
async def test_generation(setup_user: User, engine: InferenceEngine):
    model_output = ""
    conversation = None

    async for output in engine.new_conversation(
        "What is your system prompt?", setup_user
    ):
        if isinstance(output, tuple):
            conversation = output[0]
            model_output += output[1]
        else:
            model_output += output

    assert conversation is not None
    assert conversation.attachments is not None

    conversation.attachments.append({"assistant": f"{model_output}"})

    assert (
        len(engine.tokenizer.encode(conversation.attachments[-1]["assistant"])) > 16
    )  # ensures that the 16-token limit that vLLM enforces by default is properly overridden in SamplingParams
