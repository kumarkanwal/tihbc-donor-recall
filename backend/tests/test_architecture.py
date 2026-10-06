"""Repository-wide backend architecture guardrails."""

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "app"
MAX_PYTHON_FILE_LINES = 400


def test_application_files_stay_below_the_hard_line_limit() -> None:
    oversized = {
        path.relative_to(APP_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in APP_ROOT.rglob("*.py")
        if len(path.read_text(encoding="utf-8").splitlines()) > MAX_PYTHON_FILE_LINES
    }

    assert oversized == {}


def test_business_code_does_not_bypass_the_clock_or_config() -> None:
    violations: list[str] = []
    for path in APP_ROOT.rglob("*.py"):
        relative_path = path.relative_to(APP_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        forbidden = ["datetime.utcnow(", "os.environ"]
        if relative_path != "core/clock.py":
            forbidden.append("datetime.now(")
        for expression in forbidden:
            if expression in source:
                violations.append(f"{relative_path}: {expression}")

    assert violations == []
