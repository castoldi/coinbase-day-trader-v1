from trader_app.strategies.base import Candle, Signal
from trader_app.strategies.ema_ribbon_reversal import ema


def macd(
    closes: list[float], fast: int, slow: int, signal: int
) -> tuple[list[float], list[float]]:
    """MACD line (fast EMA - slow EMA) and its signal line (EMA of the MACD line)."""
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


class TripleScreenTrendStrategy:
    """Triple-screen trend-continuation strategy from YouTube video O3Q1uxBaIc0.

    Adapted from a Renko triple-screen (Alexander Elder) approach:
    - Trend: EMA 27 vs EMA 55 define the higher-timeframe direction.
    - Momentum filter: MACD must agree (the source colors the box green only
      when MACD is bullish).
    - Entry (long): in an uptrend, price pulls back to the moving-average zone
      and then reclaims the fast EMA with a bullish candle.
    - Stop at the recent swing low; target at a 3:1 reward:risk.

    Long-only; Renko brick construction and order-flow from the source video are
    not available on daily candles, so the indicator core is implemented here.
    """

    requires_transcript_review = False

    def __init__(
        self,
        ema_fast: int = 27,
        ema_slow: int = 55,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        risk_reward: float = 3.0,
        swing_lookback: int = 3,
    ) -> None:
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.risk_reward = risk_reward
        self.swing_lookback = swing_lookback
        self.name = "triple_screen_trend"
        self.version = "1.0.0"

    def generate_signal(self, candles: list[Candle]) -> Signal:
        warmup = max(self.ema_slow, self.macd_slow) + 2
        if len(candles) < warmup:
            return Signal(action="hold", reason="Not enough candles for the trend filters.")

        closes = [candle.close for candle in candles]
        ema_fast = ema(closes, self.ema_fast)[-1]
        ema_slow = ema(closes, self.ema_slow)[-1]
        macd_line, signal_line = macd(closes, self.macd_fast, self.macd_slow, self.macd_signal)
        macd_bullish = macd_line[-1] >= signal_line[-1]
        last = candles[-1]
        product_id = last.product_id

        if ema_fast > ema_slow:
            pulled_back = last.low <= ema_fast
            reclaimed = last.close > ema_fast and last.close > last.open
            if pulled_back and reclaimed and macd_bullish:
                entry = last.close
                stop_loss = min(candle.low for candle in candles[-self.swing_lookback:])
                risk = entry - stop_loss
                if risk > 0:
                    return Signal(
                        action="buy",
                        product_id=product_id,
                        confidence=0.6,
                        reason="Uptrend pullback reclaim with bullish MACD.",
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=entry + self.risk_reward * risk,
                    )
            return Signal(action="hold", product_id=product_id, reason="Uptrend but no qualifying entry.")

        if ema_fast < ema_slow:
            return Signal(
                action="sell",
                product_id=product_id,
                confidence=0.6,
                reason="Trend flipped down (fast EMA below slow EMA); exit longs.",
            )

        return Signal(action="hold", product_id=product_id, reason="No trend alignment.")
