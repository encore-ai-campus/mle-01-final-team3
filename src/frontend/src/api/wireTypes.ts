export type WireStage = "marketing" | "legal";
export type WireRunStatus = "queued" | "running" | "succeeded" | "failed";
export type WireDecision = "pending" | "approved" | "rejected";
export type WireLegalStatus =
  | "pending"
  | "in-progress"
  | "completed-approved"
  | "completed-rejected"
  | "completed-needs-revision"
  | "completed-continuable";
export type WireAllowedAction =
  | "request-legal-review"
  | "cancel-review"
  | "start-legal-review"
  | "complete-legal-approved"
  | "complete-legal-rejected"
  | "complete-legal-needs-revision"
  | "complete-legal-continuable"
  | "close-review";

export interface WireError {
  code: string;
  message: string;
  details: Record<string, string | number | boolean | null> | null;
}

export interface ExecutionStatusWire {
  reviewId: string;
  runId: string;
  stage: WireStage;
  runStatus: WireRunStatus;
  attempt: number;
  startedAt: string | null;
  completedAt: string | null;
  error: WireError | null;
}

export interface ReviewItemWire {
  submissionId: string;
  reviewId: string;
  title: string;
  reportRunId: string | null;
  stage: WireStage;
  decision: WireDecision;
  legalStatus: WireLegalStatus | null;
  reviewer: string | null;
  sentAt: string;
  decidedAt: string | null;
  allowedActions: WireAllowedAction[];
}

export interface ReviewListResponseWire {
  items: ReviewItemWire[];
  nextCursor: string | null;
}

export interface AttachmentResponseWire {
  attachmentId: string;
  filename: string;
  size: number;
}
