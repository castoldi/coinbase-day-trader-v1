import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";

afterEach(() => {
  cleanup();
});

describe("App", () => {
  it("renders the live trading dashboard shell", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Live Trading" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Trading History" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Account Management" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Backtests" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Strategies" })).toBeTruthy();
  });

  it("changes pages when dashboard menu buttons are clicked", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Trading History" }));
    expect(screen.getByRole("heading", { name: "Trading History" })).toBeTruthy();
    expect(screen.getByText("No trades recorded yet.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Account Management" }));
    expect(screen.getByRole("heading", { name: "Account Management" })).toBeTruthy();
    expect(screen.getByText("Safety lock")).toBeTruthy();
  });

  it("shows standard backtest periods when Backtests is selected", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Backtests" }));
    expect(screen.getByRole("heading", { name: "Backtests" })).toBeTruthy();
    expect(screen.getByText("No backtest runs recorded yet.")).toBeTruthy();
    expect(screen.getByText("2024")).toBeTruthy();
    expect(screen.getByText("2025")).toBeTruthy();
    expect(screen.getByText("2026")).toBeTruthy();
    expect(screen.getByText("Last 30 days")).toBeTruthy();
  });
});
