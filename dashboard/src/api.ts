export type Trade = {
  id: number;
  product_id: string;
  strategy: string;
  status: string;
  quantity: number;
  entry_price_usd: number;
  entry_value_usd: number;
  stop_loss_usd: number | null;
  take_profit_usd: number | null;
  exit_price_usd: number | null;
  realized_pnl_usd: number;
  opened_at: string | null;
  closed_at: string | null;
};

export type PriceRow = {
  product_id: string;
  price_usd: number | null;
};

export type DashboardSummary = {
  account: {
    initial_cash_usd: number;
    cash_usd: number;
    equity_usd: number;
    realized_pnl_usd: number;
    trading_enabled: boolean;
    safety_lock_reason: string;
  };
  bot: {
    status: string;
    strategies: string[];
  };
  metrics: {
    win_rate_pct: number;
    closed_count: number;
    open_count: number;
  };
  prices: PriceRow[];
  trades: {
    open: Trade[];
    closed: Trade[];
  };
};

export type BacktestRunSummary = {
  id: number;
  strategy_name: string;
  strategy_version: string;
  granularity: string | null;
  period_name: string;
  product_id: string | null;
  product_ids: string[];
  start_date: string;
  end_date: string;
  starting_cash_usd: number;
  ending_equity_usd: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  trade_count: number;
  market_return_pct: number;
  notes: string;
  created_at: string | null;
};

export type BacktestsSummary = {
  total_runs: number;
  periods: string[];
  runs: BacktestRunSummary[];
};

export type Candle = {
  open: number;
  high: number;
  low: number;
  close: number;
};

export type StrategyExample = {
  label: string;
  side: "long" | "short";
  candles: Candle[];
  entry: number;
  stop_loss: number;
  take_profit: number;
  entry_index: number;
};

export type StrategyInfo = {
  name: string;
  version: string;
  title: string;
  summary: string;
  rules: {
    indicators: string[];
    entry: string;
    stop_loss: string;
    take_profit: string;
    risk: string;
  };
  examples: StrategyExample[];
};

export type StrategiesResponse = {
  strategies: StrategyInfo[];
};

async function getJson<T>(url: string, errorMessage: string): Promise<T> {
  // never serve a cached API response, so the dashboard always shows live data
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(errorMessage);
  }
  return response.json();
}

export function fetchDashboardSummary(): Promise<DashboardSummary> {
  return getJson("/api/dashboard/summary", "Dashboard summary request failed");
}

export function fetchBacktestsSummary(): Promise<BacktestsSummary> {
  return getJson("/api/backtests/summary", "Backtests summary request failed");
}

export function fetchStrategies(): Promise<StrategiesResponse> {
  return getJson("/api/strategies", "Strategies request failed");
}
