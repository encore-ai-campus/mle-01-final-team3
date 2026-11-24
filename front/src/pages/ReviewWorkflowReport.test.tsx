import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { ReviewDetailPage } from "./ReviewDetailPage";
import { ReviewReportPage } from "./ReviewReportPage";

describe("ReviewWorkflowReport", () => {
  it("renders the status-specific first review report and actions", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-1"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-1", "first-review-completed")} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "1차 검토 보고서" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "법무팀 검토 요청" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2차 검토 요청" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "닫기" })).toBeInTheDocument();
  });

  it("links reference reports and provides a return action on the report detail", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-2"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-1", "second-review-completed")} />} /><Route path="/reviews/:reviewId/reports/:reportStage" element={<ReviewReportPage provider={new FixtureProvider()} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("link", { name: "1차 검토 보고서" })).toHaveAttribute("href", "/reviews/fixture-review-1/reports/first-review");
  });
});
