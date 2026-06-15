import React, { useEffect, useState } from "react";
import { Activity, BarChart3, BookOpen, History, Landmark } from "lucide-react";
import { buildCoinBreakdown } from "./breakdown";
import {
  fetchBacktestsSummary,
  fetchDashboardSummary,
  fetchStrategies,
  type BacktestsSummary,
  type DashboardSummary,
  type PriceRow,
  type StrategiesResponse,
  type StrategyExample,
  type StrategyInfo,
  type Trade,
} from "./api";

type Page = "Live Trading" | "Trading History" | "Account Management" | "Backtests" | "Strategies";

const navItems = [
  ["Live Trading", Activity],
  ["Trading History", History],
  ["Account Management", Landmark],
  ["Backtests", BarChart3],
  ["Strategies", BookOpen],
] as const;

const APP_VERSION = typeof __APP_VERSION__ !== "undefined" ? __APP_VERSION__ : "dev";

const POLL_INTERVAL_MS = 10000;

const pageSlugs: Record<Page, string> = {
  "Live Trading": "live-trading",
  "Trading History": "trading-history",
  "Account Management": "account-management",
  Backtests: "backtests",
  Strategies: "strategies",
};
const slugToPage = Object.fromEntries(
  Object.entries(pageSlugs).map(([page, slug]) => [slug, page as Page]),
) as Record<string, Page>;

