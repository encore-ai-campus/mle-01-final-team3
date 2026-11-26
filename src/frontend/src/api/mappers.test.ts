import { describe, expect, it } from "vitest";
import {
  mapReviewListResponse,
  parseAttachmentResponse,
  parseExecutionStatus,
  parseReviewListResponse,
} from "./mappers";

const reviewItem = {
  submissionId: "submission-1",
  reviewId: "review-1",
  title: "광고 문구",
  reportRunId: "run-1",
  stage: "legal",
  decision: "pending",
  legalStatus: "in-progress",
  reviewer: "법무 담당자",
  sentAt: "2026-11-26T09:00:00Z",
  decidedAt: null,
  allowedActions: ["complete-legal-approved", "complete-legal-rejected", "close-review"],
};

describe("backend response mappers", () => {
  it("validates and maps a paginated review response without losing API metadata", () => {
    const parsed = parseReviewListResponse({ items: [reviewItem], nextCursor: "cursor-2" });
    const mapped = mapReviewListResponse({ items: [reviewItem], nextCursor: "cursor-2" });

    expect(parsed.items[0]?.reviewId).toBe("review-1");
    expect(mapped.nextCursor).toBe("cursor-2");
    expect(mapped.items[0]).toMatchObject({
      id: "review-1",
      title: "광고 문구",
      author: "법무 담당자",
      status: "legal-in-progress",
      judgment: "pending",
      api: {
        submissionId: "submission-1",
        reportRunId: "run-1",
        allowedActions: ["complete-legal-approved", "complete-legal-rejected", "close-review"],
      },
    });
  });

  it("validates execution status, including nullable error and timestamps", () => {
    expect(
      parseExecutionStatus({
        reviewId: "review-1",
        runId: "run-1",
        stage: "marketing",
        runStatus: "succeeded",
        attempt: 1,
        startedAt: "2026-11-26T09:00:00Z",
        completedAt: "2026-11-26T09:00:05Z",
        error: null,
      }),
    ).toMatchObject({ runStatus: "succeeded", error: null });
  });

  it("validates attachment metadata", () => {
    expect(parseAttachmentResponse({ attachmentId: "attachment-1", filename: "brief.pdf", size: 42 })).toEqual({
      attachmentId: "attachment-1",
      filename: "brief.pdf",
      size: 42,
    });
  });

  it("converts malformed wire responses into invalid-payload errors", () => {
    expectInvalidPayload(() => parseReviewListResponse({ items: [{ ...reviewItem, stage: "unknown" }], nextCursor: null }));
    expectInvalidPayload(() => parseExecutionStatus({ reviewId: "review-1" }));
    expectInvalidPayload(() => parseAttachmentResponse({ attachmentId: "attachment-1", filename: "brief.pdf", size: -1 }));
  });
});

function expectInvalidPayload(callback: () => unknown): void {
  try {
    callback();
    throw new Error("Expected an invalid-payload error");
  } catch (error) {
    expect(error).toMatchObject({ kind: "invalid-payload" });
  }
}
