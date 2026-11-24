import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ReviewDetail } from "../../types/domain";
import { ReviewDecisionForm } from "./ReviewDecisionForm";

const detail: ReviewDetail = {
  id: "review-1", title: "보고서", advertiser: "광고주", submittedAt: "날짜", status: "waiting", judgment: "pending", assignee: "담당자", processedAt: null, ownerId: "user", copy: "문구", attachments: [], canDecide: true, readOnlyReason: null, decisionReason: null, pdfUrl: null,
};

describe("ReviewDecisionForm", () => {
  it("requires confirmation for approve and a reason for reject", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<ReviewDecisionForm detail={detail} onSubmit={onSubmit} pending={false} />);
    await user.click(screen.getByRole("button", { name: "적합" }));
    expect(screen.getByRole("dialog", { name: "적합 처리" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "확인" }));
    expect(onSubmit).toHaveBeenCalledWith({ reviewId: "review-1", decision: "approved" });
  });
});
