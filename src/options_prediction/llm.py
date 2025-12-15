from __future__ import annotations

import dataclasses
from typing import Dict, List

from .config import LLMConfig


@dataclasses.dataclass
class Prediction:
    direction: str
    confidence: float
    rationale: str


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._used_tokens = 0

    @property
    def remaining_budget(self) -> int:
        return max(self.config.request_budget - self._used_tokens, 0)

    def predict_direction(self, ticker: str, context: Dict[str, str]) -> Prediction:
        raise NotImplementedError


class HeuristicLLM(LLMClient):
    """A lightweight, offline-friendly stand-in for an LLM call."""

    def predict_direction(self, ticker: str, context: Dict[str, str]) -> Prediction:
        surprise = float(context.get("eps_surprise", 0.0) or 0.0)
        rationale_parts: List[str] = []
        if surprise > 0:
            direction = "up"
            confidence = min(0.5 + surprise, 0.95)
            rationale_parts.append("Positive EPS surprise suggests bullish move.")
        elif surprise < 0:
            direction = "down"
            confidence = min(0.5 + abs(surprise), 0.95)
            rationale_parts.append("Negative EPS surprise suggests bearish move.")
        else:
            direction = "flat"
            confidence = 0.4
            rationale_parts.append("No surprise detected; expecting muted reaction.")

        notes = context.get("notes")
        if notes:
            rationale_parts.append(f"Incorporated notes: {notes}")
        self._used_tokens += int(len(rationale_parts) * 50)
        return Prediction(direction=direction, confidence=confidence, rationale=" ".join(rationale_parts))


def make_llm(config: LLMConfig) -> LLMClient:
    return HeuristicLLM(config)
