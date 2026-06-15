from dataclasses import dataclass

from trader_app.strategies.base import Candle, Signal


def ema(values: list[float], period: int) -> list[float]:
    """Exponential moving average seeded with the first value."""
    if not values:
        return []
    multiplier = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(value * multiplier + result[-1] * (1 - multiplier))
    return result


@dataclass(frozen=True)
class Channels:
    white_upper: float  # EMA(high, white_len)
    white_lower: float  # EMA(low, white_len)
    green_upper: float  # EMA(high, channel_len)
    green_lower: float  # EMA(low, channel_len)
    orange: float  # EMA(close, trend_len)


class EmaRibbonReversalStrategy:
    """EMA ribbon reversal strategy from YouTube video HkMXGqz7MRI.

    - Orange line (EMA 200 close) identifies the trend.
    - Green channel (EMA 100 of high/low) marks the pullback zone.
    - White channel (EMA 5 of high/low) confirms the end of the pullback.

    Long: white channel fully above orange, price pulls back to touch the green
    channel, then a candle closes above the white channel. Stop below the green
    channel, target at the configured reward:risk. Short is the mirror image.
    """

    requires_transcript_review = False

    def __init__(
        self,
        white_len: int = 5,
        channel_len: int = 100,
        trend_len: int = 200,
        risk_reward: float = 2.0,
        pullback_window: int = 10,
    ) -> None:
        self.white_len = white_len
        self.channel_len = channel_len
        self.trend_len = trend_len
        self.risk_reward = risk_reward
        self.pullback_window = pullback_window
        self.name = "ema_ribbon_reversal"
        self.version = "1.0.0"

    def channels(self, candles: list[Candle]) -> list[Channels]:
        highs = [candle.high for candle in candles]
        lows = [candle.low for candle in candles]
        closes = [candle.close for candle in candles]
        white_upper = ema(highs, self.white_len)
        white_lower = ema(lows, self.white_len)
        green_upper = ema(highs, self.channel_len)
        green_lower = ema(lows, self.channel_len)
        orange = ema(closes, self.trend_len)
        return [
            Channels(
                white_upper=white_upper[i],
                white_lower=white_lower[i],
                green_upper=green_upper[i],
                green_lower=green_lower[i],
                orange=orange[i],
            )
            for i in range(len(candles))
        ]

    def generate_signal(self, candles: list[Candle]) -> Signal:
        if len(candles) < self.trend_len + 2:
            return Signal(action="hold", reason="Not enough candles to compute EMAs.")
        return self._decide(candles, self.channels(candles))

    def _decide(self, candles: list[Candle], channels: list[Channels]) -> Signal:
        last = candles[-1]
        current = channels[-1]
        product_id = last.product_id
        window = candles[-self.pullback_window:]
        window_channels = channels[-self.pullback_window:]

        # Long setup: white channel fully above the orange trend line.
        if current.white_lower > current.orange:
            touched_green = any(
                bar.low <= chan.green_upper for bar, chan in zip(window, window_channels)
            )
            triggered = last.close > current.white_upper
            if touched_green and triggered:
                entry = last.close
                stop_loss = current.green_lower
                risk = entry - stop_loss
                if risk > 0:
                    return Signal(
                        action="buy",
                        product_id=product_id,
                        confidence=0.6,
                        reason="Long reversal: pullback to green channel, close above white channel.",
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=entry + self.risk_reward * risk,
                    )

        # Short setup: white channel fully below the orange trend line.
        if current.white_upper < current.orange:
            touched_green = any(
                bar.high >= chan.green_lower for bar, chan in zip(window, window_channels)
            )
            triggered = last.close < current.white_lower
            if touched_green and triggered:
                entry = last.close
                stop_loss = current.green_upper
                risk = stop_loss - entry
                if risk > 0:
                    return Signal(
                        action="sell",
                        product_id=product_id,
                        confidence=0.6,
                        reason="Short reversal: pullback to green channel, close below white channel.",
                        entry_price=entry,
                        stop_loss=stop_loss,
                        take_profit=entry - self.risk_reward * risk,
                    )

        return Signal(action="hold", product_id=product_id, reason="No confirmed reversal setup.")
