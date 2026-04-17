from __future__ import annotations

from cuga_arc3.eval.harness import compute_reliability_metrics
from cuga_arc3.reporting import reliability_delta
from cuga_arc3.runner.events import PAYLOAD_KEY_RETRY_COUNT, PAYLOAD_KEY_STOP_REASON


def test_compute_reliability_metrics_counts_aborts() -> None:
    game_traces = [
        {
            "game_id": "g-1",
            "events": [
                {
                    "event_type": "episode_end",
                    "payload": {
                        PAYLOAD_KEY_STOP_REASON: "solved",
                        PAYLOAD_KEY_RETRY_COUNT: 0,
                    },
                }
            ],
        },
        {
            "game_id": "g-2",
            "events": [
                {
                    "event_type": "episode_end",
                    "payload": {
                        PAYLOAD_KEY_STOP_REASON: "aborted_max_retries",
                        PAYLOAD_KEY_RETRY_COUNT: 3,
                    },
                }
            ],
        },
        {
            "game_id": "g-3",
            "events": [
                {
                    "event_type": "episode_end",
                    "payload": {
                        PAYLOAD_KEY_STOP_REASON: "aborted_max_retries",
                        PAYLOAD_KEY_RETRY_COUNT: 2,
                    },
                }
            ],
        },
    ]

    metrics = compute_reliability_metrics(stage="S1", game_traces=game_traces)

    assert metrics.stage == "S1"
    assert metrics.total_episodes == 3
    assert metrics.abort_count == 2
    assert metrics.abort_rate == 2 / 3


def test_compute_reliability_metrics_sums_retries() -> None:
    game_traces = [
        {
            "game_id": "g-1",
            "events": [
                {"event_type": "retry", "payload": {}},
                {"event_type": "retry", "payload": {}},
                {
                    "event_type": "episode_end",
                    "payload": {
                        PAYLOAD_KEY_STOP_REASON: "max_steps_reached",
                    },
                },
            ],
        },
        {
            "game_id": "g-2",
            "events": [
                {"event_type": "retry", "payload": {}},
                {
                    "event_type": "episode_end",
                    "payload": {
                        PAYLOAD_KEY_STOP_REASON: "solved",
                        PAYLOAD_KEY_RETRY_COUNT: 1,
                    },
                },
            ],
        },
    ]

    metrics = compute_reliability_metrics(stage="S2", game_traces=game_traces)

    assert metrics.retry_total == 3
    assert metrics.mean_retries == 1.5
    assert metrics.invalid_action_count == 3


def test_reliability_delta_negative_abort_rate_is_improvement() -> None:
    baseline = compute_reliability_metrics(
        stage="S0",
        game_traces=[
            {
                "game_id": "g-1",
                "events": [
                    {
                        "event_type": "episode_end",
                        "payload": {
                            PAYLOAD_KEY_STOP_REASON: "aborted_max_retries",
                            PAYLOAD_KEY_RETRY_COUNT: 3,
                        },
                    }
                ],
            },
            {
                "game_id": "g-2",
                "events": [
                    {
                        "event_type": "episode_end",
                        "payload": {
                            PAYLOAD_KEY_STOP_REASON: "solved",
                            PAYLOAD_KEY_RETRY_COUNT: 1,
                        },
                    }
                ],
            },
        ],
    )
    candidate = compute_reliability_metrics(
        stage="S1",
        game_traces=[
            {
                "game_id": "g-1",
                "events": [
                    {
                        "event_type": "episode_end",
                        "payload": {
                            PAYLOAD_KEY_STOP_REASON: "solved",
                            PAYLOAD_KEY_RETRY_COUNT: 0,
                        },
                    }
                ],
            },
            {
                "game_id": "g-2",
                "events": [
                    {
                        "event_type": "episode_end",
                        "payload": {
                            PAYLOAD_KEY_STOP_REASON: "solved",
                            PAYLOAD_KEY_RETRY_COUNT: 1,
                        },
                    }
                ],
            },
        ],
    )

    delta = reliability_delta(baseline, candidate)

    assert delta["from_stage"] == "S0"
    assert delta["to_stage"] == "S1"
    assert delta["abort_rate_delta"] == -0.5
    assert delta["mean_retries_delta"] == -1.5
    assert delta["invalid_action_delta"] == 0
