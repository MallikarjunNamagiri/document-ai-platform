"""Guards the exact failures seen on deploy: the app must boot with only requirements.txt."""
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=120
    )


def test_app_boots_when_optional_eval_libraries_are_absent():
    # Setting sys.modules[name] = None makes `import name` raise ImportError, simulating "not installed".
    r = _run(
        "import sys\n"
        "for m in ('ragas','datasets','torch','sentence_transformers','langchain_huggingface','faiss'):\n"
        "    sys.modules[m] = None\n"
        "from src.main import app\n"
        "print('BOOT_OK')\n"
    )
    assert "BOOT_OK" in r.stdout, r.stderr[-1500:]


def test_importing_models_does_not_pull_in_pytorch():
    r = _run(
        "import sys\n"
        "import src.core.models\n"
        "bad = [m for m in ('torch','sentence_transformers') if m in sys.modules]\n"
        "print('LOADED:' + ','.join(bad))\n"
    )
    assert r.stdout.strip() == "LOADED:", r.stdout + r.stderr[-1500:]


def test_evaluate_endpoint_reports_503_when_ragas_missing():
    r = _run(
        "import sys, json\n"
        "sys.modules['ragas'] = None\n"
        "sys.modules['datasets'] = None\n"
        "from fastapi.testclient import TestClient\n"
        "from src.main import app\n"
        "resp = TestClient(app, raise_server_exceptions=False).post('/api/evaluate', "
        "json={'question':'q','answer':'a','contexts':['c']})\n"
        "print(resp.status_code, json.dumps(resp.json()))\n"
    )
    assert r.stdout.startswith("503"), r.stdout + r.stderr[-1500:]
    assert "ragas" in r.stdout.lower()
