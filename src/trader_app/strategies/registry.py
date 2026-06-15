from trader_app.strategies.base import Strategy
from trader_app.strategies.ema_ribbon_reversal import EmaRibbonReversalStrategy
from trader_app.strategies.stochastic_swing import StochasticSwingStrategy
from trader_app.strategies.triple_screen_trend import TripleScreenTrendStrategy


def available_strategies() -> dict[str, type[Strategy]]:
    return {
        "ema_ribbon_reversal": EmaRibbonReversalStrategy,
        "stochastic_swing": StochasticSwingStrategy,
        "triple_screen_trend": TripleScreenTrendStrategy,
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
