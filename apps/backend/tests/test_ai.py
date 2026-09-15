from platform import system

import pytest
from homegrownai.ai.engine import InferenceEngine
from homegrownai.database.models import User
from homegrownai.exceptions import PlatformNotSupportedError


def test_init():
    plat = system().lower()

    if "darwin" in plat:
        model_str = "mlx-community/Qwen3.8-27B-4bit"
    elif "linux" in plat:
        model_str = "RedHatAI/Qwen3.8-27B-INT4"
    else:
        raise PlatformNotSupportedError()

    engine = InferenceEngine(model_str)

    # first ensure that both engines are initialized correctly, even though they have to be initialized if they reached this point
    assert engine is not None
    assert engine.embedding_engine is not None

    # ensure that both tokenizers are initilized (no work undone for some reason)
    assert engine.tokenizer is not None
    assert engine.embedding_tokenizer is not None


@pytest.fixture
def engine():
    plat = system().lower()

    if "darwin" in plat:
        model_str = "mlx-community/Qwen3.8-27B-4bit"
    elif "linux" in plat:
        model_str = "RedHatAI/Qwen3.8-27B-INT4"
    else:
        raise PlatformNotSupportedError()

    engine = InferenceEngine(model_str)

    yield engine

    engine.shutdown()


@pytest.mark.asyncio
async def test_generation(test_user: User, engine: InferenceEngine):
    model_output = ""

    async for output in engine.new_conversation("Hello! How are you today?", test_user):
        if isinstance(output, tuple):
            conversation = output[0]
            model_output += output[1]
        else:
            model_output += output

    assert conversation is not None
    assert conversation.attachments is not None

    conversation.attachments.append({"assistent": f"{model_output}"})

    assert len(conversation.attachments[-1]["assistent"]) > 0
