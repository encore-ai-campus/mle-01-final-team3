import { createApiError, type ApiError } from "./errors";

export interface RestClientOptions {
  baseUrl: string;
  fetchImpl?: typeof fetch;
}

export interface RestRequestInit extends Omit<RequestInit, "body"> {
  body?: BodyInit | Record<string, unknown> | unknown[] | null;
}

export interface RestResponse<T> {
  data: T;
  status: number;
  headers: Headers;
  location: string | null;
}

export class RestClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  public constructor(options: RestClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  public request<T>(path: string, init: RestRequestInit = {}): Promise<RestResponse<T>> {
    return this.send<T>(path, init, "json");
  }

  public requestBlob(path: string, init: RestRequestInit = {}): Promise<RestResponse<Blob>> {
    return this.send<Blob>(path, init, "blob");
  }

  private async send<T>(
    path: string,
    init: RestRequestInit,
    responseType: "json" | "blob",
  ): Promise<RestResponse<T>> {
    const { body, headers: inputHeaders, ...requestInit } = init;
    const headers = normalizeHeaders(inputHeaders);
    headers.Accept ??= "application/json";

    let requestBody: BodyInit | undefined;
    if (isJsonBody(body)) {
      headers["Content-Type"] ??= "application/json";
      requestBody = JSON.stringify(body);
    } else if (body !== null && body !== undefined) {
      requestBody = body as BodyInit;
    }

    let response: Response;
    try {
      response = await this.fetchImpl(this.buildUrl(path), {
        ...requestInit,
        body: requestBody,
        credentials: "include",
        headers,
      });
    } catch (error) {
      throw createNetworkError(error);
    }

    const payload = await readResponsePayload(response, responseType);
    if (!response.ok) {
      throw createHttpError(response, payload);
    }

    return {
      data: payload as T,
      status: response.status,
      headers: response.headers,
      location: response.headers.get("Location"),
    };
  }

  private buildUrl(path: string): string {
    return `${this.baseUrl}/${path.replace(/^\/+/, "")}`;
  }
}

function normalizeHeaders(input: HeadersInit | undefined): Record<string, string> {
  if (!input) return {};
  if (input instanceof Headers) return Object.fromEntries(input.entries());
  if (Array.isArray(input)) return Object.fromEntries(input);
  return { ...input };
}

function isJsonBody(value: RestRequestInit["body"]): value is Record<string, unknown> | unknown[] {
  if (value === null || typeof value !== "object") return false;
  if (value instanceof FormData || value instanceof Blob || value instanceof ArrayBuffer || value instanceof URLSearchParams) {
    return false;
  }

  return true;
}

async function readResponsePayload(response: Response, responseType: "json" | "blob"): Promise<unknown> {
  if (response.status === 204 || response.status === 205) return null;
  if (responseType === "blob") return response.blob();

  const text = await response.text();
  if (!text.trim()) return null;

  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(text);
    } catch (error) {
      throw createApiError("invalid-payload", "API JSON 응답을 해석할 수 없습니다.", error, response.status);
    }
  }

  return text;
}

function createNetworkError(error: unknown): ApiError {
  const message = error instanceof Error ? error.message : "API 서버에 연결할 수 없습니다.";
  return createApiError("network", message, error);
}

function createHttpError(response: Response, payload: unknown): ApiError {
  const details = extractErrorDetails(payload);
  const message = isRecord(details) && typeof details.message === "string"
    ? details.message
    : `API 요청이 실패했습니다. (${response.status})`;

  return createApiError("http", message, details, response.status);
}

function extractErrorDetails(payload: unknown): unknown {
  if (isRecord(payload) && isRecord(payload.error)) return payload.error;
  return payload;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
