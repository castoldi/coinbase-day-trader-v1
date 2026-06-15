import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.backtests.granularity import granularity_seconds
from trader_app.backtests.periods import BacktestPeriod, standard_periods
from trader_app.config import Settings
from trader_app.models import BacktestRun
from trader_app.strategies.base import Candle
from trader_app.strategies.registry import load_strategies


@dataclass(frozen=True)
class CandlePoint:
    start: datetime
    low: float
    high: float
    open: float
    close: float
    volume: float


class BacktestService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        settings: Settings,
        candle_loader: Callable[[str, date, date], list[CandlePoint]] | None = None,
        strategies: list | None = None,
        granularity: str | None = None,
        granularities: list[str] | None = None,
        fee_rate: float | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        # The sweep compares one or more granularities. An explicit single
        # `granularity` (used by focused tests and the live loader) takes
        # precedence; otherwise fall back to the configured comma-separated set.
        if granularities is not None:
            grans = list(granularities)
        elif granularity is not None:
            grans = [granularity]
        else:
            grans = [g.strip() for g in settings.backtest_granularities.split(",") if g.strip()]
        for name in grans:
            granularity_seconds(name)  # validate up front
        self.granularities = grans
        self.granularity = granularity or grans[0]
        self.fee_rate = settings.backtest_fee_rate if fee_rate is None else fee_rate
        self._custom_loader = candle_loader
        self.strategies = strategies
        self.market_dir = Path("data/market")
        self.market_dir.mkdir(parents=True, exist_ok=True)

    def run_standard_backtests(self, today: date | None = None) -> list[BacktestRun]:
        runs: list[BacktestRun] = []
        strategies = self.strategies or load_strategies(self.settings.default_strategies)
        products = self.settings.products

        with self.session_factory() as session:
            # Each invocation regenerates the full standard sweep, so clear the
            # previous sweep first (including runs from retired strategies).
            session.execute(delete(BacktestRun))
            for granularity in self.granularities:
                for period in standard_periods(granularity, today):
                    for strategy in strategies:
                        for product_id in products:
                            run = self._build_run(strategy, period, product_id, granularity)
                            session.add(run)
                            session.flush()
                            runs.append(run)
            session.commit()

        return runs

    def get_backtests_summary(self) -> dict[str, object]:
        with self.session_factory() as session:
            runs = session.scalars(
                select(BacktestRun).order_by(
                    BacktestRun.granularity.asc(),
                    BacktestRun.start_date.asc(),
                    BacktestRun.period_name.asc(),
                    BacktestRun.product_id.asc(),
                )
            ).all()

        return {
            "total_runs": len(runs),
            "periods": [run.period_name for run in runs],
            "runs": [self._run_to_dict(run) for run in runs],
        }

    def _build_run(
        self,
        strategy,
        period: BacktestPeriod,
        product_id: str,
        granularity: str,
    ) -> BacktestRun:
        candles = self._load_points(product_id, period.start, period.end, granularity)
        if len(candles) >= 2 and candles[0].close:
            market_return_pct = ((candles[-1].close - candles[0].close) / candles[0].close) * 100
        else:
            market_return_pct = 0.0

        result = self._simulate(strategy, period, [product_id], {product_id: candles})

        if result["trade_count"] == 0:
            notes = f"No qualifying setups for {product_id} in this period; account stayed flat."
        else:
            notes = (
                f"{product_id}: executed {result['trade_count']} trade(s) with a "
                f"{result['win_rate_pct']:.1f}% win rate."
            )

        return BacktestRun(
            strategy_name=strategy.name,
            strategy_version=strategy.version,
            granularity=granularity,
            period_name=period.name,
            product_id=product_id,
            product_ids=product_id,
            start_date=period.start.isoformat(),
            end_date=period.end.isoformat(),
            starting_cash_usd=period.starting_cash_usd,
            ending_equity_usd=round(result["ending_equity_usd"], 2),
            total_return_pct=round(result["total_return_pct"], 4),
            max_drawdown_pct=round(result["max_drawdown_pct"], 4),
            win_rate_pct=round(result["win_rate_pct"], 2),
            trade_count=result["trade_count"],
            market_return_pct=round(market_return_pct, 4),
            notes=notes,
        )

    def _simulate(
        self,
        strategy,
        period: BacktestPeriod,
        products: list[str],
        series: dict[str, list[CandlePoint]],
    ) -> dict[str, float]:
        starting = period.starting_cash_usd
        cash = starting
        peak = starting
        max_drawdown = 0.0
        wins = 0
        trade_count = 0
        fee = self.fee_rate
        positions: dict[str, dict[str, float]] = {}
        last_close: dict[str, float] = {}
        allocation = starting / len(products) if products else starting

        strategy_candles = {
            product_id: self._to_strategy_candles(product_id, points)
            for product_id, points in series.items()
        }
        # Iterate every candle in chronological order (works for daily or
        # intraday granularities). Each product's bar is located by its exact
        # start timestamp so multiple bars per calendar day are all processed.
        index_by_ts = {
            product_id: {point.start: index for index, point in enumerate(points)}
            for product_id, points in series.items()
        }
        timeline = sorted({point.start for points in series.values() for point in points})

        for timestamp in timeline:
            for product_id in products:
                index = index_by_ts.get(product_id, {}).get(timestamp)
                if index is None:
                    continue
                today = series[product_id][index]
                last_close[product_id] = today.close

                position = positions.get(product_id)
                if position is not None:
                    stop = position["stop"]
                    take = position["take"]
                    exit_price = None
                    if stop is not None and today.low <= stop:
                        exit_price = stop
                    elif take is not None and today.high >= take:
                        exit_price = take
                    else:
                        exit_price = self._strategy_exit(
                            strategy, strategy_candles[product_id][: index + 1], position["entry"]
                        )
                    if exit_price is not None:
                        proceeds = position["quantity"] * exit_price * (1 - fee)
                        pnl = proceeds - position["cost"]
                        cash += proceeds
                        trade_count += 1
                        if pnl > 0:
                            wins += 1
                        del positions[product_id]
                        position = None

                if position is None:
                    signal = strategy.generate_signal(strategy_candles[product_id][: index + 1])
                    if signal.action == "buy" and signal.take_profit is not None and today.close > 0:
                        spend = min(allocation, cash)
                        if spend > 0:
                            # Size so the entry fee fits inside the spend budget;
                            # cost is the total cash outlay (notional + entry fee).
                            quantity = spend / (today.close * (1 + fee))
                            cost = quantity * today.close * (1 + fee)
                            positions[product_id] = {
                                "quantity": quantity,
                                "cost": cost,
                                "entry": today.close,
                                "stop": signal.stop_loss,
                                "take": signal.take_profit,
                            }
                            cash -= cost

            equity = cash + sum(
                position["quantity"] * last_close.get(product_id, 0.0)
                for product_id, position in positions.items()
            )
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - equity) / peak * 100)

        for product_id, position in list(positions.items()):
            exit_price = last_close.get(product_id, position["entry"])
            proceeds = position["quantity"] * exit_price * (1 - fee)
            pnl = proceeds - position["cost"]
            cash += proceeds
            trade_count += 1
            if pnl > 0:
                wins += 1
            del positions[product_id]

        ending_equity = cash
        return {
            "ending_equity_usd": ending_equity,
            "total_return_pct": (ending_equity - starting) / starting * 100 if starting else 0.0,
            "max_drawdown_pct": max_drawdown,
            "win_rate_pct": (wins / trade_count * 100) if trade_count else 0.0,
            "trade_count": trade_count,
        }

    @staticmethod
    def _strategy_exit(strategy, candles: list[Candle], entry_price: float) -> float | None:
        exit_signal = getattr(strategy, "exit_signal", None)
        if exit_signal is None:
            return None
        return exit_signal(candles, entry_price)

    def load_strategy_candles(self, product_id: str, start_date: date, end_date: date) -> list[Candle]:
        points = self._load_points(product_id, start_date, end_date, self.granularity)
        return self._to_strategy_candles(product_id, points)

    def _load_points(
        self, product_id: str, start_date: date, end_date: date, granularity: str
    ) -> list[CandlePoint]:
        """Load candle points, using an injected loader if present (tests) or
        the Coinbase loader for the given granularity."""
        if self._custom_loader is not None:
            return self._custom_loader(product_id, start_date, end_date)
        return self._load_coinbase_candles(product_id, start_date, end_date, granularity)

    def _to_strategy_candles(self, product_id: str, points: list[CandlePoint]) -> list[Candle]:
        return [
            Candle(
                product_id=product_id,
                timestamp=point.start.isoformat(),
                open=point.open,
                high=point.high,
                low=point.low,
                close=point.close,
                volume=point.volume,
            )
            for point in points
        ]

    def _load_coinbase_candles(
        self, product_id: str, start_date: date, end_date: date, granularity: str
    ) -> list[CandlePoint]:
        cache_path = self.market_dir / f"{product_id}-{granularity}.json"
        cached = self._read_cache(cache_path)
        # Daily candles are cheap, so keep a wide rolling cache; intraday windows
        # would be enormous, so only cache the requested span.
        cache_start = date(2024, 1, 1) if granularity == "ONE_DAY" else start_date
        cache_end = max(end_date, date.today())
        if not cached or self._cache_last_date(cached) < cache_end:
            fetched = self._fetch_coinbase_candles(product_id, cache_start, cache_end, granularity)
            merged = {point.start.isoformat(): point for point in [*cached, *fetched]}
            candles = sorted(merged.values(), key=lambda point: point.start)
            self._write_cache(cache_path, candles, granularity)
        else:
            candles = cached

        return [point for point in candles if start_date <= point.start.date() <= end_date]

    def _fetch_coinbase_candles(
        self, product_id: str, start_date: date, end_date: date, granularity: str
    ) -> list[CandlePoint]:
        gran = granularity_seconds(granularity)
        # The Coinbase candles endpoint returns at most 300 candles per request.
        chunk = timedelta(seconds=gran * 300)
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        candles: list[CandlePoint] = []
        chunk_start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        with httpx.Client(base_url="https://api.exchange.coinbase.com", timeout=20) as client:
            while chunk_start < end_dt:
                chunk_end = min(chunk_start + chunk, end_dt)
                response = client.get(
                    f"/products/{product_id}/candles",
                    params={
                        "granularity": gran,
                        "start": chunk_start.isoformat(),
                        "end": chunk_end.isoformat(),
                    },
                )
                response.raise_for_status()
                payload = response.json()
                for item in payload:
                    candles.append(
                        CandlePoint(
                            start=datetime.fromtimestamp(item[0], tz=timezone.utc),
                            low=float(item[1]),
                            high=float(item[2]),
                            open=float(item[3]),
                            close=float(item[4]),
                            volume=float(item[5]),
                        )
                    )
                chunk_start = chunk_end

        deduped = {point.start.isoformat(): point for point in candles}
        return sorted(deduped.values(), key=lambda point: point.start)

    def _read_cache(self, cache_path: Path) -> list[CandlePoint]:
        if not cache_path.exists():
            return []
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        return [
            CandlePoint(
                start=datetime.fromisoformat(item["start"]),
                low=float(item["low"]),
                high=float(item["high"]),
                open=float(item["open"]),
                close=float(item["close"]),
                volume=float(item["volume"]),
            )
            for item in payload.get("candles", [])
        ]

    def _write_cache(self, cache_path: Path, candles: list[CandlePoint], granularity: str) -> None:
        payload = {
            "product_id": cache_path.stem.replace(f"-{granularity}", ""),
            "granularity": granularity,
            "candles": [
                {
                    "start": point.start.isoformat(),
                    "low": point.low,
                    "high": point.high,
                    "open": point.open,
                    "close": point.close,
                    "volume": point.volume,
                }
                for point in candles
            ],
        }
        cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _cache_last_date(self, candles: list[CandlePoint]) -> date:
        return candles[-1].start.date() if candles else date(1970, 1, 1)

    def _run_to_dict(self, run: BacktestRun) -> dict[str, object]:
        return {
            "id": run.id,
            "strategy_name": run.strategy_name,
            "strategy_version": run.strategy_version,
            "granularity": run.granularity,
            "period_name": run.period_name,
            "product_id": run.product_id,
            "product_ids": run.product_ids.split(","),
            "start_date": run.start_date,
            "end_date": run.end_date,
            "starting_cash_usd": run.starting_cash_usd,
            "ending_equity_usd": run.ending_equity_usd,
            "total_return_pct": run.total_return_pct,
            "max_drawdown_pct": run.max_drawdown_pct,
            "win_rate_pct": run.win_rate_pct,
            "trade_count": run.trade_count,
            "market_return_pct": run.market_return_pct,
            "notes": run.notes,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
