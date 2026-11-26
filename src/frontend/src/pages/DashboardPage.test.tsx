import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { DashboardPage } from "./DashboardPage";

describe("DashboardPage", () => {
  it("renders provider summary data without quick actions or the review shortcut", async () => {
    render(<MemoryRouter><DashboardPage provider={new FixtureProvider("LG-1")} /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "대시보드" })).toBeInTheDocument();
    expect((await screen.findAllByText("저당 에너지바 광고")).length).toBeGreaterThan(0);
    expect(screen.queryByRole("link", { name: /검토함에서 보기/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ 새 광고 문구 검사" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "새로고침" })).not.toBeInTheDocument();
    expect(screen.queryByText("검토함에서 전체 보고서를 확인하세요.")).not.toBeInTheDocument();
  });

  it("renders the empty state from the provider", async () => {
    render(<MemoryRouter><DashboardPage provider={new FixtureProvider("LG-2")} /></MemoryRouter>);
    expect(await screen.findByText("접수된 보고서가 없습니다.")).toBeInTheDocument();
  });
});
