from __future__ import annotations

from typing import Dict, List

from .config import AppConfig
from .llm import LLMClient, Prediction, make_llm
from .notes import load_notes


class Predictor:
    def __init__(self, config: AppConfig):
        self.config = config
        self.llm: LLMClient = make_llm(config.llm)
        self.cached_notes = load_notes(config.run.notes_path)

    def build_context(self, eps_surprise: float | None, extra: Dict[str, str] | None = None) -> Dict[str, str]:
        context: Dict[str, str] = {"eps_surprise": eps_surprise or 0.0}
        if self.cached_notes:
            context["notes"] = " ; ".join(self.cached_notes[-5:])
        if extra:
            context.update(extra)
        return context

    def predict(self, ticker: str, eps_surprise: float | None, extra: Dict[str, str] | None = None) -> Prediction:
        context = self.build_context(eps_surprise, extra)
        return self.llm.predict_direction(ticker, context)

    def remaining_budget(self) -> int:
        return self.llm.remaining_budget

    def refresh_notes(self) -> List[str]:
        self.cached_notes = load_notes(self.config.run.notes_path)
        return self.cached_notes
