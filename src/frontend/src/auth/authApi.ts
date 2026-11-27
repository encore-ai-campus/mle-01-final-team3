import { createApiError } from "../api/errors";
import type { RestClient } from "../api/restClient";
import type { Account, PasswordUpdateInput } from "../types/domain";

export type BackendUserRole = "MARKETING" | "LEGAL" | "ADMIN";
export type LoginType = "STAFF" | "ADMIN";

export interface BackendUser {
  userId: string;
  name: string;
  email: string;
  role: BackendUserRole;
  mustChangePassword: boolean;
}

export interface LoginInput {
  email: string;
  password: string;
  loginType: LoginType;
}

export interface AuthApi {
  login(input: LoginInput): Promise<Account>;
  me(): Promise<Account>;
  changePassword(input: Pick<PasswordUpdateInput, "currentPassword" | "newPassword">): Promise<Account>;
  logout(): Promise<void>;
}

interface LoginResponse {
  user: Omit<BackendUser, "mustChangePassword">;
  mustChangePassword: boolean;
}

export class RestAuthApi implements AuthApi {
  public constructor(private readonly client: RestClient) {}

  public async login(input: LoginInput): Promise<Account> {
    const response = await this.client.request<LoginResponse>("auth/login", {
      method: "POST",
      body: { ...input },
    });
    if (!isRecord(response.data) || !isRecord(response.data.user)) {
      throw invalidPayload(response.data);
    }

    return mapBackendUser({
      ...response.data.user,
      mustChangePassword: response.data.mustChangePassword,
    });
  }

  public async me(): Promise<Account> {
    const response = await this.client.request<BackendUser>("me");
    return mapBackendUser(response.data);
  }

  public async changePassword(input: Pick<PasswordUpdateInput, "currentPassword" | "newPassword">): Promise<Account> {
    const response = await this.client.request<BackendUser>("me/password", {
      method: "PATCH",
      body: { currentPassword: input.currentPassword, newPassword: input.newPassword },
    });
    return mapBackendUser(response.data);
  }

  public async logout(): Promise<void> {
    await this.client.request<null>("auth/logout", { method: "POST" });
  }
}

export function mapBackendUser(payload: BackendUser): Account {
  if (
    !isRecord(payload) ||
    !isString(payload.userId) ||
    !isString(payload.name) ||
    !isString(payload.email) ||
    !isBackendRole(payload.role) ||
    typeof payload.mustChangePassword !== "boolean"
  ) {
    throw invalidPayload(payload);
  }

  const roleMapping: Record<BackendUserRole, Pick<Account, "department" | "role">> = {
    MARKETING: { department: "marketing", role: "reviewer" },
    LEGAL: { department: "legal", role: "reviewer" },
    ADMIN: { department: "unknown", role: "admin" },
  };

  return {
    userId: payload.userId,
    name: payload.name,
    email: payload.email,
    ...roleMapping[payload.role],
    needsPasswordChange: payload.mustChangePassword,
  };
}

function invalidPayload(payload: unknown) {
  return createApiError("invalid-payload", "인증 API 응답 형식이 올바르지 않습니다.", payload);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isBackendRole(value: unknown): value is BackendUserRole {
  return value === "MARKETING" || value === "LEGAL" || value === "ADMIN";
}
