import pytest

from trader_app.strategies.base import Candle
from trader_app.strategies.ema_ribbon_reversal import (
    Channels,
    EmaRibbonReversalStrategy,
    ema,
)


def candle(close: float, high: float, low: float, open_: float | None = None) -> Candle:
    return Candle(
        product_id="BTC-USD",
        timestamp="2024-01-01T00:00:00+00:00",
        open=open_ if open_ is not None else close,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )


def test_ema_matches_manual_calculation():
    values = ema([1.0, 2.0, 3.0], period=2)
    assert values[0] == pytest.approx(1.0)
    assert values[1] == pytest.approx(1.6667, abs=1e-3)
    assert values[2] == pytest.approx(2.5556, abs=1e-3)


def test_metadata():
    strategy = EmaRibbonReversalStrategy()
    assert strategy.name == "ema_ribbon_reversal"
    assert strategy.version == "1.0.0"
    assert strategy.requires_transcript_review is False


def test_hold_when_not_enough_candles():
    strategy = EmaRibbonReversalStrategy(white_len=2, channel_len=3, trend_len=4)
    candles = [candle(10, 11, 9) for _ in range(3)]
    assert strategy.generate_signal(candles).action == "hold"


def make_decide_inputs(green_upper, green_lower, white_upper, white_lower, orange, candles):
    channels = [
        Channels(
            white_upper=white_upper,
            white_lower=white_lower,
            green_upper=green_upper,
            green_lower=green_lower,
            orange=orange,
        )
        for _ in candles
    ]
    return channels


def test_decide_buy_on_long_setup():
    strategy = EmaRibbonReversalStrategy(pullback_window=3, risk_reward=2.0)
    # white channel fully above orange (110 > 100); recent pullback touched green
    # channel (a low of 102 <= green_upper 103); trigger candle closes above white (115 > 112).
    candles = [
        candle(close=108, high=109, low=104),
        candle(close=106, high=107, low=102),  # pullback touches green channel
        candle(close=115, high=116, low=111),  # closes above white channel -> trigger
    ]
    channels = make_decide_inputs(
        green_upper=103, green_lower=105, white_upper=112, white_lower=110, orange=100, candles=candles
    )
    signal = strategy._decide(candles, channels)
    assert signal.action == "buy"
    assert signal.entry_price == pytest.approx(115)
    assert signal.stop_loss == pytest.approx(105)
    assert signal.take_profit == pytest.approx(115 + 2 * (115 - 105))


def test_decide_sell_on_short_setup():
    strategy = EmaRibbonReversalStrategy(pullback_window=3, risk_reward=2.0)
    # white channel fully below orange (90 < 100); pullback up touched green channel
    # (a high of 98 >= green_lower 97); trigger candle closes below white (85 < 88).
    candles = [
        candle(close=92, high=94, low=91),
        candle(close=94, high=98, low=93),  # pullback up touches green channel
        candle(close=85, high=89, low=84),  # closes below white channel -> trigger
    ]
    channels = make_decide_inputs(
        green_upper=99, green_lower=97, white_upper=90, white_lower=88, orange=100, candles=candles
    )
    signal = strategy._decide(candles, channels)
    assert signal.action == "sell"
    assert signal.entry_price == pytest.approx(85)
    assert signal.stop_loss == pytest.approx(99)
    assert signal.take_profit == pytest.approx(85 - 2 * (99 - 85))


def test_decide_hold_when_no_pullback_touch():
    strategy = EmaRibbonReversalStrategy(pullback_window=3, risk_reward=2.0)
    # uptrend + trigger but no candle ever dipped to touch the green channel
    candles = [
        candle(close=120, high=121, low=118),
        candle(close=121, high=122, low=119),
        candle(close=125, high=126, low=121),  # closes above white but no pullback
    ]
    channels = make_decide_inputs(
        green_upper=103, green_lower=105, white_upper=112, white_lower=110, orange=100, candles=candles
    )
    assert strategy._decide(candles, channels).action == "hold"


def test_generate_signal_emits_a_buy_over_a_reversal_series():
    strategy = EmaRibbonReversalStrategy(white_len=3, channel_len=8, trend_len=13, pullback_window=6)
    closes: list[float] = []
    # established downtrend so EMAs start high and price below orange
    closes += [100 - i for i in range(40)]  # 100 .. 61
    # sharp reversal up, crossing above the lagging EMAs
    closes += [62 + 4 * i for i in range(25)]  # 62 .. 158
    # pullback down into the ribbon
    closes += [158 - 5 * i for i in range(6)]  # 158 .. 133
    # reclaim candle pushing back up
    closes += [150]

    candles = [candle(close=c, high=c + 2, low=c - 2) for c in closes]
    actions = [
        strategy.generate_signal(candles[: i + 1]).action for i in range(len(candles))
    ]
    assert "buy" in actions
