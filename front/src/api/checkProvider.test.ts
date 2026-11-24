import { describe, expect, it } from "vitest";
import { ApiCheckProvider, FixtureCheckProvider } from "./checkProvider";

describe("CheckDataProvider", () => {
  it("does not claim API operations succeeded without a verified contract", async () => {
    const provider = new ApiCheckProvider();
    const input = {
      title: "광고 초안",
      productType: "general-food" as const,
      ingredient: "원료",
      channel: "상세페이지",
      copy: "광고 문구",
    };

    await expect(provider.getResult("check-1")).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.saveDraft(input)).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.startCheck(input)).resolves.toMatchObject({ status: "not-configured" });
    await expect(provider.getProgress("check-1")).resolves.toMatchObject({ status: "not-configured" });
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
});
