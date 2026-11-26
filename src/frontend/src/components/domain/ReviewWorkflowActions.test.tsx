import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReviewWorkflowActions } from "./ReviewWorkflowActions";

describe("ReviewWorkflowActions", () => {
  it("shows only the next action for the recorded first-review result", async () => {
    const onAction = vi.fn();
    const { rerender } = render(<ReviewWorkflowActions reviewId="fixture-review-1" status="first-review-completed" judgment="rejected" role="unknown" onAction={onAction} onClose={vi.fn()} />);

    expect(screen.queryByRole("button", { name: "적합" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "부적합" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2차 검토 요청" })).toBeInTheDocument();

    rerender(<ReviewWorkflowActions reviewId="fixture-review-1" status="second-review-completed" judgment="rejected" role="unknown" onAction={onAction} onClose={vi.fn()} />);
    expect(screen.getByRole("button", { name: "삭제" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "닫기" })).toBeInTheDocument();

    rerender(<ReviewWorkflowActions reviewId="fixture-review-1" status="first-review-completed" judgment="approved" role="unknown" onAction={onAction} onClose={vi.fn()} />);
    expect(screen.getByRole("button", { name: "법무팀 검토 요청" })).toBeInTheDocument();
    screen.getByRole("button", { name: "법무팀 검토 요청" }).click();
    expect(onAction).toHaveBeenCalledWith("request-legal-review");
  });

  it("does not expose legal decisions to a marketing member", () => {
    render(<ReviewWorkflowActions reviewId="fixture-review-3" status="legal-review" judgment="pending" role="marketing" onAction={vi.fn()} onClose={vi.fn()} />);

    expect(screen.queryByRole("button", { name: "승인" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "반려" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "닫기" })).toBeInTheDocument();
  });

  it("requires a legal opinion before a legal reviewer can complete the review", async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    render(<ReviewWorkflowActions reviewId="fixture-review-3" status="legal-pending" judgment="pending" role="legal" onAction={onAction} onClose={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "진행 가능" }));
    expect(screen.getByRole("status")).toHaveTextContent("의견을 입력해 주세요.");
    expect(onAction).not.toHaveBeenCalled();
    await user.type(screen.getByRole("textbox", { name: "의견" }), "문구를 확인했습니다.");
    await user.click(screen.getByRole("button", { name: "진행 가능" }));
    expect(onAction).toHaveBeenCalledWith("complete-legal-continuable", "문구를 확인했습니다.");
  });

  it.each(["legal-pending", "legal-in-progress"] as const)("shows legal outcome actions for %s", async (status) => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    render(<ReviewWorkflowActions reviewId="fixture-review-3" status={status} judgment="pending" role="legal" onAction={onAction} onClose={vi.fn()} />);

    expect(screen.getByRole("button", { name: "보완 필요" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "진행 가능" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "닫기" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "보완 필요" }));
    expect(screen.getByRole("status")).toHaveTextContent("의견을 입력해 주세요.");
    expect(onAction).not.toHaveBeenCalled();

    await user.type(screen.getByRole("textbox", { name: "의견" }), "보완 후 다시 확인해 주세요.");
    await user.click(screen.getByRole("button", { name: "보완 필요" }));
    expect(onAction).toHaveBeenCalledWith("complete-legal-needs-revision", "보완 후 다시 확인해 주세요.");
  });
});
