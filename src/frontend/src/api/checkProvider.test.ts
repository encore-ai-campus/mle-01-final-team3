import { describe, expect, it } from "vitest";
import { ApiCheckProvider, FixtureCheckProvider } from "./checkProvider";
import { FixtureProvider } from "./fixtureProvider";
import { createFixtureWorkflowStore } from "./fixtureWorkflowStore";

describe("CheckDataProvider", () => {
  it("does not claim API operations succeeded without a verified contract", async () => {
    const provider = new ApiCheckProvider();
    const input = {
      title: "광고 초안",
      productType: "general-food" as const,
      ingredient: "원료",
      channel: "상세페이지",
      copy: "광고 문구",
      attachments: [],
    };

    await expect(provider.getResult("check-1")).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.saveDraft(input)).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.startCheck(input)).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.getProgress("check-1")).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.requestRecommendation("check-1")).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.requestAdCheck(input)).resolves.toMatchObject({ status: "not-configured" });
  });

  it("provides an isolated fixture result and progress flow", async () => {
    const provider = new FixtureCheckProvider();
    const result = await provider.getResult("fixture-check-1");
    const progress = await provider.getProgress("fixture-check-1");

    expect(result.status).toBe("ready");
    if (result.status === "ready") {
      expect(result.data.findings.length).toBeGreaterThan(0);
      expect(result.data.reviewId).toBe("fixture-review-1");
    }
    expect(progress.status).toBe("ready");
    if (progress.status === "ready") {
      expect(progress.data.steps.some((step) => step.status === "in-progress")).toBe(true);
    }
  });

  it("uses a review-ready demo copy for the screenshot flow", async () => {
    const result = await new FixtureCheckProvider().getResult("fixture-check-1");

    expect(result).toMatchObject({ status: "ready", data: { title: "저당 에너지바 광고", reviewId: "fixture-review-1" } });
  });

  it("derives an approved fixture result from a compliant submitted copy", async () => {
    const provider = new FixtureCheckProvider();
    await provider.startCheck({ title: "안전 광고", productType: "general-food", ingredient: "원료", channel: "상세페이지", copy: "건강한 생활에 도움을 줄 수 있어요", attachments: [] });
    const result = await provider.getResult("fixture-check-1");

    expect(result).toMatchObject({ status: "ready", data: { marketingJudgment: "approved", findings: [{ severity: "safe" }] } });
  });

  it("returns a marketing judgment and recommendation for the fixture flow", async () => {
    const provider = new FixtureCheckProvider();
    const result = await provider.getResult("fixture-check-1");
    const recommendation = await provider.requestRecommendation("fixture-check-1");

    expect(result).toMatchObject({ status: "ready", data: { marketingJudgment: "rejected" } });
    expect(recommendation).toMatchObject({ status: "ready", data: { selectedRecommendation: "건강한 생활에 도움을 줄 수 있어요" } });
  });

  it("shares a marketing action with the review detail provider", async () => {
    const store = createFixtureWorkflowStore();
    const checkProvider = new FixtureCheckProvider("LG-1", store);
    const reviewProvider = new FixtureProvider("LG-1", undefined, store);
    await checkProvider.performMarketingAction({ checkId: "fixture-check-1", reviewId: "fixture-review-1", action: "request-legal-review" });

    const detail = await reviewProvider.getReviewDetail("fixture-review-1");
    expect(detail).toMatchObject({ status: "ready", data: { status: "legal-pending", canDecide: true } });
  });
});
