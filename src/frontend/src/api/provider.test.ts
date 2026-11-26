import { describe, expect, it } from "vitest";
import { ApiProvider } from "./apiProvider";
import { FixtureProvider } from "./fixtureProvider";

describe("data providers", () => {
  it("returns not-configured when no verified API contract is supplied", async () => {
    const result = await new ApiProvider().getDashboard();

    expect(result.status).toBe("not-configured");
  });

  it("maps malformed API payloads to a typed error", async () => {
    const provider = new ApiProvider({
      contract: {
        getDashboard: async () => ({ unexpected: true }),
      },
    });

    const result = await provider.getDashboard();

    expect(result.status).toBe("error");
    if (result.status === "error") {
      expect(result.error.kind).toBe("invalid-payload");
    }
  });

  it("returns the selected Artifact scenario from the fixture provider", async () => {
    const provider = new FixtureProvider("LG-34");

    const result = await provider.listNotifications();

    expect(result.status).toBe("ready");
    if (result.status === "ready") {
      expect(result.data.scenarioId).toBe("LG-34");
    }
  });

  it("keeps the submitted reason available when a decision fails", async () => {
    const provider = new FixtureProvider("LG-22");
    const reason = "광고 문구의 확인이 필요합니다.";

    const result = await provider.submitDecision({
      reviewId: "fixture-review-22",
      decision: "rejected",
      reason,
    });

    expect(result.status).toBe("error");
    if (result.status === "error") {
      expect(result.error.details).toEqual({ reason });
    }
  });

  it("provides screenshot-oriented dashboard data and status entry points", async () => {
    const dashboard = await new FixtureProvider("LG-1").getDashboard();
    const waitingReviews = await new FixtureProvider("LG-5").listReviews({});
    const inProgressReviews = await new FixtureProvider("LG-6").listReviews({});

    expect(dashboard).toMatchObject({ status: "ready", data: { pendingCount: 14, inProgressCount: 9, completedTodayCount: 3 } });
    expect(waitingReviews.status).toBe("ready");
    expect(inProgressReviews.status).toBe("ready");
    if (waitingReviews.status === "ready" && inProgressReviews.status === "ready") {
      expect(waitingReviews.data[0]?.status).toBe("waiting");
      expect(inProgressReviews.data[0]?.status).toBe("in-progress");
    }
  });

  it("updates only editable review fields and persists workflow actions", async () => {
    const provider = new FixtureProvider("LG-1");
    const updated = await provider.updateReview("fixture-review-1", { title: "수정된 광고", category: "일반식품", copy: "수정된 상세 내용" });
    const approved = await provider.performReviewAction({ reviewId: "fixture-review-1", action: "request-second-review" });
    const detail = await provider.getReviewDetail("fixture-review-1");

    expect(updated).toMatchObject({ status: "ready", data: { title: "수정된 광고", category: "일반식품" } });
    expect(approved).toMatchObject({ status: "ready", data: { status: "second-review-completed", judgment: "approved" } });
    expect(detail).toMatchObject({ status: "ready", data: { title: "수정된 광고", copy: "수정된 상세 내용", status: "second-review-completed", judgment: "approved" } });
  });

  it("uses the marketing/legal status flow and two report types", async () => {
    const provider = new FixtureProvider("LG-1");

    const marketingRejected = await provider.getReviewDetail("fixture-review-1");
    expect(marketingRejected).toMatchObject({ status: "ready", data: { status: "marketing-completed-rejected", judgment: "rejected" } });

    const cancelled = await provider.performReviewAction({ reviewId: "fixture-review-1", action: "cancel-review", role: "marketing" });
    expect(cancelled).toMatchObject({ status: "ready", data: { status: "marketing-cancelled" } });

    const marketingApproved = await provider.getReviewDetail("fixture-review-2");
    expect(marketingApproved).toMatchObject({ status: "ready", data: { status: "marketing-completed-approved", judgment: "approved" } });
    await provider.performReviewAction({ reviewId: "fixture-review-2", action: "request-legal-review", role: "marketing" });
    const pending = await provider.getReviewDetail("fixture-review-2");
    expect(pending).toMatchObject({ status: "ready", data: { status: "legal-pending" } });

    const forbidden = await provider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-approved", role: "marketing", legalOpinion: "검토 의견" });
    expect(forbidden).toMatchObject({ status: "error" });

    const missingOpinion = await provider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-approved", role: "legal", legalOpinion: "   " });
    expect(missingOpinion).toMatchObject({ status: "error" });

    const approved = await provider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-approved", role: "legal", legalOpinion: "표현상 문제가 없어 승인합니다." });
    expect(approved).toMatchObject({ status: "ready", data: { status: "legal-completed-approved", legalOpinion: "표현상 문제가 없어 승인합니다." } });

    const report = await provider.getReviewReport("fixture-review-2", "legal");
    expect(report).toMatchObject({ status: "ready", data: { title: "[법무]광고 문구 검토 보고서", stage: "legal" } });
    if (report.status === "ready") expect(report.data.references).toEqual([{ id: "fixture-review-2", label: "[마케팅]광고 문구 검토 보고서", stage: "marketing" }]);
  });

  it("keeps a legal review in progress when a legal user closes it", async () => {
    const provider = new FixtureProvider("LG-1");

    const result = await provider.performReviewAction({ reviewId: "fixture-review-3", action: "close-review", role: "legal" });

    expect(result).toMatchObject({ status: "ready", data: { status: "legal-in-progress" } });
  });

  it("records legal review outcomes for revision or continuation", async () => {
    const invalidSourceProvider = new FixtureProvider("LG-1");
    const invalidSource = await invalidSourceProvider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-continuable", role: "legal", legalOpinion: "아직 법무 검토 대상이 아닙니다." });
    expect(invalidSource).toMatchObject({ status: "error" });

    const needsRevisionProvider = new FixtureProvider("LG-1");
    await needsRevisionProvider.performReviewAction({ reviewId: "fixture-review-2", action: "request-legal-review", role: "marketing" });

    const forbidden = await needsRevisionProvider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-needs-revision", role: "marketing", legalOpinion: "보완이 필요합니다." });
    expect(forbidden).toMatchObject({ status: "error" });

    const missingOpinion = await needsRevisionProvider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-needs-revision", role: "legal", legalOpinion: "   " });
    expect(missingOpinion).toMatchObject({ status: "error" });

    const needsRevision = await needsRevisionProvider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-needs-revision", role: "legal", legalOpinion: "보완이 필요합니다." });
    expect(needsRevision).toMatchObject({ status: "ready", data: { status: "legal-completed-needs-revision", judgment: "rejected", legalOpinion: "보완이 필요합니다." } });

    const continuableProvider = new FixtureProvider("LG-1");
    await continuableProvider.performReviewAction({ reviewId: "fixture-review-2", action: "request-legal-review", role: "marketing" });
    const continuable = await continuableProvider.performReviewAction({ reviewId: "fixture-review-2", action: "complete-legal-continuable", role: "legal", legalOpinion: "진행 가능합니다." });
    expect(continuable).toMatchObject({ status: "ready", data: { status: "legal-completed-continuable", judgment: "approved", legalOpinion: "진행 가능합니다." } });
  });
});
