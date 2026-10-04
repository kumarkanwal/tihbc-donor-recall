"""Export the backend OpenAPI contract for the frontend client."""

import json
from pathlib import Path

from app.main import app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPOSITORY_ROOT / "frontend" / "openapi.json"


def build_openapi_json() -> str:
    """Serialize the current OpenAPI schema in a deterministic format."""
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def export_openapi(output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    """Write the current OpenAPI schema to the requested path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_openapi_json(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    export_openapi()
