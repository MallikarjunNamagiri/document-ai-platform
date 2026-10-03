from types import SimpleNamespace


class FakeClient:
    """qdrant-client >= 1.16 only exposes query_points(); .search() no longer exists."""

    def __init__(self):
        self.kwargs = None

    def query_points(self, **kwargs):
        self.kwargs = kwargs
        hit = SimpleNamespace(
            score=0.91,
            payload={"page_content": "Net 30", "doc_name": "c.pdf", "page_number": 4, "token_count": 2},
        )
        return SimpleNamespace(points=[hit])


class FakeEmbeddings:
    def embed_query(self, q):
        return [0.1, 0.2, 0.3]


def test_search_is_filtered_to_one_document_and_maps_payload(monkeypatch):
    import src.services.qdrant_ops as ops

    client = FakeClient()
    monkeypatch.setattr(ops, "get_qdrant_client", lambda: client)
    monkeypatch.setattr(ops, "get_embeddings", lambda: FakeEmbeddings())

    docs = ops.search_qdrant_with_doc_filter("payment terms", "abc123", top_k=3)

    assert client.kwargs["query"] == [0.1, 0.2, 0.3]
    assert client.kwargs["limit"] == 3
    flt = client.kwargs["query_filter"]
    assert flt.must[0].key == "doc_hash" and flt.must[0].match.value == "abc123"
    assert docs[0].page_content == "Net 30"
    assert docs[0].metadata["source"] == "c.pdf" and docs[0].metadata["page_number"] == 4
