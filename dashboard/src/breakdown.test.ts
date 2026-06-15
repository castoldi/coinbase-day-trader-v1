import { describe, expect, it } from "vitest";
import { buildCoinBreakdown } from "./breakdown";
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

describe("buildCoinBreakdown", () => {
  it("pivots runs into coin -> period x strategy", () => {
    const runs = [
      run({ product_id: "BTC-USD", strategy_name: "ema", period_name: "2024", total_return_pct: 9, trade_count: 5, market_return_pct: 111 }),
      run({ product_id: "BTC-USD", strategy_name: "stoch", period_name: "2024", total_return_pct: 11, trade_count: 8, market_return_pct: 111 }),
      run({ product_id: "ETH-USD", strategy_name: "ema", period_name: "2024", total_return_pct: -3, trade_count: 2, market_return_pct: 41 }),
      run({ product_id: "ETH-USD", strategy_name: "stoch", period_name: "2024", total_return_pct: 2, trade_count: 5, market_return_pct: 41 }),
    ];
    const breakdown = buildCoinBreakdown(runs);

    expect(breakdown.strategies.map((s) => s.name)).toEqual(["ema", "stoch"]);
    expect(breakdown.periods).toEqual(["2024"]);
    expect(breakdown.coins.map((c) => c.product_id)).toEqual(["BTC-USD", "ETH-USD"]);

    const btc = breakdown.coins[0];
    const row2024 = btc.rows[0];
    expect(row2024.period).toBe("2024");
    expect(row2024.market_return_pct).toBe(111); // per coin/period, strategy-independent
    expect(row2024.cells[breakdown.strategies[0].key]?.total_return_pct).toBe(9);
    expect(row2024.cells[breakdown.strategies[1].key]?.total_return_pct).toBe(11);

    const eth = breakdown.coins[1];
    expect(eth.rows[0].market_return_pct).toBe(41);
    expect(eth.rows[0].cells[breakdown.strategies[0].key]?.total_return_pct).toBe(-3);
  });

  it("leaves a missing strategy/period cell undefined", () => {
    const runs = [
      run({ product_id: "BTC-USD", strategy_name: "ema", period_name: "2024" }),
      run({ product_id: "BTC-USD", strategy_name: "stoch", period_name: "2025" }),
    ];
    const breakdown = buildCoinBreakdown(runs);
    expect(breakdown.periods).toEqual(["2024", "2025"]);
    const btc = breakdown.coins[0];
    const emaKey = breakdown.strategies.find((s) => s.name === "ema")!.key;
    // ema has no 2025 run
    const row2025 = btc.rows.find((r) => r.period === "2025")!;
    expect(row2025.cells[emaKey]).toBeUndefined();
  });
});
