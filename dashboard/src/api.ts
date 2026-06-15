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
  trades: {
    open: unknown[];
    closed: unknown[];
  };
};

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch("/api/dashboard/summary");
  if (!response.ok) {
    throw new Error("Dashboard summary request failed");
  }
  return response.json();
}
