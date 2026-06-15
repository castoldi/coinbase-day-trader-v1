from trader_app.strategies.base import Candle, Signal


class PriceActionTranscriptStrategy:
    name = "price_action_transcript"
    version = "0.1.0"
    requires_transcript_review = True

    def generate_signal(self, candles: list[Candle]) -> Signal:
        return Signal(
            action="hold",
            confidence=0,
            reason="Strategy rules require transcript review before signals are enabled.",
        )
