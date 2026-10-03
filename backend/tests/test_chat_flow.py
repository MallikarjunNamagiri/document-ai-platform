"""Chat after upload. Qdrant Cloud rejects filtered searches unless the filtered field has a payload index,
and unhandled server errors lose their CORS headers, which browsers report as a bare 'Failed to fetch'."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from qdrant_client.models import PayloadSchemaType

ORIGIN = {"Origin": "https://my-app.vercel.app"}


class FakeQdrant:
    def __init__(self, collections=("enterprise_documents",)):
        self.collections = list(collections)
        self.calls = []

    def get_collections(self):
        return SimpleNamespace(collections=[SimpleNamespace(name=n) for n in self.collections])

    def create_collection(self, **kw):
        self.calls.append(("create_collection", kw))
        self.collections.append(kw["collection_name"])

    def create_payload_index(self, **kw):
        self.calls.append(("create_payload_index", kw))

    def upsert(self, **kw):
        self.calls.append(("upsert", kw))


@pytest.fixture(autouse=True)
def fresh_index_cache(monkeypatch):
    import src.services.ingestion as ing

    monkeypatch.setattr(ing, "_indexed_collections", set(), raising=False)


def _index_calls(client):
    return [kw for name, kw in client.calls if name == "create_payload_index"]


@pytest.mark.parametrize("existing", [True, False])
def test_doc_hash_gets_a_keyword_index_whether_or_not_the_collection_already_exists(existing):
    from src.services.ingestion import ensure_collection_exists

    client = FakeQdrant(collections=("enterprise_documents",) if existing else ())
    ensure_collection_exists(client, vector_size=384)

    (idx,) = _index_calls(client)
    assert idx["collection_name"] == "enterprise_documents"
    assert idx["field_name"] == "doc_hash"
    assert idx["field_schema"] == PayloadSchemaType.KEYWORD


def test_search_ensures_the_index_before_querying(monkeypatch):
    """Covers documents uploaded before the fix: chat must work without re-uploading."""
    import src.services.qdrant_ops as ops

    order = []

    class C(FakeQdrant):
        def create_payload_index(self, **kw):
            order.append("index")
            super().create_payload_index(**kw)

        def query_points(self, **kw):
            order.append("query")
            return SimpleNamespace(points=[])

    monkeypatch.setattr(ops, "get_qdrant_client", lambda: C())
    monkeypatch.setattr(ops, "get_embeddings", lambda: SimpleNamespace(embed_query=lambda q: [0.1]))

    ops.search_qdrant_with_doc_filter("what is fiverr", "abc", top_k=3)
    assert order == ["index", "query"]


def test_index_is_only_requested_once_per_process():
    from src.services.ingestion import ensure_collection_exists

    client = FakeQdrant()
    ensure_collection_exists(client, vector_size=384)
    ensure_collection_exists(client, vector_size=384)
    assert len(_index_calls(client)) == 1


@pytest.fixture
def client():
    from src.main import app

    return TestClient(app, raise_server_exceptions=False)


def _chat(client):
    return client.post(
        "/api/chat/stream",
        json={"question": "what is fiverr account?", "document_hash": "abc", "chat_history": []},
        headers=ORIGIN,
    )


def test_search_failure_returns_json_502_that_the_browser_is_allowed_to_read(client, monkeypatch):
    import src.api.endpoints as ep

    monkeypatch.setattr(ep, "get_llm", lambda: object())
    monkeypatch.setattr(ep, "check_semantic_cache", lambda *a, **k: None)

    def boom(*a, **k):
        raise RuntimeError("qdrant exploded")

    monkeypatch.setattr(ep, "search_qdrant_with_doc_filter", boom)

    r = _chat(client)
    assert r.status_code == 502
    assert "search" in r.json()["detail"].lower()
    assert r.headers["access-control-allow-origin"] == ORIGIN["Origin"]  # else browser says "Failed to fetch"


def test_missing_groq_key_returns_503_naming_the_setting(client, monkeypatch):
    import src.api.endpoints as ep

    monkeypatch.setattr(ep, "get_llm", lambda: None)
    monkeypatch.setattr(ep, "check_semantic_cache", lambda *a, **k: None)
    monkeypatch.setattr(
        ep, "search_qdrant_with_doc_filter",
        lambda *a, **k: [SimpleNamespace(page_content="x", metadata={})],
    )

    r = _chat(client)
    assert r.status_code == 503
    assert "GROQ_API_KEY" in r.json()["detail"]
    assert r.headers["access-control-allow-origin"] == ORIGIN["Origin"]
