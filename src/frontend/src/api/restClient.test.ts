import { describe, expect, it, vi } from "vitest";
import { RestClient } from "./restClient";

describe("RestClient", () => {
  it("normalizes the base URL and includes session credentials for JSON requests", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new RestClient({
      baseUrl: "http://localhost:8000/api/v1/",
      fetchImpl,
    });

    const response = await client.request<{ ok: boolean }>("/reviews");

    expect(response.data).toEqual({ ok: true });
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/reviews",
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({ Accept: "application/json" }),
      }),
    );
  });

  it("adds JSON content headers and serializes a JSON body", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ id: "review-1" }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new RestClient({ baseUrl: "http://api.test/api/v1", fetchImpl });

    await client.request<{ id: string }>("reviews", {
      method: "POST",
      body: { title: "광고 문구" },
      headers: { "Idempotency-Key": "request-1" },
    });

    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api.test/api/v1/reviews",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ title: "광고 문구" }),
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "Idempotency-Key": "request-1",
        },
      }),
    );
  });

  it("does not overwrite the browser boundary for FormData bodies", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(null, { status: 201 }),
    );
    const client = new RestClient({ baseUrl: "http://api.test/api/v1", fetchImpl });
    const body = new FormData();
    body.append("purpose", "AD_COPY");

    await client.request("attachments", { method: "POST", body });

    expect(fetchImpl).toHaveBeenCalledWith(
      "http://api.test/api/v1/attachments",
      expect.objectContaining({
        body,
        headers: { Accept: "application/json" },
      }),
    );
  });

  it("returns a Blob response without trying to parse it as JSON", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response("pdf-content", {
        status: 200,
        headers: { "Content-Type": "application/pdf" },
      }),
    );
    const client = new RestClient({ baseUrl: "http://api.test/api/v1", fetchImpl });

    const response = await client.requestBlob("reviews/review-1/report.pdf");

    expect(response.data).toBeInstanceOf(Blob);
    expect(response.data.type).toBe("application/pdf");
    expect(response.data.size).toBeGreaterThan(0);
  });

  it("preserves the Location header from an accepted response", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ runId: "run-1" }), {
        status: 202,
        headers: {
          "Content-Type": "application/json",
          Location: "/api/v1/review-runs/run-1",
        },
      }),
    );
    const client = new RestClient({ baseUrl: "http://api.test/api/v1", fetchImpl });

    const response = await client.request<{ runId: string }>("reviews", { method: "POST" });

    expect(response.status).toBe(202);
    expect(response.location).toBe("/api/v1/review-runs/run-1");
  });

  it("converts a JSON error response into an ApiError", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({
        error: {
          code: "VALIDATION_ERROR",
          message: "검토 문구를 입력해 주세요.",
          fieldErrors: [{ field: "text", code: "REQUIRED" }],
        },
      }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new RestClient({ baseUrl: "http://api.test/api/v1", fetchImpl });

    await expect(client.request("reviews", { method: "POST" })).rejects.toMatchObject({
      kind: "http",
      statusCode: 422,
      message: "검토 문구를 입력해 주세요.",
      details: { code: "VALIDATION_ERROR", fieldErrors: [{ field: "text", code: "REQUIRED" }] },
    });
  });

  it("converts a network failure into a network ApiError", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockRejectedValue(new Error("연결 실패"));
    const client = new RestClient({ baseUrl: "http://api.test/api/v1", fetchImpl });

    await expect(client.request("reviews")).rejects.toMatchObject({
      kind: "network",
      message: "연결 실패",
    });
  });
});
