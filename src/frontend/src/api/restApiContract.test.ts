import { describe, expect, it, vi } from "vitest";
import { ApiProvider } from "./apiProvider";
import { createRestApiContract } from "./restApiContract";
import { RestClient } from "./restClient";

const reviewItem = {
  submissionId: "submission-1",
  reviewId: "review-1",
  title: "광고 문구",
  reportRunId: "run-1",
  stage: "marketing",
  decision: "approved",
  legalStatus: null,
  reviewer: "마케팅 담당자",
  sentAt: "2026-11-26T09:00:00Z",
  decidedAt: "2026-11-26T09:05:00Z",
  allowedActions: ["request-legal-review"],
};

describe("RestApiContract", () => {
  it("uses an injected list path and maps the wire response for ApiProvider", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [reviewItem], nextCursor: "cursor-2" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const contract = createRestApiContract({
      client: new RestClient({ baseUrl: "https://api.example.test", fetchImpl }),
      routes: { listReviews: "/confirmed/reviews" },
    });

    await expect(contract?.listReviews?.({ search: "봄 광고", processingStatus: "waiting" })).resolves.toMatchObject([
      {
        id: "review-1",
        title: "광고 문구",
        status: "marketing-completed-approved",
        judgment: "approved",
      },
    ]);
    expect(fetchImpl).toHaveBeenCalledWith(
      "https://api.example.test/confirmed/reviews?search=%EB%B4%84+%EA%B4%91%EA%B3%A0&processingStatus=waiting",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("does not create a contract or request when the route is blank", () => {
    const fetchImpl = vi.fn<typeof fetch>();
    const contract = createRestApiContract({
      client: new RestClient({ baseUrl: "https://api.example.test", fetchImpl }),
      routes: { listReviews: "   " },
    });

    expect(contract).toBeNull();
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("feeds the mapped list into the existing ApiProvider contract boundary", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [reviewItem], nextCursor: null }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const contract = createRestApiContract({
      client: new RestClient({ baseUrl: "https://api.example.test", fetchImpl }),
      routes: { listReviews: "/confirmed/reviews" },
    });
    const provider = new ApiProvider({ contract: contract ?? undefined });

    const result = await provider.listReviews({});

    expect(result).toMatchObject({
      status: "ready",
      data: [{ id: "review-1", status: "marketing-completed-approved" }],
    });
  });
});
