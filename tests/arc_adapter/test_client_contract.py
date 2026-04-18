import json

import httpx
import pytest

from cuga_arc3.arc_adapter.client import ArcClient


@pytest.mark.anyio
async def test_list_games_sends_api_key_header_and_returns_json_list() -> None:
    expected_games = [{"id": "game-1"}, {"id": "game-2"}]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/games"
        assert request.headers["X-API-Key"] == "test-api-key"
        return httpx.Response(status_code=200, json=expected_games)

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    games = await client.list_games()

    assert games == expected_games


@pytest.mark.anyio
async def test_open_scorecard_posts_metadata_payload() -> None:
    metadata = {"game_id": "game-1", "stage": "S0"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/scorecard/open"
        assert json.loads(request.content.decode()) == metadata
        return httpx.Response(status_code=200, json={"guid": "g-1"})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.open_scorecard(metadata)

    assert response == {"guid": "g-1"}


@pytest.mark.anyio
async def test_reset_or_start_posts_required_fields_without_guid() -> None:
    expected_payload = {"game_id": "game-1", "card_id": "card-1"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/cmd/RESET"
        assert json.loads(request.content.decode()) == expected_payload
        return httpx.Response(status_code=200, json={"ok": True})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.reset_or_start(game_id="game-1", card_id="card-1")

    assert response == {"ok": True}


@pytest.mark.anyio
async def test_reset_or_start_posts_guid_when_provided() -> None:
    expected_payload = {"game_id": "game-1", "card_id": "card-1", "guid": "guid-1"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/cmd/RESET"
        assert json.loads(request.content.decode()) == expected_payload
        return httpx.Response(status_code=200, json={"ok": True})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.reset_or_start(
        game_id="game-1",
        card_id="card-1",
        guid="guid-1",
    )

    assert response == {"ok": True}


@pytest.mark.anyio
async def test_execute_action_uses_action6_endpoint_with_coordinates_payload() -> None:
    expected_payload = {"guid": "guid-1", "game_id": "", "x": 3, "y": 4}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/cmd/ACTION6"
        assert json.loads(request.content.decode()) == expected_payload
        return httpx.Response(status_code=200, json={"ok": True})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.execute_action(guid="guid-1", action=6, x=3, y=4)

    assert response == {"ok": True}


@pytest.mark.anyio
async def test_execute_action_uses_action_number_endpoint_for_non_6() -> None:
    expected_payload = {"guid": "guid-1", "game_id": ""}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/cmd/ACTION4"
        assert json.loads(request.content.decode()) == expected_payload
        return httpx.Response(status_code=200, json={"ok": True})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.execute_action(guid="guid-1", action=4)

    assert response == {"ok": True}


@pytest.mark.anyio
async def test_execute_action_raises_when_action6_missing_coordinates() -> None:
    client = ArcClient(base_url="https://three.arcprize.org", api_key="test-api-key")

    with pytest.raises(ValueError, match="x and y are required for action 6"):
        await client.execute_action(guid="guid-1", action=6, x=None, y=1)


@pytest.mark.anyio
async def test_close_scorecard_sends_card_id() -> None:
    expected_payload = {"card_id": "card-123"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/scorecard/close"
        assert json.loads(request.content.decode()) == expected_payload
        return httpx.Response(status_code=200, json={"status": "closed"})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.close_scorecard(card_id="card-123")

    assert response == {"status": "closed"}


@pytest.mark.anyio
async def test_get_scorecard_uses_card_id_in_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/scorecard/card-123"
        return httpx.Response(status_code=200, json={"card_id": "card-123"})

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    response = await client.get_scorecard(card_id="card-123")

    assert response == {"card_id": "card-123"}


@pytest.mark.anyio
async def test_request_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0
    sleep_durations: list[float] = []

    async def fake_sleep(duration: float) -> None:
        sleep_durations.append(duration)

    monkeypatch.setattr("cuga_arc3.arc_adapter.client.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("cuga_arc3.arc_adapter.client.random.uniform", lambda _a, _b: 0.0)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            return httpx.Response(
                status_code=429,
                request=request,
                json={"error": "rate_limited"},
            )
        return httpx.Response(status_code=200, request=request, json=[{"id": "game-1"}])

    client = ArcClient(
        base_url="https://three.arcprize.org",
        api_key="test-api-key",
        _transport=httpx.MockTransport(handler),
    )

    games = await client.list_games()

    assert games == [{"id": "game-1"}]
    assert attempts == 3
    assert sleep_durations == [1.0, 2.0]