function pageFromHash(): Page {
  const slug = window.location.hash.replace(/^#/, "");
  return slugToPage[slug] ?? "Live Trading";
}

export default function App() {
  const [activePage, setActivePage] = useState<Page>(pageFromHash);
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [backtestsSummary, setBacktestsSummary] = useState<BacktestsSummary | null>(null);
  const [strategies, setStrategies] = useState<StrategiesResponse | null>(null);
  const [dashboardError, setDashboardError] = useState("");
  const [backtestsError, setBacktestsError] = useState("");
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [backtestsLoading, setBacktestsLoading] = useState(true);

  useEffect(() => {
    let alive = true;

    async function load<T>(
      loader: () => Promise<T>,
      onData: (data: T) => void,
      onError: (message: string) => void,
      fallback: string,
      onSettled?: () => void,
    ) {
      try {
        const data = await loader();
        if (alive) {
          onData(data);
          onError("");
        }
      } catch (error) {
        if (alive) {
          onError(error instanceof Error ? error.message : fallback);
        }
      } finally {
        if (alive) {
          onSettled?.();
        }
      }
    }

    function loadAll() {
      void load(fetchDashboardSummary, setDashboardSummary, setDashboardError, "Dashboard request failed", () =>
        setDashboardLoading(false),
      );
      void load(fetchBacktestsSummary, setBacktestsSummary, setBacktestsError, "Backtests request failed", () =>
        setBacktestsLoading(false),
      );
      void load(fetchStrategies, setStrategies, () => {}, "Strategies request failed");
    }

    // initial fetch + async background polling that updates state in place
    // (no full-page reload); also refetches immediately on navigation
    loadAll();
    const timer = setInterval(loadAll, POLL_INTERVAL_MS);

    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [activePage]);

  useEffect(() => {
    const onHashChange = () => setActivePage(pageFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigate = (page: Page) => {
    window.location.hash = pageSlugs[page];
    setActivePage(page);
  };

  return (
    <main className="appShell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brandMark">CB</span>
          <span>Coinbase Day Trader</span>
        </div>
        <nav aria-label="Dashboard">
          {navItems.map(([label, Icon]) => (
            <button
              aria-current={activePage === label ? "page" : undefined}
              className={`navButton${activePage === label ? " navButtonActive" : ""}`}
              key={label}
              onClick={() => navigate(label)}
              type="button"
              title={label}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="buildTag">Build {APP_VERSION}</div>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Paper trading control room</p>
            <h1>{activePage}</h1>
          </div>
          <span className="statusPill">
            {dashboardSummary?.bot.status ? dashboardSummary.bot.status.replaceAll("_", " ") : "Loading"}
          </span>
        </header>
        {activePage === "Live Trading" && (
          <LiveTradingPage summary={dashboardSummary} loading={dashboardLoading} error={dashboardError} />
        )}
        {activePage === "Trading History" && (
          <TradingHistoryPage summary={dashboardSummary} loading={dashboardLoading} error={dashboardError} />
        )}
        {activePage === "Account Management" && (
          <AccountManagementPage summary={dashboardSummary} loading={dashboardLoading} error={dashboardError} />
        )}
        {activePage === "Backtests" && (
          <BacktestsPage summary={backtestsSummary} loading={backtestsLoading} error={backtestsError} />
        )}
        {activePage === "Strategies" && (
          <StrategiesPage strategies={strategies} backtests={backtestsSummary} />
        )}
      </section>
    </main>
  );
}

function LiveTradingPage({
  summary,
  loading,
  error,
}: {
  summary: DashboardSummary | null;
  loading: boolean;
  error: string;
}) {
  const metrics = [
    ["Equity", formatCurrency(summary?.account.equity_usd ?? 1000), "Paper account equity"],
    ["Cash", formatCurrency(summary?.account.cash_usd ?? 1000), "Available to deploy"],
    ["Realized PnL", formatCurrency(summary?.account.realized_pnl_usd ?? 0), "Closed trade performance"],
    [
      "Win Rate",
      `${(summary?.metrics?.win_rate_pct ?? 0).toFixed(0)}%`,
      `${summary?.metrics?.closed_count ?? 0} closed trades`,
    ],
  ] as const;

  return (
    <>
      <section className="metricGrid" aria-label="Trading metrics">
        {metrics.map(([label, value, note]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{loading ? "Loading…" : note}</small>
          </article>
        ))}
      </section>
      {error ? <p className="feedbackText">{error}</p> : null}
      <section className="tradeLayout">
        <article className="tableSurface">
          <div className="sectionHeader">
            <h2>Open Trades</h2>
            <span>{summary?.trades.open.length ?? 0} active</span>
          </div>
          <TradeTable trades={summary?.trades.open ?? []} emptyText="No open trades." />
        </article>
        <article className="tableSurface">
          <div className="sectionHeader">
            <h2>Coin Prices</h2>
            <span>Latest close</span>
          </div>
          <PriceList prices={summary?.prices ?? []} />
        </article>
      </section>
    </>
  );
}

function TradingHistoryPage({
  summary,
  loading,
  error,
}: {
  summary: DashboardSummary | null;
  loading: boolean;
  error: string;
}) {
  return (
    <section className="pageStack">
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Closed Trades</h2>
          <span>{summary?.trades.closed.length ?? 0} recorded</span>
        </div>
        {loading ? (
          <p>Loading trade history.</p>
        ) : (
          <TradeTable trades={summary?.trades.closed ?? []} emptyText="No trades recorded yet." showExit />
        )}
      </article>
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Open Trades</h2>
          <span>{summary?.trades.open.length ?? 0} active</span>
        </div>
        <TradeTable trades={summary?.trades.open ?? []} emptyText="No open trades." />
      </article>
      {error ? <p className="feedbackText">{error}</p> : null}
    </section>
  );
}

function AccountManagementPage({
  summary,
  loading,
  error,
}: {
  summary: DashboardSummary | null;
  loading: boolean;
  error: string;
}) {
  return (
    <section className="metricGrid" aria-label="Account controls">
      <article>
        <span>Starting Capital</span>
        <strong>{formatCurrency(summary?.account.initial_cash_usd ?? 1000)}</strong>
        <small>{loading ? "Loading baseline" : "Paper account baseline"}</small>
      </article>
      <article>
        <span>Current Equity</span>
        <strong>{formatCurrency(summary?.account.equity_usd ?? 1000)}</strong>
        <small>{loading ? "Loading equity" : "Rollover balance"}</small>
      </article>
      <article>
        <span>Safety lock</span>
        <strong>{summary?.account.trading_enabled ? "Armed" : "Tripped"}</strong>
        <small>{summary?.account.safety_lock_reason || "Stops trading at 50% drawdown"}</small>
      </article>
      <article>
        <span>Manual reset</span>
        <strong>Ready</strong>
        <small>Run `trader reset-safety` when the lock trips</small>
      </article>
      {error ? <p className="feedbackText feedbackTextFull">{error}</p> : null}
    </section>
  );
}

function BacktestsPage({
  summary,
  loading,
  error,
}: {
  summary: BacktestsSummary | null;
  loading: boolean;
  error: string;
}) {
  const runs = summary?.runs ?? [];
  const breakdown = buildCoinBreakdown(runs);

  return (
    <section className="pageStack">
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Summary</h2>
          <span>{loading ? "Loading" : `${summary?.total_runs ?? 0} runs`}</span>
        </div>
        <p>
          {error
            ? error
            : runs.length
              ? `${breakdown.coins.length} coins × ${breakdown.granularities.length} timeframes × ${breakdown.strategies.length} strategies. Each cell is that strategy's return on that coin, timeframe, and period.`
              : loading
                ? "Loading backtest runs."
                : "No backtest runs recorded yet."}
        </p>
        {runs.length ? (
          <p className="inlineNote">
            Each backtest starts with $1,000 per coin and is net of trading fees. Cells show return
            with trades · win rate. "Buy &amp; Hold" is the coin's market move over the window
            (strategy-independent).
          </p>
        ) : null}
      </article>
      {breakdown.coins.map((coin) => (
        <CoinBreakdownSection key={coin.product_id} coin={coin} strategies={breakdown.strategies} />
      ))}
    </section>
  );
}

function CoinBreakdownSection({
  coin,
  strategies,
}: {
  coin: ReturnType<typeof buildCoinBreakdown>["coins"][number];
  strategies: ReturnType<typeof buildCoinBreakdown>["strategies"];
}) {
  return (
    <article className="tableSurface">
      <div className="sectionHeader">
        <h2>{coin.product_id}</h2>
        <span>$1,000 per backtest · net of fees</span>
      </div>
      {coin.granularities.map((gran) => (
        <div key={gran.granularity} className="granularityBlock">
          <h3 className="granularityHeading">{formatGranularity(gran.granularity)}</h3>
          <div className="tableWrap">
            <table className="dataTable">
              <thead>
                <tr>
                  <th>Period</th>
                  {strategies.map((strategy) => (
                    <th key={strategy.key}>{strategy.name}</th>
                  ))}
                  <th>Buy &amp; Hold</th>
                </tr>
              </thead>
              <tbody>
                {gran.rows.map((row) => (
                  <tr key={row.period}>
                    <td>{formatPeriodName(row.period)}</td>
                    {strategies.map((strategy) => {
                      const run = row.cells[strategy.key];
                      if (!run) {
                        return <td key={strategy.key}>—</td>;
                      }
                      return (
                        <td key={strategy.key}>
                          <span className={run.total_return_pct >= 0 ? "pnlUp" : "pnlDown"}>
                            {formatPercent(run.total_return_pct)}
                          </span>
                          <span className="cellSub">
                            {run.trade_count} {run.trade_count === 1 ? "trade" : "trades"}
                            {run.trade_count > 0 ? ` · ${Math.round(run.win_rate_pct)}% win` : ""}
                          </span>
                        </td>
                      );
                    })}
                    <td>{formatPercent(row.market_return_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </article>
  );
}

function StrategiesPage({
  strategies,
  backtests,
}: {
  strategies: StrategiesResponse | null;
  backtests: BacktestsSummary | null;
}) {
  if (!strategies?.strategies.length) {
    return (
      <section className="pageGrid">
        <article className="tableSurface">
          <h2>Loading strategies…</h2>
        </article>
      </section>
    );
  }

  const allRuns = backtests?.runs ?? [];

  return (
    <section className="pageStack">
      {strategies.strategies.map((strategy) => {
        const strategyRuns = allRuns.filter((run) => run.strategy_name === strategy.name);
        const latestRun =
          [...strategyRuns]
            .filter((run) => run.created_at)
            .sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)))[0] ?? null;
        return <StrategyCard key={strategy.name} strategy={strategy} latestRun={latestRun} />;
      })}
    </section>
  );
}

function StrategyCard({
  strategy,
  latestRun,
}: {
  strategy: StrategyInfo;
  latestRun: BacktestsSummary["runs"][number] | null;
}) {
  return (
    <article className="tableSurface">
      <div className="sectionHeader">
        <h2>{strategy.title}</h2>
        <span>
          {strategy.name} {strategy.version}
        </span>
      </div>
      <p>{strategy.summary}</p>
      <ul className="ruleList">
        {strategy.rules.indicators.map((indicator) => (
          <li key={indicator}>{indicator}</li>
        ))}
        <li>
          <strong>Entry:</strong> {strategy.rules.entry}
        </li>
        <li>
          <strong>Stop loss:</strong> {strategy.rules.stop_loss}
        </li>
        <li>
          <strong>Take profit:</strong> {strategy.rules.take_profit}
        </li>
        <li>
          <strong>Risk:</strong> {strategy.rules.risk}
        </li>
      </ul>
      <div className="chartGrid">
        {strategy.examples.map((example) => (
          <figure className="chartCard" key={example.label}>
            <figcaption>{example.label}</figcaption>
            <CandleChart example={example} />
            <div className="chartLegend">
              <span className="legendEntry">Entry {formatPrice(example.entry)}</span>
              <span className="legendStop">Stop {formatPrice(example.stop_loss)}</span>
              <span className="legendTake">Target {formatPrice(example.take_profit)}</span>
            </div>
          </figure>
        ))}
      </div>
      {latestRun ? (
        <p className="inlineNote">
          Latest backtest ({formatPeriodName(latestRun.period_name)}): {latestRun.notes}
        </p>
      ) : null}
    </article>
  );
}

function CandleChart({ example }: { example: StrategyExample }) {
  const width = 340;
  const height = 200;
  const padding = { top: 12, right: 56, bottom: 12, left: 12 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const levels = [example.entry, example.stop_loss, example.take_profit];
  const highs = example.candles.map((candle) => candle.high);
  const lows = example.candles.map((candle) => candle.low);
  const max = Math.max(...highs, ...levels);
  const min = Math.min(...lows, ...levels);
  const range = max - min || 1;

  const y = (value: number) => padding.top + (1 - (value - min) / range) * innerHeight;
  const slot = innerWidth / example.candles.length;
  const bodyWidth = Math.max(4, slot * 0.55);

  const line = (value: number, className: string, label: string) => (
    <g key={label}>
      <line
        x1={padding.left}
        x2={padding.left + innerWidth}
        y1={y(value)}
        y2={y(value)}
        className={className}
        strokeDasharray="4 3"
      />
      <text x={padding.left + innerWidth + 4} y={y(value) + 4} className="chartLabel">
        {label}
      </text>
    </g>
  );

  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${example.label} chart`} className="candleChart">
      {line(example.take_profit, "lineTake", "TP")}
      {line(example.entry, "lineEntry", "Entry")}
      {line(example.stop_loss, "lineStop", "SL")}
      {example.candles.map((candle, index) => {
        const center = padding.left + slot * index + slot / 2;
        const bullish = candle.close >= candle.open;
        const bodyTop = y(Math.max(candle.open, candle.close));
        const bodyBottom = y(Math.min(candle.open, candle.close));
        const isEntry = index === example.entry_index;
        return (
          <g key={index} className={bullish ? "candleUp" : "candleDown"}>
            <line x1={center} x2={center} y1={y(candle.high)} y2={y(candle.low)} className="candleWick" />
            <rect
              x={center - bodyWidth / 2}
              y={bodyTop}
              width={bodyWidth}
              height={Math.max(2, bodyBottom - bodyTop)}
              className={isEntry ? "candleBody candleEntry" : "candleBody"}
            />
          </g>
        );
      })}
    </svg>
  );
}

function TradeTable({
  trades,
  emptyText,
  showExit = false,
}: {
  trades: Trade[];
  emptyText: string;
  showExit?: boolean;
}) {
  if (!trades.length) {
    return <p>{emptyText}</p>;
  }
  return (
    <div className="tableWrap">
      <table className="dataTable">
        <thead>
          <tr>
            <th>Product</th>
            <th>Strategy</th>
            <th>Qty</th>
            <th>Entry</th>
            <th>Stop</th>
            <th>Target</th>
            {showExit ? <th>Exit</th> : null}
            <th>PnL</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.id}>
              <td>{trade.product_id}</td>
              <td>{trade.strategy}</td>
              <td>{trade.quantity.toFixed(6)}</td>
              <td>{formatPrice(trade.entry_price_usd)}</td>
              <td>{trade.stop_loss_usd != null ? formatPrice(trade.stop_loss_usd) : "—"}</td>
              <td>{trade.take_profit_usd != null ? formatPrice(trade.take_profit_usd) : "—"}</td>
              {showExit ? <td>{trade.exit_price_usd != null ? formatPrice(trade.exit_price_usd) : "—"}</td> : null}
              <td className={trade.realized_pnl_usd >= 0 ? "pnlUp" : "pnlDown"}>
                {formatCurrency(trade.realized_pnl_usd)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PriceList({ prices }: { prices: PriceRow[] }) {
  if (!prices.length) {
    return <p>No coins configured.</p>;
  }
  return (
    <ul className="coinList">
      {prices.map((row) => (
        <li key={row.product_id}>
          <span>{row.product_id}</span>
          <strong>{row.price_usd != null ? formatCurrency(row.price_usd) : "No data yet"}</strong>
        </li>
      ))}
    </ul>
  );
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatPrice(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number) {
  return `${value.toFixed(2)}%`;
}

function formatPeriodName(period: string) {
  const recent = period.match(/^last_(\d+)_days$/);
  if (recent) {
    return `Last ${recent[1]} Days`;
  }
  return period;
}

const GRANULARITY_LABELS: Record<string, string> = {
  ONE_MINUTE: "1-minute candles",
  FIVE_MINUTE: "5-minute candles",
  FIFTEEN_MINUTE: "15-minute candles",
  ONE_HOUR: "1-hour candles",
  SIX_HOUR: "6-hour candles",
  ONE_DAY: "Daily candles",
};

function formatGranularity(granularity: string) {
  return GRANULARITY_LABELS[granularity] ?? granularity;
}
