from __future__ import annotations

from typing import Any

import requests


class APIClient:

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch(
        self,
        endpoint: str,
        timestamp_param: str | None = None,
        timestamp_value: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:

        all_records: list[dict[str, Any]] = []
        offset = 0

        while True:

            params = {
                "limit": limit,
                "offset": offset,
            }

            if timestamp_param and timestamp_value:
                params[timestamp_param] = timestamp_value

            response = requests.get(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

            payload = response.json()
            records = payload.get("data", [])

            if not records:
                break

            all_records.extend(records)

            if len(records) < limit:
                break

            offset += limit

        return all_records