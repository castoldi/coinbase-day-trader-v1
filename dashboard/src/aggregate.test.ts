import { describe, expect, it } from "vitest";
import { aggregateRunsByPeriod } from "./aggregate";
import type { BacktestRunSummary } from "./api";

function run(overrides: Partial<BacktestRunSummary>): BacktestRunSummary {
  return {
    id: 1,
    strategy_name: "s",
    strategy_version: "1.0.0",
    period_name: "2024",
    product_id: "BTC-USD",
    product_ids: ["BTC-USD"],
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    starting_cash_usd: 1000,
    ending_equity_usd: 1000,
    total_return_pct: 0,
    max_drawdown_pct: 0,
    win_rate_pct: 0,
    trade_count: 0,
    market_return_pct: 0,
    notes: "",
    created_at: null,
    ...overrides,
  };
}

describe("aggregateRunsByPeriod", () => {
  it("combines all coins within a period", () => {
    const runs = [
      run({ product_id: "BTC-USD", trade_count: 12, win_rate_pct: 50, ending_equity_usd: 1100, market_return_pct: 12.5 }),
      run({ product_id: "ETH-USD", trade_count: 8, win_rate_pct: 25, ending_equity_usd: 900, market_return_pct: 7.5 }),
    ];
    const agg = aggregateRunsByPeriod(runs);
    expect(agg).toHaveLength(1);
    expect(agg[0].period_name).toBe("2024");
    expect(agg[0].trade_count).toBe(20);
    expect(agg[0].starting_cash_usd).toBe(2000);
    expect(agg[0].ending_equity_usd).toBe(2000);
    expect(agg[0].total_return_pct).toBeCloseTo(0);
    // trade-weighted win rate: (50*12 + 25*8) / 20 = 40
    expect(agg[0].win_rate_pct).toBeCloseTo(40);
    // equal-weight Buy & Hold across coins: (12.5 + 7.5) / 2 = 10
    expect(agg[0].market_return_pct).toBeCloseTo(10);
  });

  it("keeps periods in first-seen order and handles zero trades", () => {
    const runs = [
      run({ period_name: "2024", product_id: "BTC-USD", trade_count: 0, ending_equity_usd: 1000 }),
      run({ period_name: "2025", product_id: "BTC-USD", trade_count: 2, win_rate_pct: 100, ending_equity_usd: 1200 }),
      run({ period_name: "2024", product_id: "ETH-USD", trade_count: 0, ending_equity_usd: 1000 }),
    ];
    const agg = aggregateRunsByPeriod(runs);
    expect(agg.map((a) => a.period_name)).toEqual(["2024", "2025"]);
    expect(agg[0].win_rate_pct).toBe(0); // no trades -> no division by zero
    expect(agg[1].total_return_pct).toBeCloseTo(20);
  });
});
