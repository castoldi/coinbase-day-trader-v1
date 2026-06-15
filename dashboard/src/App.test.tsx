import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.location.hash = "";
});

const openTrade = {
  id: 1,
  product_id: "BTC-USD",
  strategy: "ema_ribbon_reversal",
  status: "open",
  quantity: 0.01,
  entry_price_usd: 50000,
  entry_value_usd: 500,
  stop_loss_usd: 49000,
  take_profit_usd: 52000,
  exit_price_usd: null,
  realized_pnl_usd: 0,
  opened_at: "2026-06-10T12:00:00+00:00",
  closed_at: null,
};

const closedTrade = {
  ...openTrade,
  id: 2,
  status: "closed",
  exit_price_usd: 52000,
  realized_pnl_usd: 20,
  closed_at: "2026-06-11T12:00:00+00:00",
};

function summaryPayload() {
  return {
    account: {
      initial_cash_usd: 1000,
      cash_usd: 520,
      equity_usd: 1020,
      realized_pnl_usd: 20,
      trading_enabled: true,
      safety_lock_reason: "",
    },
    bot: { status: "healthy", strategies: ["ema_ribbon_reversal"] },
    metrics: { win_rate_pct: 100, closed_count: 1, open_count: 1 },
    prices: [
      { product_id: "BTC-USD", price_usd: 65000 },
      { product_id: "ETH-USD", price_usd: 3500 },
    ],
    trades: { open: [openTrade], closed: [closedTrade] },
  };
}

function strategyEntry(name: string, title: string) {
  return {
    name,
    version: "1.0.0",
    title,
    summary: `${title} summary.`,
    rules: {
      indicators: ["Indicator line."],
      entry: "Entry rule.",
      stop_loss: "Stop rule.",
      take_profit: "Target rule.",
      risk: "Risk rule.",
    },
    examples: [
      {
        label: "Long setup",
        side: "long",
        candles: [
          { open: 101, high: 108, low: 101, close: 105 },
          { open: 105, high: 112, low: 104, close: 111 },
        ],
        entry: 105,
        stop_loss: 100,
        take_profit: 115,
        entry_index: 0,
      },
      {
        label: "Second setup",
        side: "long",
        candles: [
          { open: 99, high: 99, low: 92, close: 95 },
          { open: 95, high: 96, low: 88, close: 89 },
        ],
        entry: 95,
        stop_loss: 90,
        take_profit: 105,
        entry_index: 0,
      },
    ],
  };
}

function strategiesPayload() {
  return {
    strategies: [
      strategyEntry("ema_ribbon_reversal", "EMA Ribbon Reversal"),
      strategyEntry("stochastic_swing", "Fast Stochastic Swing"),
    ],
  };
}

function backtestsPayload() {
  const base = {
    granularity: "ONE_DAY",
    period_name: "2024",
    product_ids: ["BTC-USD", "ETH-USD", "SOL-USD"],
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    starting_cash_usd: 1000,
    ending_equity_usd: 1100,
    total_return_pct: 10,
    max_drawdown_pct: 5,
    win_rate_pct: 60,
    trade_count: 5,
    market_return_pct: 12.5,
    notes: "Executed 5 trade(s) with a 60.0% win rate.",
    created_at: "2026-06-14T20:00:00+00:00",
  };
  return {
    total_runs: 4,
    periods: ["2024", "2024", "2024", "2024"],
    runs: [
      { ...base, id: 1, strategy_name: "ema_ribbon_reversal", strategy_version: "1.0.0", product_id: "BTC-USD", total_return_pct: 9, trade_count: 12, market_return_pct: 111, notes: "EMA executed 12 trades." },
      { ...base, id: 2, strategy_name: "stochastic_swing", strategy_version: "1.0.0", product_id: "BTC-USD", total_return_pct: 11, trade_count: 8, market_return_pct: 111, notes: "Stochastic executed 21 trades." },
      { ...base, id: 3, strategy_name: "ema_ribbon_reversal", strategy_version: "1.0.0", product_id: "ETH-USD", total_return_pct: -3, trade_count: 2, market_return_pct: 41, notes: "EMA executed 12 trades." },
      { ...base, id: 4, strategy_name: "stochastic_swing", strategy_version: "1.0.0", product_id: "ETH-USD", total_return_pct: 2, trade_count: 5, market_return_pct: 41, notes: "Stochastic executed 21 trades." },
    ],
  };
}

function mockFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string) => {
      const routes: Record<string, unknown> = {
        "/api/dashboard/summary": summaryPayload(),
        "/api/backtests/summary": backtestsPayload(),
        "/api/strategies": strategiesPayload(),
      };
      if (input in routes) {
        return Promise.resolve({ ok: true, json: async () => routes[input] });
      }
      return Promise.reject(new Error(`Unexpected fetch: ${input}`));
    }),
  );
}

describe("App", () => {
  it("renders the live trading dashboard shell", () => {
    mockFetch();
    render(<App />);
    expect(screen.getByRole("heading", { name: "Live Trading" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Trading History" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Account Management" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Backtests" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Strategies" })).toBeTruthy();
  });

  it("shows a build version indicator", () => {
    mockFetch();
    render(<App />);
    expect(screen.getByText(/^Build /)).toBeTruthy();
  });

  it("restores the active page from the URL hash on load", () => {
    window.location.hash = "#backtests";
    mockFetch();
    render(<App />);
    expect(screen.getByRole("heading", { name: "Backtests" })).toBeTruthy();
  });

  it("updates the URL hash when navigating so a refresh stays put", () => {
    mockFetch();
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Strategies" }));
    expect(window.location.hash).toBe("#strategies");
  });

  it("shows live prices and open trades", async () => {
    mockFetch();
    render(<App />);
    await waitFor(() => expect(screen.getAllByText("BTC-USD").length).toBeGreaterThan(0));
    expect(screen.getByText("$65,000.00")).toBeTruthy();
  });

  it("changes pages when dashboard menu buttons are clicked", () => {
    mockFetch();
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Account Management" }));
    expect(screen.getByRole("heading", { name: "Account Management" })).toBeTruthy();
    expect(screen.getByText("Safety lock")).toBeTruthy();
  });

  it("refetches backtests when navigating to the Backtests tab", async () => {
    mockFetch();
    render(<App />);
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    const callsTo = (url: string) =>
      fetchMock.mock.calls.filter((call) => call[0] === url).length;
    await waitFor(() => expect(callsTo("/api/backtests/summary")).toBeGreaterThan(0));
    const before = callsTo("/api/backtests/summary");
    fireEvent.click(screen.getByRole("button", { name: "Backtests" }));
    await waitFor(() => expect(callsTo("/api/backtests/summary")).toBeGreaterThan(before));
  });

  it("breaks down backtests per coin with strategies as columns", async () => {
    mockFetch();
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Backtests" }));
    expect(screen.getByRole("heading", { name: "Backtests" })).toBeTruthy();
    // one section per coin
    await waitFor(() => expect(screen.getByRole("heading", { name: "BTC-USD" })).toBeTruthy());
    expect(screen.getByRole("heading", { name: "ETH-USD" })).toBeTruthy();
    // strategies appear as column headers (once per coin section)
    expect(screen.getAllByText("ema_ribbon_reversal").length).toBe(2);
    expect(screen.getAllByText("stochastic_swing").length).toBe(2);
    // per coin/period/strategy return is shown
    expect(screen.getByText("9.00%")).toBeTruthy(); // ema on BTC
    expect(screen.getByText("11.00%")).toBeTruthy(); // stochastic on BTC
  });

  it("describes each strategy with its own chart examples and backtest note", async () => {
    mockFetch();
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Strategies" }));
    await waitFor(() => expect(screen.getByText("EMA Ribbon Reversal")).toBeTruthy());
    expect(screen.getByText("Fast Stochastic Swing")).toBeTruthy();
    // each card shows ITS OWN latest backtest note, not a shared/global one
    expect(screen.getByText(/EMA executed 12 trades\./)).toBeTruthy();
    expect(screen.getByText(/Stochastic executed 21 trades\./)).toBeTruthy();
  });
});
