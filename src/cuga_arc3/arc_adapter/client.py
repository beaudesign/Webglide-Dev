from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ArcClient:
    base_url: str
    api_key: str
    transport: httpx.BaseTransport | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        with httpx.Client(base_url=self.base_url, transport=self.transport) as client:
            response = client.request(
                method=method,
                url=path,
                headers=self._headers(),
                json=json_body,
            )

        response.raise_for_status()
        return response.json()

    def list_games(self) -> list[Any]:
        return self._request("GET", "/games")

    def open_scorecard(self, metadata: dict[str, Any]) -> Any:
        return self._request("POST", "/scorecards/open", json_body=metadata)

    def reset_or_start(
        self,
        game_id: str,
        card_id: str,
        guid: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"game_id": game_id, "card_id": card_id}
        if guid is not None:
            payload["guid"] = guid

        return self._request("POST", "/commands/reset", json_body=payload)

    def execute_action(
        self,
        guid: str,
        action: int,
        x: int | None = None,
        y: int | None = None,
    ) -> Any:
        endpoint = "/commands/action6" if action == 6 else f"/commands/action{action}"
        payload: dict[str, Any] = {"guid": guid}
        if action == 6:
            payload["x"] = x
            payload["y"] = y

        return self._request("POST", endpoint, json_body=payload)
