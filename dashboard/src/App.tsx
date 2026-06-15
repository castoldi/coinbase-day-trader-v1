import React, { useState } from "react";
import { Activity, BarChart3, BookOpen, History, Landmark } from "lucide-react";

type Page = "Live Trading" | "Trading History" | "Account Management" | "Backtests" | "Strategies";

const navItems = [
  ["Live Trading", Activity],
  ["Trading History", History],
  ["Account Management", Landmark],
  ["Backtests", BarChart3],
  ["Strategies", BookOpen],
] as const;

const metrics = [
  ["Equity", "$1,000.00", "Starting paper capital"],
  ["Cash", "$1,000.00", "Available to deploy"],
  ["PnL", "$0.00", "Realized"],
  ["Win Rate", "0%", "No closed trades"],
] as const;

const backtestPeriods = ["2024", "2025", "2026", "Last 30 days"] as const;

export default function App() {
  const [activePage, setActivePage] = useState<Page>("Live Trading");

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
              onClick={() => setActivePage(label)}
              type="button"
              title={label}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Paper trading control room</p>
            <h1>{activePage}</h1>
          </div>
          <span className="statusPill">Local mode</span>
        </header>
        {activePage === "Live Trading" && <LiveTradingPage />}
        {activePage === "Trading History" && <TradingHistoryPage />}
        {activePage === "Account Management" && <AccountManagementPage />}
        {activePage === "Backtests" && <BacktestsPage />}
        {activePage === "Strategies" && <StrategiesPage />}
      </section>
    </main>
  );
}

function LiveTradingPage() {
  return (
    <>
      <section className="metricGrid" aria-label="Trading metrics">
        {metrics.map(([label, value, note]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{note}</small>
          </article>
        ))}
      </section>
      <section className="tradeLayout">
        <article className="tableSurface">
          <div className="sectionHeader">
            <h2>Open Trades</h2>
            <span>0 active</span>
          </div>
          <p>No open trades.</p>
        </article>
        <article className="tableSurface">
          <div className="sectionHeader">
            <h2>Coins Trading</h2>
            <span>Watchlist</span>
          </div>
          <ul className="coinList">
            <li><span>BTC-USD</span><strong>Ready</strong></li>
            <li><span>ETH-USD</span><strong>Ready</strong></li>
            <li><span>SOL-USD</span><strong>Ready</strong></li>
          </ul>
        </article>
      </section>
    </>
  );
}

function TradingHistoryPage() {
  return (
    <section className="pageGrid">
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Closed Trades</h2>
          <span>0 recorded</span>
        </div>
        <p>No trades recorded yet.</p>
      </article>
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Open Trades</h2>
          <span>Paper ledger</span>
        </div>
        <p>No open trades.</p>
      </article>
    </section>
  );
}

function AccountManagementPage() {
  return (
    <section className="metricGrid" aria-label="Account controls">
      <article>
        <span>Starting Capital</span>
        <strong>$1,000.00</strong>
        <small>Paper account baseline</small>
      </article>
      <article>
        <span>Current Equity</span>
        <strong>$1,000.00</strong>
        <small>Rollover balance</small>
      </article>
      <article>
        <span>Safety lock</span>
        <strong>Armed</strong>
        <small>Stops trading at 50% drawdown</small>
      </article>
      <article>
        <span>Manual reset</span>
        <strong>Ready</strong>
        <small>Use CLI when lock trips</small>
      </article>
    </section>
  );
}

function BacktestsPage() {
  return (
    <section className="pageGrid">
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Summary</h2>
          <span>0 runs</span>
        </div>
        <p>No backtest runs recorded yet.</p>
      </article>
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>Standard Periods</h2>
          <span>$1,000 each</span>
        </div>
        <ul className="coinList">
          {backtestPeriods.map((period) => (
            <li key={period}><span>{period}</span><strong>Pending</strong></li>
          ))}
        </ul>
      </article>
    </section>
  );
}

function StrategiesPage() {
  return (
    <section className="pageGrid">
      <article className="tableSurface">
        <div className="sectionHeader">
          <h2>price_action_transcript</h2>
          <span>Transcript gated</span>
        </div>
        <p>Strategy signals stay on hold until the YouTube transcript is reviewed and encoded.</p>
      </article>
    </section>
  );
}
