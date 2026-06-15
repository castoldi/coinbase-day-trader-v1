"""Human-facing descriptions and illustrative chart examples for strategies.

The example candles are hand-built teaching diagrams (not live data) so the
Strategy page can render entry, stop-loss, and take-profit annotations.
"""


def _candle(open_: float, high: float, low: float, close: float) -> dict[str, float]:
    return {"open": open_, "high": high, "low": low, "close": close}


# Long reversal: downtrend, cross above trend, pullback into the green channel,
# then a candle closes above the white channel -> long entry at 105.
_LONG_EXAMPLE = {
    "label": "Long reversal setup",
    "side": "long",
    "candles": [
        _candle(118, 119, 112, 113),
        _candle(113, 114, 106, 107),
        _candle(107, 109, 101, 102),
        _candle(102, 104, 98, 103),
        _candle(103, 107, 102, 106),
        _candle(106, 110, 105, 109),
        _candle(109, 111, 103, 104),  # pullback into green channel
        _candle(104, 106, 100, 101),  # touches green channel low
        _candle(101, 108, 101, 105),  # closes above white channel -> entry
        _candle(105, 112, 104, 111),
        _candle(111, 116, 110, 115),  # take-profit reached
        _candle(115, 117, 113, 116),
    ],
    "entry": 105.0,
    "stop_loss": 100.0,
    "take_profit": 115.0,
    "entry_index": 8,
}

# Short reversal: mirror image -> short entry at 95.
_SHORT_EXAMPLE = {
    "label": "Short reversal setup",
    "side": "short",
    "candles": [
        _candle(82, 88, 81, 87),
        _candle(87, 94, 86, 93),
        _candle(93, 99, 92, 98),
        _candle(98, 102, 96, 97),
        _candle(97, 98, 93, 94),
        _candle(94, 95, 90, 91),
        _candle(91, 97, 90, 96),  # pullback into green channel
        _candle(96, 100, 95, 99),  # touches green channel high
        _candle(99, 99, 92, 95),  # closes below white channel -> entry
        _candle(95, 96, 88, 89),
        _candle(89, 90, 84, 85),  # take-profit reached
        _candle(85, 87, 83, 84),
    ],
    "entry": 95.0,
    "stop_loss": 100.0,
    "take_profit": 85.0,
    "entry_index": 8,
}


# Stochastic swing long: oversold dip, then price rallies to the % target.
_STOCH_TARGET_EXAMPLE = {
    "label": "Oversold dip → % target",
    "side": "long",
    "candles": [
        _candle(105, 106, 103, 104),
        _candle(104, 105, 101, 102),
        _candle(102, 103, 99, 100),  # %K below 5 (oversold) -> buy at 100
        _candle(100, 104, 100, 103),  # rallies to the +3% target
        _candle(103, 107, 102, 106),
        _candle(106, 108, 105, 107),
    ],
    "entry": 100.0,
    "stop_loss": 99.0,  # trailing highest-high exit line (no hard stop in this strategy)
    "take_profit": 103.0,
    "entry_index": 2,
}

# Stochastic swing long: target missed, position exits on the trailing highest-high line.
_STOCH_TRAIL_EXAMPLE = {
    "label": "Trailing exit (target missed)",
    "side": "long",
    "candles": [
        _candle(105, 106, 103, 104),
        _candle(104, 105, 101, 102),
        _candle(102, 103, 98, 100),  # oversold -> buy at 100
        _candle(100, 101, 99, 100),  # weak bounce, stays under the +3% target
        _candle(100, 100, 97, 98),   # rolls over
        _candle(98, 99, 96, 97),     # exits on the falling highest-high line
    ],
    "entry": 100.0,
    "stop_loss": 99.0,  # trailing highest-high exit line
    "take_profit": 103.0,
    "entry_index": 2,
}


def strategy_catalog() -> list[dict[str, object]]:
    return [
        {
            "name": "ema_ribbon_reversal",
            "version": "1.0.0",
            "title": "EMA Ribbon Reversal",
            "summary": (
                "A reversal strategy that catches the start of a new trend using a ribbon of "
                "exponential moving averages. Adapted from the source price-action video."
            ),
            "rules": {
                "indicators": [
                    "Orange line: EMA(200) of close — overall trend direction.",
                    "Green channel: EMA(100) of high and EMA(100) of low — the pullback zone.",
                    "White channel: EMA(5) of high and EMA(5) of low — end-of-pullback trigger.",
                ],
                "entry": (
                    "Long: price and the white channel cross above the orange line, price pulls back "
                    "to touch the green channel, then a candle closes above the white channel. "
                    "Short is the mirror image (close below the white channel)."
                ),
                "stop_loss": "Just beyond the green channel (below it for longs, above it for shorts).",
                "take_profit": "Fixed 2:1 reward-to-risk from entry.",
                "risk": "Author recommends the 1% risk rule per trade.",
            },
            "examples": [_LONG_EXAMPLE, _SHORT_EXAMPLE],
        },
        {
            "name": "stochastic_swing",
            "version": "1.0.0",
            "title": "Fast Stochastic Swing",
            "summary": (
                "A long-only swing strategy that buys oversold dips on the fast Stochastic and takes "
                "a small fixed percentage profit, with a trailing highest-high exit. Adapted from the "
                "source swing-trade video."
            ),
            "rules": {
                "indicators": [
                    "Fast Stochastic %K (period 5) — momentum / oversold detector.",
                    "Highest-high (period 5) — trailing exit line.",
                ],
                "entry": "Long when the fast Stochastic %K drops below 5 (oversold); buy at the close.",
                "stop_loss": (
                    "No hard stop. The position exits on the trailing highest-high line, which "
                    "falls over time as old highs roll off."
                ),
                "take_profit": "A configurable percentage above entry (default 3%); smaller targets raise the win rate.",
                "risk": "Long-only; diversify across several tickers because setups are infrequent.",
            },
            "examples": [_STOCH_TARGET_EXAMPLE, _STOCH_TRAIL_EXAMPLE],
        },
    ]
