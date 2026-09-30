from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ApprovalSchemaLoader:
    """
    Loads the schema used to constrain Gemini's classification output.
    """

    def __init__(self, schema_path: str | Path):
        self.schema_path = Path(schema_path)

    def load(self) -> dict[str, Any]:
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Approval schema not found: {self.schema_path}"
            )

        with self.schema_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            schema = json.load(file)

        if not isinstance(schema, dict):
            raise ValueError(
                "Approval schema must contain a JSON object."
            )

        return schema