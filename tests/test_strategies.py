from trader_app.strategies.registry import available_strategies, load_strategies


def test_load_single_strategy():
    strategies = load_strategies("price_action_transcript")
    assert [strategy.name for strategy in strategies] == ["price_action_transcript"]


def test_load_all_strategies():
    strategies = load_strategies("ALL")
    assert [strategy.name for strategy in strategies] == list(available_strategies().keys())


def test_price_action_strategy_is_transcript_gated():
    strategy = load_strategies("price_action_transcript")[0]
    assert strategy.version == "0.1.0"
    assert strategy.requires_transcript_review is True
    assert strategy.generate_signal([]).action == "hold"
