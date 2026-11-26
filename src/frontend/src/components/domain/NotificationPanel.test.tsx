import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NotificationPanel } from "./NotificationPanel";

describe("NotificationPanel", () => {
  it("renders notifications and exposes mark-all-read", () => {
    render(<NotificationPanel state={{ status: "ready", data: { notifications: [{ id: "1", title: "새 알림", message: "확인", createdAt: "오늘", read: false }] } }} onMarkAllRead={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "알림" })).toBeInTheDocument();
    expect(screen.getByText("새 알림")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "모두 읽음 처리" })).toBeInTheDocument();
  });

  it("renders an empty notification state", () => {
    render(<NotificationPanel state={{ status: "empty", message: "새로운 알림이 없습니다." }} onMarkAllRead={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getAllByText("새로운 알림이 없습니다.").length).toBeGreaterThan(0);
  });
});
