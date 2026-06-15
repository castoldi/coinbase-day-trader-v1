from trader_app.strategies.base import Strategy
from trader_app.strategies.price_action_transcript import PriceActionTranscriptStrategy


def available_strategies() -> dict[str, type[Strategy]]:
    return {
        "price_action_transcript": PriceActionTranscriptStrategy,
    }


def load_strategies(selection: str) -> list[Strategy]:
    registry = available_strategies()
    names = (
        list(registry.keys())
        if selection.strip().upper() == "ALL"
        else [item.strip() for item in selection.split(",") if item.strip()]
    )
    unknown = [name for name in names if name not in registry]
    if unknown:
        raise ValueError(f"Unknown strategies: {', '.join(unknown)}")
    return [registry[name]() for name in names]
