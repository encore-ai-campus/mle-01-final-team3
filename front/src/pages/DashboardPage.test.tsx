import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { DashboardPage } from "./DashboardPage";

describe("DashboardPage", () => {
  it("renders provider summary data and task links", async () => {
    render(<MemoryRouter><DashboardPage provider={new FixtureProvider("LG-1")} /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "대시보드" })).toBeInTheDocument();
    expect((await screen.findAllByText("예시 검토 보고서")).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "검토함에서 보기" })).toHaveAttribute("href", "/reviews");
  });

  it("renders the empty state from the provider", async () => {
    render(<MemoryRouter><DashboardPage provider={new FixtureProvider("LG-2")} /></MemoryRouter>);
    expect(await screen.findByText("접수된 보고서가 없습니다.")).toBeInTheDocument();
  });
});
