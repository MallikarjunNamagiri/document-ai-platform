import sys
import types
from typing import List, Dict, Any

import math

from src.core.models import get_eval_llm, get_embeddings


class EvaluationUnavailable(RuntimeError):
    """Raised when the optional evaluation libraries (ragas, datasets) are not installed."""


def _install_vertexai_compat() -> None:
    """ragas 0.4.3 imports Vertex classes removed from langchain-community 0.4."""
    chat_name = "langchain_community.chat_models.vertexai"
    llm_name = "langchain_community.llms.vertexai"

    if chat_name not in sys.modules:
        try:
            __import__(chat_name)
        except ModuleNotFoundError:
            chat_mod = types.ModuleType(chat_name)

            class ChatVertexAI:
                pass

            chat_mod.ChatVertexAI = ChatVertexAI
            sys.modules[chat_name] = chat_mod

    if llm_name not in sys.modules:
        try:
            __import__(llm_name)
        except ModuleNotFoundError:
            llm_mod = types.ModuleType(llm_name)

            class VertexAI:
                pass

            class VertexAIModelGarden:
                pass

            llm_mod.VertexAI = VertexAI
            llm_mod.VertexAIModelGarden = VertexAIModelGarden
            sys.modules[llm_name] = llm_mod



def _load_ragas():
    """Imports ragas/datasets on demand; they are optional and heavy (see requirements-eval.txt)."""
    try:
        _install_vertexai_compat()
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, ContextRelevance, answer_correctness
    except ImportError as exc:
        raise EvaluationUnavailable(
            "Evaluation needs the optional 'ragas' and 'datasets' packages "
            "(pip install -r requirements-eval.txt)."
        ) from exc
    return Dataset, evaluate, faithfulness, ContextRelevance, answer_correctness


def _score(result, key: str):
    """First-row score as a rounded float, or None if absent/NaN (a failed judge call)."""
    try:
        value = float(result[key][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return None if math.isnan(value) else round(value, 2)


def run_ragas_evaluation(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: str = ""
) -> Dict[str, Any]:
    """
    Scores one Q&A turn with RAGAS. Only real scores are ever returned:
    a metric that could not be computed is None, never a placeholder number.
    - faithfulness: is the answer grounded in the retrieved contexts
    - context_relevancy: are the retrieved contexts relevant to the question
    - answer_correctness: only computed when a reference answer (ground_truth) is given
    status: "success" (all requested metrics scored), "partial", or "failed".
    """
    Dataset, evaluate, faithfulness, ContextRelevance, answer_correctness = _load_ragas()
    empty = {"faithfulness": None, "context_relevancy": None, "answer_correctness": None}
    try:
        data_dict = {
            "question": [question],
            "contexts": [contexts if contexts else ["No context retrieved"]],
            "answer": [answer],
        }
        selected_metrics = [faithfulness, ContextRelevance()]
        if ground_truth:
            data_dict["ground_truth"] = [ground_truth]
            selected_metrics.append(answer_correctness)

        result = evaluate(
            Dataset.from_dict(data_dict),
            metrics=selected_metrics,
            llm=get_eval_llm(),
            embeddings=get_embeddings(),
            raise_exceptions=False,
        )
    except Exception as exc:
        print(f"Ragas evaluation failed: {exc}")
        return {**empty, "status": "failed"}

    scores = {
        "faithfulness": _score(result, "faithfulness"),
        "context_relevancy": _score(result, "nv_context_relevance"),
        "answer_correctness": _score(result, "answer_correctness") if ground_truth else None,
    }
    requested = [v for k, v in scores.items() if k != "answer_correctness" or ground_truth]
    if all(v is not None for v in requested):
        status = "success"
    elif any(v is not None for v in requested):
        status = "partial"
    else:
        status = "failed"
    return {**scores, "status": status}
