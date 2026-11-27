export type ApiErrorKind = "network" | "http" | "invalid-payload" | "unknown";

export interface ApiError {
  kind: ApiErrorKind;
  message: string;
  statusCode?: number;
  details?: unknown;
  code?: string;
  retryable?: boolean;
  requestId?: string;
  fieldErrors?: unknown[];
}

export function createApiError(
  kind: ApiErrorKind,
  message: string,
  details?: unknown,
  statusCode?: number,
): ApiError {
  const metadata = isRecord(details) ? details : {};
  return {
    kind,
    message,
    details,
    statusCode,
    code: typeof metadata.code === "string" ? metadata.code : undefined,
    retryable: typeof metadata.retryable === "boolean" ? metadata.retryable : undefined,
    requestId: typeof metadata.requestId === "string" ? metadata.requestId : undefined,
    fieldErrors: Array.isArray(metadata.fieldErrors) ? metadata.fieldErrors : undefined,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof Error) {
    return createApiError("unknown", error.message, error);
  }

  return createApiError("unknown", "알 수 없는 API 오류가 발생했습니다.", error);
}
