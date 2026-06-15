import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the live trading dashboard shell", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Live Trading" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Trading History" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Account Management" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Backtests" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Strategies" })).toBeTruthy();
  });
});
