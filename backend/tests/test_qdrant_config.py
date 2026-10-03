"""A missing QDRANT_URL must fail loudly, not silently fall back to localhost:6333."""
import os

import pytest
from fastapi.testclient import TestClient

from tests.pdf_fixtures import make_pdf


def test_missing_qdrant_url_raises_a_clear_error_instead_of_defaulting_to_localhost(monkeypatch):
    from src.services.ingestion import get_qdrant_client, QdrantNotConfigured

    monkeypatch.delenv("QDRANT_URL", raising=False)
    with pytest.raises(QdrantNotConfigured, match="QDRANT_URL"):
        get_qdrant_client()


def test_configured_qdrant_url_and_key_are_used(monkeypatch):
    from src.services.ingestion import get_qdrant_client

    monkeypatch.setenv("QDRANT_URL", "https://abc.cloud.qdrant.io:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "secret")
    client = get_qdrant_client()
    assert client._client.rest_uri == "https://abc.cloud.qdrant.io:6333"


def test_upload_reports_503_naming_the_missing_setting(monkeypatch):
    from src.main import app

    monkeypatch.delenv("QDRANT_URL", raising=False)
    monkeypatch.setattr("src.api.endpoints.MAX_UPLOAD_BYTES", 10_000_000)
    # real indexing path on purpose: embeddings are stubbed, the Qdrant client is NOT
    monkeypatch.setattr(
        "src.services.ingestion.get_embeddings",
        lambda: type("E", (), {"embed_documents": lambda self, t: [[0.0] * 3 for _ in t]})(),
    )
    r = TestClient(app, raise_server_exceptions=False).post(
        "/api/upload", files={"file": ("a.pdf", make_pdf(["Some content here"]), "application/pdf")}
    )
    assert r.status_code == 503
    assert "QDRANT_URL" in r.json()["detail"]


def test_env_file_values_are_loaded_but_never_override_real_environment(tmp_path, monkeypatch):
    from src.config import load_env_file

    env = tmp_path / ".env"
    env.write_text("QDRANT_URL=https://from-file\nGROQ_API_KEY=from-file\n")
    monkeypatch.delenv("QDRANT_URL", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "from-host-dashboard")

    load_env_file(env)

    assert os.environ["QDRANT_URL"] == "https://from-file"
    assert os.environ["GROQ_API_KEY"] == "from-host-dashboard"  # Render/Vercel settings win


def test_missing_env_file_is_not_an_error(tmp_path):
    from src.config import load_env_file

    load_env_file(tmp_path / "does-not-exist.env")  # e.g. on Render, where no file exists
