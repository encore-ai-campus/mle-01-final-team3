import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ReviewEditDialog } from "./ReviewEditDialog";

describe("ReviewEditDialog", () => {
  it("allows only title, category, and detail copy to be edited", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();

    render(
      <ReviewEditDialog
        task={{
          id: "fixture-review-1",
          title: "저당 에너지바 광고",
          advertiser: "푸드가드 식품",
          author: "김마케팅",
          category: "건강기능식품",
          submittedAt: "2026-11-24 09:20",
          sentAt: "2026-11-24 10:00",
          status: "first-review-completed",
          judgment: "pending",
          assignee: "김마케팅",
          processedAt: null,
          ownerId: "fixture-user",
        }}
        detailCopy="기존 상세 내용"
        onSave={onSave}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("작성자")).toHaveAttribute("readonly");
    expect(screen.getByLabelText("상태")).toHaveAttribute("readonly");
    expect(screen.getByLabelText("전송일")).toHaveAttribute("readonly");
    await user.clear(screen.getByLabelText("광고명"));
    await user.type(screen.getByLabelText("광고명"), "수정 광고명");
    await user.click(screen.getByRole("button", { name: "저장" }));

    expect(onSave).toHaveBeenCalledWith({ title: "수정 광고명", category: "건강기능식품", copy: "기존 상세 내용" });
  });
});
