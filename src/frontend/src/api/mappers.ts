import { createApiError } from "./errors";
import type {
  AttachmentResponseWire,
  ExecutionStatusWire,
  ReviewItemWire,
  ReviewListResponseWire,
  WireAllowedAction,
  WireDecision,
  WireError,
  WireLegalStatus,
  WireStage,
} from "./wireTypes";
import type { ReviewJudgment, ReviewStatus, ReviewTask } from "../types/domain";

export interface ReviewTaskApiMetadata {
  submissionId: string;
  reportRunId: string | null;
  stage: WireStage;
  legalStatus: WireLegalStatus | null;
  decidedAt: string | null;
  allowedActions: WireAllowedAction[];
}

export type MappedReviewTask = ReviewTask & { api: ReviewTaskApiMetadata };

export function parseExecutionStatus(payload: unknown): ExecutionStatusWire {
  if (!isRecord(payload)) return invalid("Execution status must be an object", payload);

  return {
    reviewId: readString(payload.reviewId, "reviewId", payload),
    runId: readString(payload.runId, "runId", payload),
    stage: readEnum(payload.stage, ["marketing", "legal"], "stage", payload),
    runStatus: readEnum(payload.runStatus, ["queued", "running", "succeeded", "failed"], "runStatus", payload),
    attempt: readNonNegativeInteger(payload.attempt, "attempt", payload),
    startedAt: readNullableString(payload.startedAt, "startedAt", payload),
    completedAt: readNullableString(payload.completedAt, "completedAt", payload),
    error: payload.error === null ? null : parseWireError(payload.error, payload),
  };
}

export function parseReviewListResponse(payload: unknown): ReviewListResponseWire {
  if (!isRecord(payload) || !Array.isArray(payload.items)) {
    return invalid("Review list response must contain an items array", payload);
  }

  return {
    items: payload.items.map((item) => parseReviewItem(item)),
    nextCursor: readNullableString(payload.nextCursor, "nextCursor", payload),
  };
}

export function parseAttachmentResponse(payload: unknown): AttachmentResponseWire {
  if (!isRecord(payload)) return invalid("Attachment response must be an object", payload);

  const size = payload.size;
  if (typeof size !== "number" || !Number.isFinite(size) || size < 0) {
    return invalid("Attachment size must be a non-negative number", payload);
  }

  return {
    attachmentId: readString(payload.attachmentId, "attachmentId", payload),
    filename: readString(payload.filename, "filename", payload),
    size,
  };
}

export function mapReviewListResponse(payload: unknown): { items: MappedReviewTask[]; nextCursor: string | null } {
  const parsed = parseReviewListResponse(payload);
  return { items: parsed.items.map(mapReviewTask), nextCursor: parsed.nextCursor };
}

export function mapReviewTask(item: ReviewItemWire): MappedReviewTask {
  return {
    id: item.reviewId,
    title: item.title,
    advertiser: "",
    author: item.reviewer ?? "",
    category: "",
    submittedAt: item.sentAt,
    sentAt: item.sentAt,
    status: mapReviewStatus(item),
    judgment: mapReviewJudgment(item.decision),
    assignee: item.reviewer,
    processedAt: item.decidedAt,
    ownerId: null,
    api: {
      submissionId: item.submissionId,
      reportRunId: item.reportRunId,
      stage: item.stage,
      legalStatus: item.legalStatus,
      decidedAt: item.decidedAt,
      allowedActions: item.allowedActions,
    },
  };
}

function parseReviewItem(payload: unknown): ReviewItemWire {
  if (!isRecord(payload)) return invalid("Review item must be an object", payload);

  return {
    submissionId: readString(payload.submissionId, "submissionId", payload),
    reviewId: readString(payload.reviewId, "reviewId", payload),
    title: readString(payload.title, "title", payload),
    reportRunId: readNullableString(payload.reportRunId, "reportRunId", payload),
    stage: readEnum(payload.stage, ["marketing", "legal"], "stage", payload),
    decision: readEnum(payload.decision, ["pending", "approved", "rejected"], "decision", payload),
    legalStatus: readNullableEnum(
      payload.legalStatus,
      ["pending", "in-progress", "completed-approved", "completed-rejected", "completed-needs-revision", "completed-continuable"],
      "legalStatus",
      payload,
    ),
    reviewer: readNullableString(payload.reviewer, "reviewer", payload),
    sentAt: readString(payload.sentAt, "sentAt", payload),
    decidedAt: readNullableString(payload.decidedAt, "decidedAt", payload),
    allowedActions: readEnumArray(
      payload.allowedActions,
      ["request-legal-review", "cancel-review", "start-legal-review", "complete-legal-approved", "complete-legal-rejected", "complete-legal-needs-revision", "complete-legal-continuable", "close-review"],
      "allowedActions",
      payload,
    ),
  };
}

function parseWireError(payload: unknown, parent: unknown): WireError {
  if (!isRecord(payload)) return invalid("Execution error must be an object or null", parent);
  const details = payload.details;
  if (details !== null && !isFlatRecord(details)) return invalid("Execution error details must be a flat object or null", parent);
  return {
    code: readString(payload.code, "error.code", parent),
    message: readString(payload.message, "error.message", parent),
    details,
  };
}

function mapReviewStatus(item: ReviewItemWire): ReviewStatus {
  if (item.stage === "marketing") {
    if (item.decision === "approved") return "marketing-completed-approved";
    if (item.decision === "rejected") return "marketing-completed-rejected";
    return "waiting";
  }

  switch (item.legalStatus) {
    case "in-progress":
      return "legal-in-progress";
    case "completed-approved":
      return "legal-completed-approved";
    case "completed-rejected":
      return "legal-completed-rejected";
    case "completed-needs-revision":
      return "legal-completed-needs-revision";
    case "completed-continuable":
      return "legal-completed-continuable";
    case "pending":
    case null:
    default:
      return "legal-pending";
  }
}

function mapReviewJudgment(decision: WireDecision): ReviewJudgment {
  if (decision === "approved") return "approved";
  if (decision === "rejected") return "rejected";
  return "pending";
}

function readString(value: unknown, field: string, payload: unknown): string {
  if (typeof value !== "string" || value.length === 0) return invalid(`${field} must be a non-empty string`, payload);
  return value;
}

function readNullableString(value: unknown, field: string, payload: unknown): string | null {
  if (value !== null && typeof value !== "string") return invalid(`${field} must be a string or null`, payload);
  return value;
}

function readNonNegativeInteger(value: unknown, field: string, payload: unknown): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) return invalid(`${field} must be a non-negative integer`, payload);
  return value;
}

function readEnum<T extends string>(value: unknown, values: readonly T[], field: string, payload: unknown): T {
  if (typeof value !== "string" || !values.includes(value as T)) return invalid(`${field} has an unsupported value`, payload);
  return value as T;
}

function readNullableEnum<T extends string>(value: unknown, values: readonly T[], field: string, payload: unknown): T | null {
  return value === null ? null : readEnum(value, values, field, payload);
}

function readEnumArray<T extends string>(value: unknown, values: readonly T[], field: string, payload: unknown): T[] {
  if (!Array.isArray(value)) return invalid(`${field} must be an array`, payload);
  return value.map((item) => readEnum(item, values, field, payload));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isFlatRecord(value: unknown): value is Record<string, string | number | boolean | null> {
  return isRecord(value) && Object.values(value).every((item) => item === null || ["string", "number", "boolean"].includes(typeof item));
}

function invalid(message: string, details: unknown): never {
  throw createApiError("invalid-payload", message, details);
}
