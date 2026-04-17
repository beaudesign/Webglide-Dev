from __future__ import annotations

from dataclasses import dataclass

from cuga_arc3.runner.events import TraceEvent


@dataclass(frozen=True)
class ActionPrior:
    action: int
    confidence: float
    rationale: str


def infer_action_prior(observation: dict[str, object], step_idx: int) -> ActionPrior:
    _ = observation
    action = step_idx % 5 + 1
    confidence = round(0.5 + (step_idx % 3) * 0.15, 2)
    rationale = f"S2 tool-prior: action {action} favoured at step {step_idx}"
    return ActionPrior(action=action, confidence=confidence, rationale=rationale)


def feature_extraction_event(
    stage: str, game_id: str, step_idx: int, prior: ActionPrior
) -> TraceEvent:
    return TraceEvent(
        event_type="feature_extraction",
        stage=stage,
        game_id=game_id,
        step_idx=step_idx,
        payload={
            "action": prior.action,
            "confidence": prior.confidence,
            "rationale": prior.rationale,
        },
    )
