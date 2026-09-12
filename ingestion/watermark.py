from __future__ import annotations

import json
from pathlib import Path


class WatermarkStore:

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}

        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get(self, entity: str) -> str | None:
        data = self.load()
        return data.get(entity)

    def save(self, entity: str, timestamp: str) -> None:
        data = self.load()
        data[entity] = timestamp

        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=2,
            )