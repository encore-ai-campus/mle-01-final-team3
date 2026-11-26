import { describe, expect, it } from "vitest";
import { createFixtureWorkflowStore } from "./fixtureWorkflowStore";
import type { CheckResult, ReviewDetail } from "../types/domain";

const review: ReviewDetail = {
  id: "review-1",
  title: "테스트 광고",
  advertiser: "테스트 식품",
  author: "테스트 담당자",
  category: "일반식품",
  submittedAt: "2026-11-25 09:00",
  sentAt: "2026-11-25 09:10",
  status: "marketing-completed-approved",
  judgment: "approved",
  assignee: "테스트 담당자",
  processedAt: null,
  ownerId: "user-1",
  copy: "안전한 테스트 문구입니다.",
  attachments: [],
  canDecide: false,
  readOnlyReason: null,
  decisionReason: null,
  pdfUrl: null,
  legalOpinion: null,
  report: undefined,
};

const result: CheckResult = {
  id: "check-1",
  title: "테스트 광고",
  productType: "general-food",
  ingredient: "테스트 원료",
  channel: "상세페이지",
  copy: "안전한 테스트 문구입니다.",
  attachments: [],
  findings: [],
  reviewId: "review-1",
  nextStep: "법무팀 검토를 요청합니다.",
  marketingJudgment: "approved",
};

describe("FixtureWorkflowStore", () => {
  it("keeps a review and its linked check result available to both providers", () => {
    const store = createFixtureWorkflowStore();

    store.saveReview(review);
    store.saveCheckResult(result);

    expect(store.getReview("review-1")).toEqual(review);
    expect(store.getCheckResult("check-1")).toEqual(result);
    expect(store.getCheckResult("check-1")?.reviewId).toBe(store.getReview("review-1")?.id);
  });
});
