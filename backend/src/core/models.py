from functools import lru_cache
from typing import List

from langchain_groq import ChatGroq

from src.config import GROQ_API_KEY, GROQ_MODEL, EMBEDDING_MODEL, RERANKER_MODEL


class FastEmbedEmbeddings:
    """ONNX-based embeddings (fastembed). Same model family as before, but no PyTorch,
    so the backend fits on small hosts. Exposes the LangChain Embeddings interface."""

    def __init__(self, model=None, model_name: str = EMBEDDING_MODEL):
        if model is None:
            from fastembed import TextEmbedding  # lazy: model is downloaded on first use

            model = TextEmbedding(model_name=model_name)
        self._model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[float(x) for x in vec] for vec in self._model.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


@lru_cache(maxsize=1)
def get_embeddings():
    return FastEmbedEmbeddings()


@lru_cache(maxsize=1)
def get_reranker():
    # Optional and heavy (PyTorch): only imported if the reranker is actually used.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANKER_MODEL)


@lru_cache(maxsize=1)
def get_llm():
    if not GROQ_API_KEY:
        return None
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
        streaming=True,
    )
