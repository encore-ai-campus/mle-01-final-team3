import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { DataProvider } from "../../types/api";
import type { DataState, ReviewTask } from "../../types/domain";
import { WorkBadge } from "./WorkBadge";

function task(status: ReviewTask["status"], id?: string): ReviewTask {
  const taskId = id ?? status;
  return {
    id: taskId,
    title: taskId,
    advertiser: "테스트 광고주",
    author: "테스트 작성자",
    category: "일반",
    submittedAt: "2026-01-01",
    sentAt: "2026-01-01",
    status,
    judgment: "pending",
    assignee: null,
    processedAt: null,
    ownerId: null,
  };
}

function providerWith(result: DataState<ReviewTask[]>): DataProvider {
  return { listReviews: vi.fn().mockResolvedValue(result) } as unknown as DataProvider;
}

describe("WorkBadge", () => {
  it("renders a red bell with the marketing user's actionable count", async () => {
    const provider = providerWith({ status: "ready", data: [task("waiting"), task("legal-pending")] });

    render(<MemoryRouter><WorkBadge provider={provider} department="marketing" currentPath="/" currentSearch="" onNavigate={vi.fn()} /></MemoryRouter>);

    const button = await screen.findByRole("button", { name: "처리할 업무 1건" });
    expect(button).toHaveClass("work-badge");
    expect(screen.getByText("1")).toHaveClass("work-badge__count");
  });

  it("shows 99 plus for counts of 100 or more", async () => {
    const provider = providerWith({ status: "ready", data: Array.from({ length: 100 }, (_, index) => task("legal-pending", `legal-${index}`)) });

    render(<MemoryRouter><WorkBadge provider={provider} department="legal" currentPath="/" currentSearch="" onNavigate={vi.fn()} /></MemoryRouter>);

    expect(await screen.findByText("99+")).toBeInTheDocument();
  });

  it("hides the count at zero and navigates to the reviews page", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    const provider = providerWith({ status: "ready", data: [] });

    render(<MemoryRouter><WorkBadge provider={provider} department="legal" currentPath="/" currentSearch="" onNavigate={onNavigate} /></MemoryRouter>);

    const button = await screen.findByRole("button", { name: "처리할 업무 없음" });
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    await user.click(button);
    expect(onNavigate).toHaveBeenCalledWith("/reviews");
  });

  it("keeps the icon available when the work list fails", async () => {
    const provider = providerWith({ status: "error", error: { kind: "http", message: "오류" } });

    render(<MemoryRouter><WorkBadge provider={provider} department="marketing" currentPath="/" currentSearch="" onNavigate={vi.fn()} /></MemoryRouter>);

    await waitFor(() => expect(screen.getByRole("button", { name: "처리할 업무 확인" })).toBeInTheDocument());
  });

  it("keeps the icon available when the provider rejects the request", async () => {
    const provider = { listReviews: vi.fn().mockRejectedValue(new Error("network")) } as unknown as DataProvider;

    render(<MemoryRouter><WorkBadge provider={provider} department="marketing" currentPath="/" currentSearch="" onNavigate={vi.fn()} /></MemoryRouter>);

    await waitFor(() => expect(screen.getByRole("button", { name: "처리할 업무 확인" })).toBeInTheDocument());
  });
});
