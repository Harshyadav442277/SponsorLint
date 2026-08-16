"""The zero-key path, guarded by a test.

A module-scope `faster_whisper`, `pypdf` or LLM-client import anywhere on the
demo path makes `python -m sponsorlint demo` die with ModuleNotFoundError in a
demo-only venv, **before dispatch runs** — and it is invisible on a dev machine
that has those packages installed. This test is the tripwire.
"""

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "sponsorlint"

#: Anything not in requirements-demo.txt.
FULL_ONLY = ("faster_whisper", "pypdf", "anthropic", "openai", "torch")

#: Modules reachable from `demo`, `verify` and `eval`.
DEMO_PATH = [
    "__init__.py",
    "__main__.py",
    "cli.py",
    "models.py",
    "lint/*.py",
    "normalize/*.py",
    "report/*.py",
    "eval/*.py",
    "web/app.py",
]


def demo_path_files() -> list[Path]:
    files: list[Path] = []
    for pattern in DEMO_PATH:
        files.extend(sorted(PACKAGE.glob(pattern)))
    return files


def module_scope_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in tree.body:  # module scope only — nested imports are the fix
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


@pytest.mark.parametrize(
    "path", demo_path_files(), ids=lambda p: str(p.relative_to(PACKAGE))
)
def test_no_full_only_import_at_module_scope(path):
    offenders = [
        name
        for name in module_scope_imports(path)
        if name.split(".")[0] in FULL_ONLY
    ]
    assert offenders == [], (
        f"{path.relative_to(PACKAGE)} imports {offenders} at module scope. "
        f"Move it inside the command branch that needs it — otherwise "
        f"`python -m sponsorlint demo` dies on a judge's machine."
    )


def test_demo_path_covers_every_module_it_should():
    assert len(demo_path_files()) >= 15
