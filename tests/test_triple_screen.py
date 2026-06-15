import pytest

from trader_app.strategies.base import Candle
from trader_app.strategies.triple_screen_trend import TripleScreenTrendStrategy, macd


def make_candles(closes, lows, opens):
    return [
        Candle(
            product_id="BTC-USD",
            timestamp=f"2024-01-{i + 1:02d}T00:00:00+00:00",
            open=opens[i],
            high=max(closes[i], opens[i]) + 1,
            low=lows[i],
            close=closes[i],
            volume=1000,
        )
        for i in range(len(closes))
    ]


def test_macd_matches_manual_calculation():
    macd_line, signal_line = macd([1.0, 2.0, 3.0, 4.0], fast=2, slow=3, signal=2)
    assert len(macd_line) == 4
    assert len(signal_line) == 4
    assert macd_line[-1] == pytest.approx(0.393, abs=1e-3)


def test_metadata():
    strategy = TripleScreenTrendStrategy()
    assert strategy.name == "triple_screen_trend"
    assert strategy.version == "1.0.0"
    assert strategy.requires_transcript_review is False


def test_hold_when_not_enough_candles():
    strategy = TripleScreenTrendStrategy(ema_fast=2, ema_slow=3, macd_fast=2, macd_slow=3, macd_signal=2)
    candles = make_candles([10, 11, 12], [9, 10, 11], [10, 10, 11])
    assert strategy.generate_signal(candles).action == "hold"


def small_strategy():
    return TripleScreenTrendStrategy(
        ema_fast=2,
        ema_slow=3,
        macd_fast=2,
        macd_slow=3,
        macd_signal=2,
        risk_reward=3.0,
        swing_lookback=3,
    )


def test_buy_on_pullback_in_uptrend_with_bullish_macd():
    closes = [10, 12, 14, 16, 18, 20]
    lows = [9, 11, 13, 15, 17, 18]
    opens = [9, 11, 13, 15, 17, 18]
    signal = small_strategy().generate_signal(make_candles(closes, lows, opens))
    assert signal.action == "buy"
    assert signal.entry_price == pytest.approx(20.0)
    assert signal.stop_loss == pytest.approx(15.0)
    assert signal.take_profit == pytest.approx(20 + 3 * (20 - 15))


def test_macd_filter_blocks_buy_when_momentum_rolls_over():
    # EMA still in an uptrend, valid pullback + reclaim, but MACD has turned bearish.
    closes = [10, 20, 28, 33, 35, 36, 36.5]
    lows = [9, 19, 27, 32, 34, 35, 35]
    opens = [9, 19, 27, 32, 34, 35, 36]
    assert small_strategy().generate_signal(make_candles(closes, lows, opens)).action == "hold"


def test_sell_when_trend_flips_down():
    closes = [20, 18, 16, 14, 12, 10]
    lows = [19, 17, 15, 13, 11, 9]
    opens = [21, 19, 17, 15, 13, 11]
    assert small_strategy().generate_signal(make_candles(closes, lows, opens)).action == "sell"
