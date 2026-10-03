"""A package that is importable on a dev machine but missing from requirements.txt breaks the deploy."""
import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def _declared() -> set[str]:
    names = set()
    for line in (BACKEND / "requirements.txt").read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            names.add(re.split(r"[\[<>=!~ ]", line, maxsplit=1)[0].lower().replace("_", "-"))
    return names


def _module_level_imports(path: Path) -> set[str]:
    tops = set()
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Import):
            tops |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            tops.add(node.module.split(".")[0])
    return tops


def test_every_third_party_import_loaded_at_startup_is_in_requirements():
    import src.main  # noqa: F401  (loads everything reachable at startup)

    src_files = [
        Path(m.__file__)
        for name, m in list(sys.modules.items())
        if name.startswith("src") and getattr(m, "__file__", None)
    ]
    assert src_files, "no src modules were loaded"

    dist_map = packages_distributions()
    declared = _declared()
    missing = {}
    for f in src_files:
        for top in _module_level_imports(f):
            if top == "src" or top in sys.stdlib_module_names:
                continue
            dists = {d.lower().replace("_", "-") for d in dist_map.get(top, [top])}
            if not dists & declared:
                missing.setdefault(sorted(dists)[0], []).append(f.name)
    assert not missing, f"imported but not in requirements.txt: {missing}"
