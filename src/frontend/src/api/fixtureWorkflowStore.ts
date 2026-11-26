import type { CheckResult, ReviewDetail } from "../types/domain";

export interface FixtureWorkflowStore {
  getReview(reviewId: string): ReviewDetail | undefined;
  saveReview(detail: ReviewDetail): void;
  getCheckResult(checkId: string): CheckResult | undefined;
  saveCheckResult(result: CheckResult): void;
}

export function createFixtureWorkflowStore(): FixtureWorkflowStore {
  const reviews = new Map<string, ReviewDetail>();
  const checks = new Map<string, CheckResult>();

  return {
    getReview: (reviewId) => reviews.get(reviewId),
    saveReview: (detail) => reviews.set(detail.id, detail),
    getCheckResult: (checkId) => checks.get(checkId),
    saveCheckResult: (result) => checks.set(result.id, result),
  };
}
