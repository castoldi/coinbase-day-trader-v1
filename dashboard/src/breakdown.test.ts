import { describe, expect, it } from "vitest";
import { buildCoinBreakdown } from "./breakdown";
import type { BacktestRunSummary } from "./api";

function run(overrides: Partial<BacktestRunSummary>): BacktestRunSummary {
  return {
    id: 1,
    strategy_name: "s",
    strategy_version: "1.0.0",
    granularity: "ONE_DAY",
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
  it("pivots runs into coin -> granularity -> period x strategy", () => {
    const runs = [
      run({ product_id: "BTC-USD", strategy_name: "ema", period_name: "2024", total_return_pct: 9, trade_count: 5, market_return_pct: 111 }),
      run({ product_id: "BTC-USD", strategy_name: "stoch", period_name: "2024", total_return_pct: 11, trade_count: 8, market_return_pct: 111 }),
      run({ product_id: "ETH-USD", strategy_name: "ema", period_name: "2024", total_return_pct: -3, trade_count: 2, market_return_pct: 41 }),
      run({ product_id: "ETH-USD", strategy_name: "stoch", period_name: "2024", total_return_pct: 2, trade_count: 5, market_return_pct: 41 }),
    ];
    const breakdown = buildCoinBreakdown(runs);

    expect(breakdown.strategies.map((s) => s.name)).toEqual(["ema", "stoch"]);
    expect(breakdown.granularities).toEqual(["ONE_DAY"]);
    expect(breakdown.coins.map((c) => c.product_id)).toEqual(["BTC-USD", "ETH-USD"]);

    const btcDaily = breakdown.coins[0].granularities[0];
    expect(btcDaily.granularity).toBe("ONE_DAY");
    const row2024 = btcDaily.rows[0];
    expect(row2024.period).toBe("2024");
    expect(row2024.market_return_pct).toBe(111); // per coin/period, strategy-independent
    expect(row2024.cells[breakdown.strategies[0].key]?.total_return_pct).toBe(9);
    expect(row2024.cells[breakdown.strategies[1].key]?.total_return_pct).toBe(11);

    const ethDaily = breakdown.coins[1].granularities[0];
    expect(ethDaily.rows[0].market_return_pct).toBe(41);
    expect(ethDaily.rows[0].cells[breakdown.strategies[0].key]?.total_return_pct).toBe(-3);
  });

  it("groups each coin's runs by granularity with its own period list", () => {
    const runs = [
      run({ granularity: "ONE_DAY", period_name: "2024", strategy_name: "ema", total_return_pct: 5 }),
      run({ granularity: "ONE_HOUR", period_name: "last_30_days", strategy_name: "ema", total_return_pct: 1 }),
      run({ granularity: "ONE_HOUR", period_name: "last_7_days", strategy_name: "ema", total_return_pct: 2 }),
    ];
    const breakdown = buildCoinBreakdown(runs);

    expect(breakdown.granularities).toEqual(["ONE_DAY", "ONE_HOUR"]);
    const btc = breakdown.coins[0];
    expect(btc.granularities.map((g) => g.granularity)).toEqual(["ONE_DAY", "ONE_HOUR"]);
    expect(btc.granularities[0].periods).toEqual(["2024"]);
    expect(btc.granularities[1].periods).toEqual(["last_30_days", "last_7_days"]);

    const emaKey = breakdown.strategies[0].key;
    expect(btc.granularities[1].rows[1].cells[emaKey]?.total_return_pct).toBe(2);
  });

  it("leaves a missing strategy/period cell undefined", () => {
    const runs = [
      run({ product_id: "BTC-USD", strategy_name: "ema", period_name: "2024" }),
      run({ product_id: "BTC-USD", strategy_name: "stoch", period_name: "2025" }),
    ];
    const breakdown = buildCoinBreakdown(runs);
    const daily = breakdown.coins[0].granularities[0];
    expect(daily.periods).toEqual(["2024", "2025"]);
    const emaKey = breakdown.strategies.find((s) => s.name === "ema")!.key;
    // ema has no 2025 run
    const row2025 = daily.rows.find((r) => r.period === "2025")!;
    expect(row2025.cells[emaKey]).toBeUndefined();
  });
});
