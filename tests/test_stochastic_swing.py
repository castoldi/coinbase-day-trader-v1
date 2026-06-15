import pytest

from trader_app.strategies.base import Candle
from trader_app.strategies.stochastic_swing import (
    StochasticSwingStrategy,
    stochastic_k,
)


def candle(close: float, high: float, low: float) -> Candle:
    return Candle(
        product_id="BTC-USD",
        timestamp="2024-01-01T00:00:00+00:00",
        open=close,
        high=high,
        low=low,
        close=close,
        volume=1000,
    )


def test_stochastic_k_matches_definition():
    highs = [10.0, 10.0, 10.0, 10.0, 10.0]
    lows = [0.0, 0.0, 0.0, 0.0, 0.0]
    closes = [5.0, 5.0, 5.0, 5.0, 2.0]
    values = stochastic_k(highs, lows, closes, period=5)
    assert values[-1] == pytest.approx(20.0)  # 100 * (2 - 0) / (10 - 0)


def test_metadata():
    strategy = StochasticSwingStrategy()
    assert strategy.name == "stochastic_swing"
    assert strategy.version == "1.0.0"
    assert strategy.requires_transcript_review is False


def test_hold_when_not_enough_candles():
    strategy = StochasticSwingStrategy(stoch_period=5, highest_period=5)
    candles = [candle(5, 10, 0) for _ in range(3)]
    assert strategy.generate_signal(candles).action == "hold"


def test_buy_when_stochastic_is_oversold():
    strategy = StochasticSwingStrategy(stoch_period=5, stoch_level=5, highest_period=5, target_pct=3.0)
    # last close near the bottom of the 5-bar range -> %K below 5
    candles = [candle(5, 10, 0) for _ in range(5)] + [candle(0.3, 10, 0)]
    signal = strategy.generate_signal(candles)
    assert signal.action == "buy"
    assert signal.product_id == "BTC-USD"
    assert signal.entry_price == pytest.approx(0.3)
    assert signal.take_profit == pytest.approx(0.3 * 1.03)


def test_hold_when_not_oversold():
    strategy = StochasticSwingStrategy(stoch_period=5, stoch_level=5, highest_period=5)
    candles = [candle(5, 10, 0) for _ in range(5)] + [candle(9.5, 10, 0)]
    assert strategy.generate_signal(candles).action == "hold"


def test_exit_signal_fills_at_percentage_target():
    strategy = StochasticSwingStrategy(highest_period=5, target_pct=3.0)
    # target = 103; recent highs reach 104 so the limit is the 103 target
    candles = [candle(101, 101, 100) for _ in range(4)] + [candle(103, 104, 102)]
    assert strategy.exit_signal(candles, entry_price=100.0) == pytest.approx(103.0)


def test_exit_signal_trails_to_highest_high_below_target():
    strategy = StochasticSwingStrategy(highest_period=5, target_pct=3.0)
    # target = 103 but recent highs top out at 100; bar touches the trailing line
    candles = [candle(99, 99, 98) for _ in range(4)] + [candle(100, 100, 98)]
    assert strategy.exit_signal(candles, entry_price=100.0) == pytest.approx(100.0)


def test_exit_signal_returns_none_when_price_below_limit():
    strategy = StochasticSwingStrategy(highest_period=5, target_pct=3.0)
    candles = [candle(99, 99, 98) for _ in range(4)] + [candle(98, 98.5, 97)]
    assert strategy.exit_signal(candles, entry_price=100.0) is None
