"""RAGAS wrapper. The LLM-backed `evaluate` is the external boundary and is faked; the shape of the fake result
mirrors ragas 0.4.3's EvaluationResult: no .get(), and result[metric] -> list of per-row scores."""
import math

import pytest


class FakeEvaluationResult:
    def __init__(self, scores):
        self._scores = scores

    def __getitem__(self, key):
        return self._scores[key]


class FakeDataset:
    @classmethod
    def from_dict(cls, d):
        return d


@pytest.fixture
def fake_ragas(monkeypatch):
    import src.services.evaluator as ev

    state = {"result": None, "error": None, "metrics_seen": None}

    def evaluate(dataset, metrics, llm, embeddings, raise_exceptions):
        state["metrics_seen"] = len(metrics)
        if state["error"]:
            raise state["error"]
        return state["result"]

    monkeypatch.setattr(
        ev, "_load_ragas", lambda: (FakeDataset, evaluate, object(), lambda: object(), object())
    )
    for name in ("get_llm", "get_eval_llm", "get_embeddings"):
        monkeypatch.setattr(ev, name, lambda: object(), raising=False)
    return state


def _run(ground_truth=""):
    from src.services.evaluator import run_ragas_evaluation

    return run_ragas_evaluation("q", "a", ["ctx"], ground_truth)


def test_scores_are_read_from_the_result_and_rounded(fake_ragas):
    fake_ragas["result"] = FakeEvaluationResult({"faithfulness": [0.8349], "nv_context_relevance": [0.5]})
    out = _run()
    assert out["faithfulness"] == 0.83
    assert out["context_relevancy"] == 0.5
    assert out["status"] == "success"


def test_answer_correctness_is_not_invented_without_a_reference_answer(fake_ragas):
    fake_ragas["result"] = FakeEvaluationResult({"faithfulness": [0.8], "nv_context_relevance": [0.5]})
    out = _run(ground_truth="")
    assert out["answer_correctness"] is None
    assert fake_ragas["metrics_seen"] == 2  # answer_correctness metric was not even requested


def test_answer_correctness_is_reported_when_a_reference_answer_is_given(fake_ragas):
    fake_ragas["result"] = FakeEvaluationResult(
        {"faithfulness": [0.8], "nv_context_relevance": [0.5], "answer_correctness": [0.7]}
    )
    out = _run(ground_truth="Net 30")
    assert out["answer_correctness"] == 0.7
    assert fake_ragas["metrics_seen"] == 3


def test_a_metric_whose_llm_job_failed_is_null_not_a_made_up_number(fake_ragas):
    # raise_exceptions=False: a failed job (e.g. LLMDidNotFinishException) comes back as NaN
    fake_ragas["result"] = FakeEvaluationResult({"faithfulness": [math.nan], "nv_context_relevance": [0.5]})
    out = _run()
    assert out["faithfulness"] is None
    assert out["context_relevancy"] == 0.5
    assert out["status"] == "partial"


def test_total_failure_returns_nulls_and_never_fabricated_scores(fake_ragas):
    fake_ragas["error"] = RuntimeError("groq rate limit")
    out = _run()
    assert out == {"faithfulness": None, "context_relevancy": None, "answer_correctness": None, "status": "failed"}


def test_characterization_ragas_result_has_no_get_but_supports_indexing():
    """The upstream surprise that broke evaluation: pin the assumption so a ragas upgrade is noticed."""
    from src.services.evaluator import _install_vertexai_compat

    _install_vertexai_compat()  # must run before ragas is imported, including by importorskip
    pytest.importorskip("ragas")
    from ragas.dataset_schema import EvaluationResult

    assert not hasattr(EvaluationResult, "get")
    assert hasattr(EvaluationResult, "__getitem__")


def test_eval_llm_gets_a_generous_completion_budget(monkeypatch):
    """Reasoning models spend completion tokens thinking; a small cap ends in LLMDidNotFinishException."""
    import src.core.models as models

    monkeypatch.setattr(models, "GROQ_API_KEY", "test-key")
    models.get_eval_llm.cache_clear() if hasattr(models, "get_eval_llm") else None
    llm = models.get_eval_llm()
    assert llm.max_tokens >= 4096
