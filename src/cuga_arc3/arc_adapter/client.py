from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ArcClient:
    base_url: str
    api_key: str
    transport: httpx.AsyncBaseTransport | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            transport=self.transport,
            timeout=30.0,
        ) as client:
            response = await client.request(
                method=method,
                url=path,
                headers=self._headers(),
                json=json_body,
            )

        response.raise_for_status()
        return response.json()

    async def list_games(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/games")

    async def open_scorecard(self, metadata: dict[str, Any]) -> Any:
        return await self._request("POST", "/scorecards/open", json_body=metadata)

    async def reset_or_start(
        self,
        game_id: str,
        card_id: str,
        guid: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"game_id": game_id, "card_id": card_id}
        if guid is not None:
            payload["guid"] = guid

        return await self._request("POST", "/commands/reset", json_body=payload)

    async def execute_action(
        self,
        guid: str,
        action: int,
        x: int | None = None,
        y: int | None = None,
    ) -> Any:
        endpoint = "/commands/action6" if action == 6 else f"/commands/action{action}"
        payload: dict[str, Any] = {"guid": guid}
        if action == 6:
            if x is None or y is None:
                raise ValueError("x and y are required for action 6")
            payload["x"] = x
            payload["y"] = y

        return await self._request("POST", endpoint, json_body=payload)
