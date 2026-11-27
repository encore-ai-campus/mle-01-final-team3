import { describe, expect, it, vi } from "vitest";
import { RestClient } from "./restClient";
import { RestReviewFlowApi } from "./reviewFlowApi";

const accepted = { reviewId: "revw_001", runId: "run_001", stage: "AI_SCREENING", runStatus: "QUEUED" };

describe("backend review flow contract", () => {
  it("uploads one attachment as multipart without overriding Content-Type", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ attachmentId: "att_001", filename: "광고.pdf", size: 12 }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const api = new RestReviewFlowApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));
    const file = new File(["pdf"], "광고.pdf", { type: "application/pdf" });

    await expect(api.uploadAttachment(file)).resolves.toEqual({ attachmentId: "att_001", filename: "광고.pdf", size: 12 });
    const [, init] = fetchImpl.mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({ Accept: "application/json" });
    expect(init?.body).toBeInstanceOf(FormData);
    expect((init?.body as FormData).get("file")).toBeInstanceOf(File);
    expect((init?.body as FormData).get("purpose")).toBe("AD_COPY");
  });

  it("creates a review with the exact backend body, idempotency key, and Location", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(accepted), {
        status: 202,
        headers: { "Content-Type": "application/json", Location: "/api/v1/review-runs/run_001" },
      }),
    );
    const api = new RestReviewFlowApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));

    await expect(api.createReview({
      title: "광고 문구",
      productCategory: "GENERAL_FOOD",
      text: "검토할 문구",
      attachmentIds: ["att_001"],
    }, "idem-create")).resolves.toMatchObject({ ...accepted, location: "/api/v1/review-runs/run_001" });
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/reviews",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ title: "광고 문구", productCategory: "GENERAL_FOOD", text: "검토할 문구", attachmentIds: ["att_001"] }),
        headers: expect.objectContaining({ "Idempotency-Key": "idem-create" }),
      }),
    );
  });

  it("uses the run endpoints and keeps uppercase statuses and structured errors", async () => {
    const run = {
      reviewId: "revw_001",
      runId: "run_001",
      stage: "AI_SCREENING",
      runStatus: "FAILED",
      attempt: 2,
      updatedAt: "2026-11-27T10:00:01+09:00",
      startedAt: "2026-11-27T10:00:01+09:00",
      finishedAt: "2026-11-27T10:03:01+09:00",
      error: { code: "AGENT_UNAVAILABLE", message: "Agent를 사용할 수 없습니다.", retryable: true },
    };
    const fetchImpl = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(JSON.stringify(run), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(accepted), { status: 202, headers: { "Content-Type": "application/json" } }));
    const api = new RestReviewFlowApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));

    await expect(api.getRun("run_001")).resolves.toEqual(run);
    await expect(api.retryRun("run_001", "idem-retry")).resolves.toMatchObject(accepted);
    expect(fetchImpl).toHaveBeenNthCalledWith(2, "http://localhost:8000/api/v1/review-runs/run_001/retry", expect.objectContaining({
      method: "POST",
      headers: expect.objectContaining({ "Idempotency-Key": "idem-retry" }),
    }));
  });

  it("calls recommendation, recheck, and dismiss with the documented paths", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockImplementation(async () => new Response(JSON.stringify(accepted), { status: 202, headers: { "Content-Type": "application/json" } }));
    const api = new RestReviewFlowApi(new RestClient({ baseUrl: "http://localhost:8000/api/v1", fetchImpl }));

    await api.requestRecommendation("revw_001", "idem-ra");
    await api.recheckSuggestion("revw_001", "run_ra", "idem-recheck");
    await api.dismissSuggestion("revw_001", "run_ra");

    expect(fetchImpl).toHaveBeenNthCalledWith(1, "http://localhost:8000/api/v1/reviews/revw_001/ra-runs", expect.objectContaining({ method: "POST" }));
    expect(fetchImpl).toHaveBeenNthCalledWith(2, "http://localhost:8000/api/v1/reviews/revw_001/ra-runs/run_ra/recheck", expect.objectContaining({ method: "POST" }));
    expect(fetchImpl).toHaveBeenNthCalledWith(3, "http://localhost:8000/api/v1/reviews/revw_001/ra-runs/run_ra/dismiss", expect.objectContaining({ method: "POST" }));
    expect(fetchImpl.mock.calls[0][1]).toMatchObject({ headers: expect.objectContaining({ "Idempotency-Key": "idem-ra" }) });
    expect(fetchImpl.mock.calls[1][1]).toMatchObject({ headers: expect.objectContaining({ "Idempotency-Key": "idem-recheck" }) });
    expect(fetchImpl.mock.calls[2][1]).not.toMatchObject({ headers: expect.objectContaining({ "Idempotency-Key": expect.anything() }) });
  });
});
