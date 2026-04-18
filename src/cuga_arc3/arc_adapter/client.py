from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class ArcClient:
    """Stateful ARC-3 API client.

    Must be used as an async context manager so the underlying httpx session
    (with its cookie jar) is shared across RESET and ACTION calls for
    session affinity (AWSALB* cookies required by the API).

        async with ArcClient(...) as client:
            await client.reset_or_start(...)
            await client.execute_action(...)

    For stateless one-off calls (list_games, open/close scorecard) a
    context-manager is not required but is still safe to use.
    """

    base_url: str
    api_key: str
    max_retries: int = 3
    # Injected in tests via a custom transport; None = real network.
    _transport: httpx.AsyncBaseTransport | None = field(default=None, repr=False)
    _session: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    # --- Context manager -------------------------------------------------------

    async def __aenter__(self) -> "ArcClient":
        self._session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            transport=self._transport,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._session is not None:
            await self._session.aclose()
            self._session = None

    # --- Internal request helper -----------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key}

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        retry_limit = max(self.max_retries, 0)
        for attempt in range(retry_limit + 1):
            if self._session is not None:
                response = await self._session.request(
                    method=method,
                    url=path,
                    headers=self._headers(),
                    json=json_body,
                )
            else:
                # Stateless fallback for tests / one-off calls without context manager.
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=30.0,
                    transport=self._transport,
                ) as client:
                    response = await client.request(
                        method=method,
                        url=path,
                        headers=self._headers(),
                        json=json_body,
                    )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                status_code = response.status_code
                retriable = status_code == 429 or 500 <= status_code < 600
                if not retriable or attempt >= retry_limit:
                    raise
                backoff_seconds = float(2**attempt)
                jitter_seconds = random.uniform(0.0, 0.5)
                await asyncio.sleep(backoff_seconds + jitter_seconds)
                continue

            return response.json()

        raise RuntimeError("unreachable")

    # --- API methods -----------------------------------------------------------

    async def list_games(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/games")

    async def open_scorecard(self, metadata: dict[str, Any]) -> Any:
        return await self._request("POST", "/api/scorecard/open", json_body=metadata)

    async def close_scorecard(self, card_id: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/scorecard/close",
            json_body={"card_id": card_id},
        )

    async def get_scorecard(self, card_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/scorecard/{card_id}")

    async def reset_or_start(
        self,
        game_id: str,
        card_id: str,
        guid: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"game_id": game_id, "card_id": card_id}
        if guid is not None:
            payload["guid"] = guid
        return await self._request("POST", "/api/cmd/RESET", json_body=payload)

    async def execute_action(
        self,
        guid: str,
        action: int,
        game_id: str = "",
        x: int | None = None,
        y: int | None = None,
    ) -> Any:
        endpoint = f"/api/cmd/ACTION{action}"
        payload: dict[str, Any] = {"guid": guid, "game_id": game_id}
        if action == 6:
            if x is None or y is None:
                raise ValueError("x and y are required for action 6")
            payload["x"] = x
            payload["y"] = y
        return await self._request("POST", endpoint, json_body=payload)
