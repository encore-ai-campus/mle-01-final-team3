import type { ReviewTask } from "../types/domain";

export type WorkDepartment = "marketing" | "legal";

const actionableStatuses: Record<WorkDepartment, ReadonlySet<ReviewTask["status"]>> = {
  marketing: new Set(["waiting", "in-progress", "first-review-completed", "second-review-completed", "marketing-completed-approved", "marketing-completed-rejected"]),
  legal: new Set(["legal-pending", "legal-in-progress", "legal-review"]),
};

export function isActionRequiredForDepartment(task: ReviewTask, department: WorkDepartment): boolean {
  return actionableStatuses[department].has(task.status);
}

export function countActionableReviews(tasks: ReviewTask[], department: WorkDepartment): number {
  return tasks.filter((task) => isActionRequiredForDepartment(task, department)).length;
}
