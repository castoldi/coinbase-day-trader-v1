from trader_app.strategies.registry import available_strategies, load_strategies


def test_load_single_strategy():
    strategies = load_strategies("ema_ribbon_reversal")
    assert [strategy.name for strategy in strategies] == ["ema_ribbon_reversal"]


def test_load_all_strategies():
    strategies = load_strategies("ALL")
    assert [strategy.name for strategy in strategies] == list(available_strategies().keys())


def test_default_strategy_is_active_not_gated():
    strategy = load_strategies("ema_ribbon_reversal")[0]
    assert strategy.version == "1.0.0"
    assert strategy.requires_transcript_review is False
