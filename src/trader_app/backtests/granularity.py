# Candle granularities supported by the Coinbase exchange candles endpoint,
# mapped to their length in seconds. The names double as cache-file suffixes
# (e.g. data/market/BTC-USD-FIVE_MINUTE.json).
GRANULARITY_SECONDS: dict[str, int] = {
    "ONE_MINUTE": 60,
    "FIVE_MINUTE": 300,
    "FIFTEEN_MINUTE": 900,
    "ONE_HOUR": 3600,
    "SIX_HOUR": 21600,
    "ONE_DAY": 86400,
}


def granularity_seconds(name: str) -> int:
    """Return the candle length in seconds for a granularity name."""
    try:
        return GRANULARITY_SECONDS[name]
    except KeyError:
        valid = ", ".join(GRANULARITY_SECONDS)
        raise ValueError(f"Unknown granularity {name!r}; expected one of: {valid}") from None
