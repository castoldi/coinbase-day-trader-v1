import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

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
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.candle_loader = candle_loader or self._load_coinbase_daily_candles
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
            for period in standard_periods(today):
                for strategy in strategies:
                    run = self._build_run(strategy, period, products)
                    session.add(run)
                    session.flush()
                    runs.append(run)
            session.commit()

        return runs

    def get_backtests_summary(self) -> dict[str, object]:
        with self.session_factory() as session:
            runs = session.scalars(
                select(BacktestRun).order_by(BacktestRun.start_date.asc(), BacktestRun.period_name.asc())
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
        products: list[str],
    ) -> BacktestRun:
        series: dict[str, list[CandlePoint]] = {}
        market_returns: list[float] = []
        for product_id in products:
            candles = self.candle_loader(product_id, period.start, period.end)
            series[product_id] = candles
            if len(candles) >= 2 and candles[0].close:
                market_returns.append(((candles[-1].close - candles[0].close) / candles[0].close) * 100)

        market_return_pct = sum(market_returns) / len(market_returns) if market_returns else 0.0
        result = self._simulate(strategy, period, products, series)

        if result["trade_count"] == 0:
            notes = "No qualifying reversal setups in this period; account stayed flat."
        else:
            notes = (
                f"Executed {result['trade_count']} trade(s) with a "
                f"{result['win_rate_pct']:.1f}% win rate."
            )

        return BacktestRun(
            strategy_name=strategy.name,
            strategy_version=strategy.version,
            period_name=period.name,
            product_ids=",".join(products),
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
        positions: dict[str, dict[str, float]] = {}
        last_close: dict[str, float] = {}
        allocation = starting / len(products) if products else starting

        strategy_candles = {
            product_id: self._to_strategy_candles(product_id, points)
            for product_id, points in series.items()
        }
        all_dates = sorted({point.start.date() for points in series.values() for point in points})

        for current_date in all_dates:
            for product_id in products:
                points = series[product_id]
                upto = [index for index, point in enumerate(points) if point.start.date() <= current_date]
                if not upto:
                    continue
                last_index = upto[-1]
                today = points[last_index]
                if today.start.date() != current_date:
                    continue
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
                            strategy, strategy_candles[product_id][: last_index + 1], position["entry"]
                        )
                    if exit_price is not None:
                        proceeds = position["quantity"] * exit_price
                        pnl = proceeds - position["cost"]
                        cash += proceeds
                        trade_count += 1
                        if pnl > 0:
                            wins += 1
                        del positions[product_id]
                        position = None

                if position is None:
                    signal = strategy.generate_signal(strategy_candles[product_id][: last_index + 1])
                    if signal.action == "buy" and signal.take_profit is not None and today.close > 0:
                        spend = min(allocation, cash)
                        if spend > 0:
                            quantity = spend / today.close
                            positions[product_id] = {
                                "quantity": quantity,
                                "cost": quantity * today.close,
                                "entry": today.close,
                                "stop": signal.stop_loss,
                                "take": signal.take_profit,
                            }
                            cash -= quantity * today.close

            equity = cash + sum(
                position["quantity"] * last_close.get(product_id, 0.0)
                for product_id, position in positions.items()
            )
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - equity) / peak * 100)

        for product_id, position in list(positions.items()):
            exit_price = last_close.get(product_id, position["cost"] / position["quantity"])
            proceeds = position["quantity"] * exit_price
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
        return self._to_strategy_candles(product_id, self.candle_loader(product_id, start_date, end_date))

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

    def _load_coinbase_daily_candles(self, product_id: str, start_date: date, end_date: date) -> list[CandlePoint]:
        cache_path = self.market_dir / f"{product_id}-ONE_DAY.json"
        cached = self._read_cache(cache_path)
        cache_start = date(2024, 1, 1)
        cache_end = max(end_date, date.today())
        if not cached or self._cache_last_date(cached) < cache_end:
            fetched = self._fetch_coinbase_daily_candles(product_id, cache_start, cache_end)
            merged = {point.start.isoformat(): point for point in [*cached, *fetched]}
            candles = sorted(merged.values(), key=lambda point: point.start)
            self._write_cache(cache_path, candles)
        else:
            candles = cached

        return [point for point in candles if start_date <= point.start.date() <= end_date]

    def _fetch_coinbase_daily_candles(self, product_id: str, start_date: date, end_date: date) -> list[CandlePoint]:
        candles: list[CandlePoint] = []
        chunk_start = start_date
        with httpx.Client(base_url="https://api.exchange.coinbase.com", timeout=20) as client:
            while chunk_start <= end_date:
                chunk_end = min(chunk_start + timedelta(days=299), end_date)
                response = client.get(
                    f"/products/{product_id}/candles",
                    params={
                        "granularity": 86400,
                        "start": datetime.combine(chunk_start, time.min, tzinfo=timezone.utc).isoformat(),
                        "end": datetime.combine(chunk_end + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat(),
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
                chunk_start = chunk_end + timedelta(days=1)

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

    def _write_cache(self, cache_path: Path, candles: list[CandlePoint]) -> None:
        payload = {
            "product_id": cache_path.stem.replace("-ONE_DAY", ""),
            "granularity": "ONE_DAY",
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
            "period_name": run.period_name,
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
