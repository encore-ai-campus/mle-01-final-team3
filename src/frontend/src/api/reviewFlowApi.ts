import { createApiError } from "./errors";
import type { RestClient } from "./restClient";

export type ProductCategory = "HEALTH_FUNCTIONAL_FOOD" | "GENERAL_FOOD" | "CHILDREN_PREFERRED_FOOD";
export type ReviewStage = "AI_SCREENING" | "RA_SUGGEST" | "RA_RECHECK";
export type RunStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface AttachmentUploadResult {
  attachmentId: string;
  filename: string;
  size: number;
}

export interface CreateReviewInput {
  title: string;
  productCategory: ProductCategory;
  text: string;
  attachmentIds?: string[];
}

export interface ReviewAccepted {
  reviewId: string;
  runId: string;
  stage: ReviewStage;
  runStatus: RunStatus;
  location: string | null;
}

export interface ReviewRunError {
  code: string;
  message: string;
  retryable: boolean;
}

export interface ReviewRun {
  reviewId: string;
  runId: string;
  stage: ReviewStage;
  runStatus: RunStatus;
  attempt: number;
  updatedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  error: ReviewRunError | null;
}

/** Raw detail is kept intact because report and finding fields are still evolving with the Agent contract. */
export type BackendReviewDetail = Record<string, unknown>;

export interface ReviewFlowApi {
  uploadAttachment(file: File, purpose?: string): Promise<AttachmentUploadResult>;
  createReview(input: CreateReviewInput, idempotencyKey?: string): Promise<ReviewAccepted>;
  getReview(reviewId: string): Promise<BackendReviewDetail>;
  getRun(runId: string): Promise<ReviewRun>;
  retryRun(runId: string, idempotencyKey?: string): Promise<ReviewAccepted>;
  requestRecommendation(reviewId: string, idempotencyKey?: string): Promise<ReviewAccepted>;
  recheckSuggestion(reviewId: string, runId: string, idempotencyKey?: string): Promise<ReviewAccepted>;
  dismissSuggestion(reviewId: string, runId: string): Promise<BackendReviewDetail>;
}

export class RestReviewFlowApi implements ReviewFlowApi {
  public constructor(private readonly client: RestClient) {}

  public async uploadAttachment(file: File, purpose = "AD_COPY"): Promise<AttachmentUploadResult> {
    const body = new FormData();
    body.append("file", file);
    body.append("purpose", purpose);
    const response = await this.client.request<unknown>("attachments", { method: "POST", body });
    const payload = requireRecord(response.data);
    if (!isString(payload.attachmentId) || !isString(payload.filename) || !isNumber(payload.size)) {
      throw invalidPayload(response.data);
    }
    return { attachmentId: payload.attachmentId, filename: payload.filename, size: payload.size };
  }

  public async createReview(input: CreateReviewInput, idempotencyKey = createIdempotencyKey()): Promise<ReviewAccepted> {
    const response = await this.client.request<unknown>("reviews", {
      method: "POST",
      body: { ...input, attachmentIds: input.attachmentIds ?? [] },
      headers: { "Idempotency-Key": idempotencyKey },
    });
    return parseAccepted(response.data, response.location);
  }

  public async getReview(reviewId: string): Promise<BackendReviewDetail> {
    return requireRecord((await this.client.request<unknown>(`reviews/${encodeURIComponent(reviewId)}`)).data);
  }

  public async getRun(runId: string): Promise<ReviewRun> {
    const payload = requireRecord((await this.client.request<unknown>(`review-runs/${encodeURIComponent(runId)}`)).data);
    if (!isString(payload.reviewId) || !isString(payload.runId) || !isReviewStage(payload.stage) || !isRunStatus(payload.runStatus) || !isNumber(payload.attempt) || !isString(payload.updatedAt) || !isStringOrNull(payload.startedAt) || !isStringOrNull(payload.finishedAt) || !isRunError(payload.error)) {
      throw invalidPayload(payload);
    }
    return payload as unknown as ReviewRun;
  }

  public async retryRun(runId: string, idempotencyKey = createIdempotencyKey()): Promise<ReviewAccepted> {
    return this.postAccepted(`review-runs/${encodeURIComponent(runId)}/retry`, idempotencyKey);
  }

  public async requestRecommendation(reviewId: string, idempotencyKey = createIdempotencyKey()): Promise<ReviewAccepted> {
    return this.postAccepted(`reviews/${encodeURIComponent(reviewId)}/ra-runs`, idempotencyKey);
  }

  public async recheckSuggestion(reviewId: string, runId: string, idempotencyKey = createIdempotencyKey()): Promise<ReviewAccepted> {
    return this.postAccepted(`reviews/${encodeURIComponent(reviewId)}/ra-runs/${encodeURIComponent(runId)}/recheck`, idempotencyKey);
  }

  public async dismissSuggestion(reviewId: string, runId: string): Promise<BackendReviewDetail> {
    return requireRecord((await this.client.request<unknown>(`reviews/${encodeURIComponent(reviewId)}/ra-runs/${encodeURIComponent(runId)}/dismiss`, { method: "POST" })).data);
  }

  private async postAccepted(path: string, idempotencyKey: string): Promise<ReviewAccepted> {
    const response = await this.client.request<unknown>(path, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
    });
    return parseAccepted(response.data, response.location);
  }
}

function parseAccepted(payload: unknown, location: string | null): ReviewAccepted {
  const record = requireRecord(payload);
  if (!isString(record.reviewId) || !isString(record.runId) || !isReviewStage(record.stage) || !isRunStatus(record.runStatus)) {
    throw invalidPayload(payload);
  }
  return { reviewId: record.reviewId, runId: record.runId, stage: record.stage, runStatus: record.runStatus, location };
}

function requireRecord(value: unknown): Record<string, unknown> {
  if (!isRecord(value)) throw invalidPayload(value);
  return value;
}

function invalidPayload(payload: unknown) {
  return createApiError("invalid-payload", "검토 API 응답 형식이 올바르지 않습니다.", payload);
}

function createIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return `frontend-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function isRecord(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null; }
function isString(value: unknown): value is string { return typeof value === "string"; }
function isNumber(value: unknown): value is number { return typeof value === "number" && Number.isFinite(value); }
function isStringOrNull(value: unknown): value is string | null { return value === null || isString(value); }
function isReviewStage(value: unknown): value is ReviewStage { return value === "AI_SCREENING" || value === "RA_SUGGEST" || value === "RA_RECHECK"; }
function isRunStatus(value: unknown): value is RunStatus { return value === "QUEUED" || value === "RUNNING" || value === "SUCCEEDED" || value === "FAILED"; }
function isRunError(value: unknown): value is ReviewRunError | null {
  return value === null || (isRecord(value) && isString(value.code) && isString(value.message) && typeof value.retryable === "boolean");
}
