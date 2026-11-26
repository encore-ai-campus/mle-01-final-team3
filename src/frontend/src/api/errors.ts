export type ApiErrorKind = "network" | "http" | "invalid-payload" | "unknown";

export interface ApiError {
  kind: ApiErrorKind;
  message: string;
  statusCode?: number;
  details?: unknown;
}

export function createApiError(
  kind: ApiErrorKind,
  message: string,
  details?: unknown,
  statusCode?: number,
): ApiError {
  return { kind, message, details, statusCode };
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof Error) {
    return createApiError("unknown", error.message, error);
  }

  return createApiError("unknown", "알 수 없는 API 오류가 발생했습니다.", error);
}
