import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(autouse=True)
def prevent_paid_calls(monkeypatch):
    # Individual adapter tests can override this with mock credentials/client.
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    monkeypatch.delenv('LLM_MODEL', raising=False)
    monkeypatch.setenv('LLM_INCLUDE_ML_CONTEXT', 'true')


@pytest.fixture
def client():
    with TestClient(app) as session:
        yield session
