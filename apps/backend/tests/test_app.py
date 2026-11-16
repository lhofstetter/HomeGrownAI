from importlib.metadata import version

from fastapi.testclient import TestClient
from homegrownai.main import app
from homegrownai.schemas.response import ServerHealthModel

client = TestClient(app)


def test_health():
    response = client.get("/")

    assert response.status_code == 200

    parsed_response = ServerHealthModel.model_validate(response.json())
    assert parsed_response.status == "ok"
    assert parsed_response.version == version("homegrownai")
