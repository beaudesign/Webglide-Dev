import httpx

from cuga_arc3.arc_adapter.client import ArcClient


def test_list_games_sends_bearer_token_and_returns_json_list() -> None:
    expected_games = [{"id": "game-1"}, {"id": "game-2"}]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/games"
        assert request.headers["Authorization"] == "Bearer test-api-key"
        return httpx.Response(status_code=200, json=expected_games)

    client = ArcClient(
        base_url="https://api.arcprize.org",
        api_key="test-api-key",
        transport=httpx.MockTransport(handler),
    )

    games = client.list_games()

    assert games == expected_games
