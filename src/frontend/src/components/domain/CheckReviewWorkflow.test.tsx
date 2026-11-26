import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureCheckProvider } from "../../api/checkProvider";
import type { CheckResult } from "../../types/domain";
import { CheckReviewWorkflow } from "./CheckReviewWorkflow";

const approvedResult: CheckResult = {
  id: "fixture-check-approved",
  title: "적합 광고",
  productType: "general-food",
  ingredient: "원료",
  channel: "상세페이지",
  copy: "안전한 광고 문구입니다.",
  attachments: [],
  findings: [],
  reviewId: "fixture-review-approved",
  nextStep: "법무팀 검토를 요청합니다.",
  marketingJudgment: "approved",
};

const rejectedResult: CheckResult = {
  ...approvedResult,
  id: "fixture-check-rejected",
  title: "부적합 광고",
  reviewId: "fixture-review-rejected",
  marketingJudgment: "rejected",
  findings: [{ id: "finding-1", severity: "violation-suspected", phrase: "효과를 보장합니다", reason: "확인 필요", allowedCopy: "도움을 줄 수 있어요", evidence: [], alternatives: ["도움을 줄 수 있어요"] }],
  recommendations: ["도움을 줄 수 있어요"],
};

describe("CheckReviewWorkflow", () => {
  it("requests legal review for an approved marketing result and navigates to reviews", async () => {
    const user = userEvent.setup();
    const provider = new FixtureCheckProvider();

    render(<MemoryRouter initialEntries={["/checks/fixture-check-approved"]}><Routes><Route path="/checks/:checkId" element={<CheckReviewWorkflow result={approvedResult} provider={provider} />} /><Route path="/reviews" element={<h1>검토함</h1>} /></Routes></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "[마케팅]광고 문구 검토 보고서", level: 2 })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "법무팀 검토 요청" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "법무팀 검토 요청" }));
    expect(await screen.findByRole("heading", { name: "검토함" })).toBeInTheDocument();
  });

  it("opens recommendation dialog for a rejected result and supports cancellation", async () => {
    const user = userEvent.setup();
    const provider = new FixtureCheckProvider();

    render(<MemoryRouter initialEntries={["/checks/fixture-check-rejected"]}><Routes><Route path="/checks/:checkId" element={<CheckReviewWorkflow result={rejectedResult} provider={provider} />} /><Route path="/reviews" element={<h1>검토함</h1>} /></Routes></MemoryRouter>);

    expect(screen.getByText("도움을 줄 수 있어요")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "심의 취소" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "AI 추천 요청" }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(within(await screen.findByRole("dialog")).getByText("추천 광고 문구")).toBeInTheDocument();
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getAllByRole("button", { name: "닫기" })[1]);
    expect(await screen.findByRole("heading", { name: "검토함" })).toBeInTheDocument();
  });
});
