import type { BacktestRunSummary } from "./api";

export type PeriodAggregate = {
  period_name: string;
  trade_count: number;
  win_rate_pct: number;
  starting_cash_usd: number;
  ending_equity_usd: number;
  total_return_pct: number;
  market_return_pct: number;
};

// Combine all per-coin runs within each period into one row per period.
export function aggregateRunsByPeriod(runs: BacktestRunSummary[]): PeriodAggregate[] {
  const order: string[] = [];
  const byPeriod = new Map<string, BacktestRunSummary[]>();
  for (const run of runs) {
    if (!byPeriod.has(run.period_name)) {
      byPeriod.set(run.period_name, []);
      order.push(run.period_name);
    }
    byPeriod.get(run.period_name)!.push(run);
  }

  return order.map((period) => {
    const periodRuns = byPeriod.get(period)!;
    const tradeCount = periodRuns.reduce((sum, run) => sum + run.trade_count, 0);
    const weightedWins = periodRuns.reduce((sum, run) => sum + run.win_rate_pct * run.trade_count, 0);
    const startingCash = periodRuns.reduce((sum, run) => sum + run.starting_cash_usd, 0);
    const endingEquity = periodRuns.reduce((sum, run) => sum + run.ending_equity_usd, 0);
    const marketReturn =
      periodRuns.reduce((sum, run) => sum + run.market_return_pct, 0) / periodRuns.length;

    return {
      period_name: period,
      trade_count: tradeCount,
      win_rate_pct: tradeCount ? weightedWins / tradeCount : 0,
      starting_cash_usd: startingCash,
      ending_equity_usd: endingEquity,
      total_return_pct: startingCash ? ((endingEquity - startingCash) / startingCash) * 100 : 0,
      market_return_pct: marketReturn,
    };
  });
}
