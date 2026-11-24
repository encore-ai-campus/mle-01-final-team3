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
});
