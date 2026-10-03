"""Upload endpoint contract. Qdrant + embeddings are the external boundary and are faked;
PDF parsing, hashing, chunking and HTTP behaviour are real."""
import hashlib

import pytest
from fastapi.testclient import TestClient

from tests.pdf_fixtures import make_pdf


@pytest.fixture
def indexed(monkeypatch):
    """Replace only the Qdrant write; record what would have been indexed."""
    import src.api.endpoints as ep

    calls = []

    def fake_index(chunks, doc_hash, filename):
        calls.append({"chunks": chunks, "hash": doc_hash, "filename": filename})
        return len(chunks)

    monkeypatch.setattr(ep, "index_chunks_to_qdrant", fake_index)
    return calls


@pytest.fixture
def client():
    from src.main import app

    # raise_server_exceptions=False => we see what a browser would see (a 500 page), not a pytest traceback
    return TestClient(app, raise_server_exceptions=False)


def _post(client, name, data):
    return client.post("/api/upload", files={"file": (name, data, "application/pdf")})


def test_valid_pdf_is_hashed_chunked_and_indexed(client, indexed):
    pdf = make_pdf(["Payment is due within thirty days"])
    r = _post(client, "contract.pdf", pdf)

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "contract.pdf"
    assert body["hash"] == hashlib.sha256(pdf).hexdigest()
    assert body["chunks"] == 1
    assert "thirty days" in indexed[0]["chunks"][0].page_content


def test_uppercase_pdf_extension_is_accepted(client, indexed):
    r = _post(client, "REPORT.PDF", make_pdf(["Quarterly numbers"]))
    assert r.status_code == 200


def test_non_pdf_is_rejected_with_json_detail(client, indexed):
    r = _post(client, "notes.txt", b"hello")
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]
    assert indexed == []


def test_corrupt_pdf_gives_json_400_not_a_500_page(client, indexed):
    r = _post(client, "broken.pdf", b"this is not a pdf at all")
    assert r.status_code == 400
    assert "read" in r.json()["detail"].lower()
    assert indexed == []


def test_pdf_without_extractable_text_is_rejected(client, indexed):
    r = _post(client, "scan.pdf", make_pdf([""]))
    assert r.status_code == 422
    assert "text" in r.json()["detail"].lower()
    assert indexed == []


def test_vector_store_outage_returns_json_502(client, monkeypatch):
    import src.api.endpoints as ep

    def boom(*a, **k):
        raise ConnectionError("qdrant unreachable")

    monkeypatch.setattr(ep, "index_chunks_to_qdrant", boom)
    r = _post(client, "ok.pdf", make_pdf(["Some content here"]))
    assert r.status_code == 502
    assert "vector" in r.json()["detail"].lower()


def test_file_over_size_limit_is_rejected_with_413(client, indexed, monkeypatch):
    import src.api.endpoints as ep

    monkeypatch.setattr(ep, "MAX_UPLOAD_BYTES", 100)
    r = _post(client, "big.pdf", make_pdf(["Some content here"]))  # > 100 bytes
    assert r.status_code == 413
    assert "too large" in r.json()["detail"].lower()
    assert indexed == []
