import { describe, expect, it } from "vitest";
import type { ReviewTask } from "../types/domain";
import { countActionableReviews, isActionRequiredForDepartment } from "./workBadge";

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

describe("workBadge", () => {
  it("counts marketing work and excludes completed or cancelled documents", () => {
    expect(isActionRequiredForDepartment(task("waiting"), "marketing")).toBe(true);
    expect(isActionRequiredForDepartment(task("in-progress"), "marketing")).toBe(true);
    expect(isActionRequiredForDepartment(task("marketing-completed-rejected"), "marketing")).toBe(true);
    expect(isActionRequiredForDepartment(task("marketing-completed-approved"), "marketing")).toBe(true);
    expect(isActionRequiredForDepartment(task("first-review-completed"), "marketing")).toBe(true);
    expect(isActionRequiredForDepartment(task("second-review-completed"), "marketing")).toBe(true);
    expect(isActionRequiredForDepartment(task("marketing-cancelled"), "marketing")).toBe(false);
    expect(countActionableReviews([task("waiting"), task("marketing-completed-approved"), task("marketing-cancelled")], "marketing")).toBe(2);
  });

  it("counts legal pending and in-progress documents only for legal users", () => {
    expect(isActionRequiredForDepartment(task("legal-pending"), "legal")).toBe(true);
    expect(isActionRequiredForDepartment(task("legal-in-progress"), "legal")).toBe(true);
    expect(isActionRequiredForDepartment(task("legal-review"), "legal")).toBe(true);
    expect(isActionRequiredForDepartment(task("legal-completed-approved"), "legal")).toBe(false);
    expect(isActionRequiredForDepartment(task("marketing-completed-rejected"), "legal")).toBe(false);
    expect(countActionableReviews([task("legal-pending"), task("legal-completed-rejected")], "legal")).toBe(1);
  });

  it("returns zero for no tasks and supports counts above 99", () => {
    expect(countActionableReviews([], "marketing")).toBe(0);
    const tasks = Array.from({ length: 100 }, (_, index) => task("waiting", `waiting-${index}`));
    expect(countActionableReviews(tasks, "marketing")).toBe(100);
  });
});
