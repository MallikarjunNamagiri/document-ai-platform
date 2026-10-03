import numpy as np


class FakeTextEmbedding:
    """Mimics fastembed.TextEmbedding: returns a generator of numpy float32 arrays."""

    def embed(self, texts):
        for t in texts:
            yield np.array([float(len(t)), 1.0, 0.5], dtype=np.float32)


def test_embed_documents_returns_plain_float_lists():
    from src.core.models import FastEmbedEmbeddings

    emb = FastEmbedEmbeddings(model=FakeTextEmbedding())
    out = emb.embed_documents(["ab", "abcd"])

    assert out == [[2.0, 1.0, 0.5], [4.0, 1.0, 0.5]]
    assert type(out[0]) is list and type(out[0][0]) is float  # JSON/Qdrant-serialisable


def test_embed_query_returns_a_single_vector():
    from src.core.models import FastEmbedEmbeddings

    emb = FastEmbedEmbeddings(model=FakeTextEmbedding())
    assert emb.embed_query("abc") == [3.0, 1.0, 0.5]
