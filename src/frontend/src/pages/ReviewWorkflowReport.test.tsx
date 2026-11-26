import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { ReviewDetailPage } from "./ReviewDetailPage";
import { ReviewReportPage } from "./ReviewReportPage";

describe("ReviewWorkflowReport", () => {
  it("renders the marketing report for a marketing-completed document", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-1"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-1", "marketing-completed-rejected")} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "[마케팅]광고 문구 검토 보고서" })).toBeInTheDocument();
    expect(screen.getByText("[마케팅]검토 완료(부적합)")).toBeInTheDocument();
  });

  it("keeps review editing inline and protects non-editable fields", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-1?edit=true"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-1", "marketing-completed-rejected")} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "검토 보고서 수정" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByLabelText("작성자")).toHaveAttribute("readonly");
    expect(screen.getByLabelText("상태")).toHaveAttribute("readonly");
    expect(screen.getByLabelText("전송일")).toHaveAttribute("readonly");
  });

  it("renders the legal report and a link to the same document's marketing report", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-2/reports/legal"]}><Routes><Route path="/reviews/:reviewId/reports/:reportStage" element={<ReviewReportPage provider={new FixtureProvider()} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { level: 1, name: "[법무]광고 문구 검토 보고서" })).toBeInTheDocument();
    const marketingLinks = screen.getAllByRole("link", { name: "[마케팅]광고 문구 검토 보고서" });
    expect(marketingLinks.some((link) => link.getAttribute("href") === "/reviews/fixture-review-2/reports/marketing")).toBe(true);
    expect(screen.getByRole("link", { name: "돌아가기" })).toHaveAttribute("href", "/reviews/fixture-review-2");
  });

  it("renders the marketing report route with the return link", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-1/reports/marketing"]}><Routes><Route path="/reviews/:reviewId/reports/:reportStage" element={<ReviewReportPage provider={new FixtureProvider()} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { level: 1, name: "[마케팅]광고 문구 검토 보고서" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "돌아가기" })).toHaveAttribute("href", "/reviews/fixture-review-1");
  });

  it("lets only a legal reviewer complete a legal review with a required opinion", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-5?team=legal"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-1", "legal-pending")} workflowRole="legal" />} /><Route path="/reviews" element={<h1>검토함</h1>} /></Routes></MemoryRouter>);

    const opinion = await screen.findByRole("textbox", { name: "의견" });
    await user.click(screen.getByRole("button", { name: "진행 가능" }));
    expect(screen.getAllByRole("status").some((element) => element.textContent?.includes("의견을 입력해 주세요."))).toBe(true);
    await user.type(opinion, "표현상 문제가 없어 승인합니다.");
    await user.click(screen.getByRole("button", { name: "진행 가능" }));
    expect(await screen.findByRole("heading", { name: "검토함" })).toBeInTheDocument();
  });

  it("renders the legal outcome label for a continuable review", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-3"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-1", "legal-completed-continuable")} workflowRole="legal" />} /></Routes></MemoryRouter>);

    expect((await screen.findAllByText("진행 가능")).length).toBeGreaterThan(0);
    expect(screen.getByRole("tab", { name: "[법무]광고 문구 검토 보고서" })).toBeInTheDocument();
  });
});
