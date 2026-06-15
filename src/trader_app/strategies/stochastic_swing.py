from trader_app.strategies.base import Candle, Signal


def stochastic_k(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    """Fast Stochastic %K over a rolling window: 100 * (close - LL) / (HH - LL)."""
    result: list[float] = []
    for index in range(len(closes)):
        start = max(0, index - period + 1)
        window_low = min(lows[start : index + 1])
        window_high = max(highs[start : index + 1])
        span = window_high - window_low
        result.append(100 * (closes[index] - window_low) / span if span else 0.0)
    return result


class StochasticSwingStrategy:
    """Fast-Stochastic swing strategy from YouTube video vzgRhKBMSyE.

    - Entry (long): fast Stochastic %K (period 5) drops below level 5 (oversold).
    - Target exit: a configurable percentage above the entry price.
    - Trailing exit: a highest-high(period) line. The exit sits at
      min(target, highest_high); if price never reaches the target, the position
      exits when price touches the trailing highest-high line, which falls over
      time as old highs roll off. Long-only (matches the source video).
    """

    requires_transcript_review = False

    def __init__(
        self,
        stoch_period: int = 5,
        stoch_level: float = 5.0,
        highest_period: int = 5,
        target_pct: float = 3.0,
    ) -> None:
        self.stoch_period = stoch_period
        self.stoch_level = stoch_level
        self.highest_period = highest_period
        self.target_pct = target_pct
        self.name = "stochastic_swing"
        self.version = "1.0.0"

    def generate_signal(self, candles: list[Candle]) -> Signal:
        warmup = max(self.stoch_period, self.highest_period)
        if len(candles) < warmup + 1:
            return Signal(action="hold", reason="Not enough candles for the stochastic.")

        highs = [candle.high for candle in candles]
        lows = [candle.low for candle in candles]
        closes = [candle.close for candle in candles]
        k = stochastic_k(highs, lows, closes, self.stoch_period)[-1]
        last = candles[-1]

        if k < self.stoch_level:
            entry = last.close
            return Signal(
                action="buy",
                product_id=last.product_id,
                confidence=0.6,
                reason=f"Fast stochastic %K {k:.1f} below {self.stoch_level} (oversold).",
                entry_price=entry,
                take_profit=entry * (1 + self.target_pct / 100),
            )
        return Signal(action="hold", product_id=last.product_id, reason="Stochastic not oversold.")

    def exit_signal(self, candles: list[Candle], entry_price: float) -> float | None:
        """Return the fill price if an open long should exit this bar, else None.

        The exit limit is min(target, highest_high(period)); it fills when the
        latest bar's high reaches it.
        """
        if len(candles) < self.highest_period:
            return None
        target = entry_price * (1 + self.target_pct / 100)
        trail = max(candle.high for candle in candles[-self.highest_period:])
        limit = min(target, trail)
        if candles[-1].high >= limit:
            return limit
        return None
