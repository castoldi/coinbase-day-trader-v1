from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Candle:
    product_id: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    action: str
    product_id: str | None = None
    confidence: float = 0
    reason: str = ""


class Strategy(Protocol):
    name: str
    version: str
    requires_transcript_review: bool

    def generate_signal(self, candles: list[Candle]) -> Signal:
        ...
