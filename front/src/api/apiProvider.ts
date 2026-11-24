import { ContractApiClient } from "./client";
import { createApiError, toApiError, type ApiError } from "./errors";
import type { ApiProviderOptions, DataProvider, ReviewQuery } from "../types/api";
import type {
  Account,
  DashboardSummary,
  DataState,
  DecisionInput,
  NotificationFeed,
  PasswordUpdateInput,
  PasswordUpdateResult,
  ReviewDetail,
  ReviewTask,
} from "../types/domain";

const notConfiguredMessage = "검증된 API 연결이 설정되지 않았습니다.";

export class ApiProvider implements DataProvider {
  private readonly client: ContractApiClient | null;

  public constructor(options: ApiProviderOptions = {}) {
    this.client = options.contract ? new ContractApiClient(options.contract) : null;
  }

  public getDashboard(): Promise<DataState<DashboardSummary>> {
    return this.run("getDashboard", () => this.client?.getDashboard(), parseDashboard);
  }

  public listReviews(query: ReviewQuery): Promise<DataState<ReviewTask[]>> {
    return this.run("listReviews", () => this.client?.listReviews(query), parseReviewList);
  }

  public getReviewDetail(reviewId: string): Promise<DataState<ReviewDetail>> {
    return this.run(
      "getReviewDetail",
      () => this.client?.getReviewDetail(reviewId),
      parseReviewDetail,
    );
  }

  public submitDecision(input: DecisionInput): Promise<DataState<ReviewDetail>> {
    return this.run(
      "submitDecision",
      () => this.client?.submitDecision(input),
      parseReviewDetail,
    );
  }

  public getAccount(): Promise<DataState<Account>> {
    return this.run("getAccount", () => this.client?.getAccount(), parseAccount);
  }

  public updatePassword(
    input: PasswordUpdateInput,
  ): Promise<DataState<PasswordUpdateResult>> {
    return this.run(
      "updatePassword",
      () => this.client?.updatePassword(input),
      parsePasswordUpdateResult,
    );
  }

  public listNotifications(): Promise<DataState<NotificationFeed>> {
    return this.run(
      "listNotifications",
      () => this.client?.listNotifications(),
      parseNotificationFeed,
    );
  }

  public markNotificationsRead(): Promise<DataState<NotificationFeed>> {
    return this.run(
      "markNotificationsRead",
      () => this.client?.markNotificationsRead(),
      parseNotificationFeed,
    );
  }

  private async run<T>(
    operation: string,
    request: () => Promise<unknown> | undefined,
    parse: (payload: unknown) => T,
  ): Promise<DataState<T>> {
    if (!this.client) {
      return { status: "not-configured", message: `${operation}: ${notConfiguredMessage}` };
    }

    try {
      const payload = await request();
      return { status: "ready", data: parse(payload) };
    } catch (error) {
      if (error instanceof Error && error.message.startsWith("검증된 API 작업")) {
        return { status: "not-configured", message: error.message };
      }

      const apiError = isApiError(error) ? error : toApiError(error);
      return { status: "error", error: apiError };
    }
  }
}

function parseDashboard(payload: unknown): DashboardSummary {
  if (!isRecord(payload) || !isNumber(payload.pendingCount) || !isNumber(payload.inProgressCount) || !isNumber(payload.completedTodayCount) || !Array.isArray(payload.tasks) || !Array.isArray(payload.recentReports)) {
    throw createApiError("invalid-payload", "대시보드 응답 형식이 올바르지 않습니다.", payload);
  }

  return {
    pendingCount: payload.pendingCount,
    inProgressCount: payload.inProgressCount,
    completedTodayCount: payload.completedTodayCount,
    tasks: parseReviewArray(payload.tasks),
    recentReports: parseReviewArray(payload.recentReports),
  };
}

function parseReviewList(payload: unknown): ReviewTask[] {
  if (!Array.isArray(payload)) {
    throw createApiError("invalid-payload", "검토 목록 응답 형식이 올바르지 않습니다.", payload);
  }

  return parseReviewArray(payload);
}

function parseReviewDetail(payload: unknown): ReviewDetail {
  if (!isRecord(payload) || !isString(payload.copy) || !Array.isArray(payload.attachments) || !isBoolean(payload.canDecide) || !isStringOrNull(payload.readOnlyReason) || !isStringOrNull(payload.decisionReason) || !isStringOrNull(payload.pdfUrl)) {
    throw createApiError("invalid-payload", "검토 상세 응답 형식이 올바르지 않습니다.", payload);
  }

  const task = parseReviewTask(payload);
  if (!payload.attachments.every(isString)) {
    throw createApiError("invalid-payload", "첨부파일 응답 형식이 올바르지 않습니다.", payload.attachments);
  }

  return {
    ...task,
    copy: payload.copy,
    attachments: payload.attachments,
    canDecide: payload.canDecide,
    readOnlyReason: payload.readOnlyReason,
    decisionReason: payload.decisionReason,
    pdfUrl: payload.pdfUrl,
  };
}

function parseAccount(payload: unknown): Account {
  if (!isRecord(payload) || !isString(payload.userId) || !isString(payload.name) || !isString(payload.email) || !isDepartment(payload.department) || !isUserRole(payload.role) || !isBoolean(payload.needsPasswordChange)) {
    throw createApiError("invalid-payload", "계정 응답 형식이 올바르지 않습니다.", payload);
  }

  return payload as Account;
}

function parsePasswordUpdateResult(payload: unknown): PasswordUpdateResult {
  if (!isRecord(payload) || !isString(payload.message)) {
    throw createApiError("invalid-payload", "비밀번호 변경 응답 형식이 올바르지 않습니다.", payload);
  }

  return { account: parseAccount(payload.account), message: payload.message };
}

function parseNotificationFeed(payload: unknown): NotificationFeed {
  if (!isRecord(payload) || !Array.isArray(payload.notifications)) {
    throw createApiError("invalid-payload", "알림 응답 형식이 올바르지 않습니다.", payload);
  }

  const notifications = payload.notifications.map((item) => {
    if (!isRecord(item) || !isString(item.id) || !isString(item.title) || !isString(item.message) || !isString(item.createdAt) || !isBoolean(item.read)) {
      throw createApiError("invalid-payload", "알림 항목 형식이 올바르지 않습니다.", item);
    }

    return item;
  });

  return { notifications };
}

function parseReviewArray(payload: unknown[]): ReviewTask[] {
  return payload.map(parseReviewTask);
}

function parseReviewTask(payload: unknown): ReviewTask {
  if (!isRecord(payload) || !isString(payload.id) || !isString(payload.title) || !isString(payload.advertiser) || !isString(payload.submittedAt) || !isReviewStatus(payload.status) || !isReviewJudgment(payload.judgment) || !isStringOrNull(payload.assignee) || !isStringOrNull(payload.processedAt) || !isStringOrNull(payload.ownerId)) {
    throw createApiError("invalid-payload", "검토 항목 응답 형식이 올바르지 않습니다.", payload);
  }

  return {
    id: payload.id,
    title: payload.title,
    advertiser: payload.advertiser,
    submittedAt: payload.submittedAt,
    status: payload.status,
    judgment: payload.judgment,
    assignee: payload.assignee,
    processedAt: payload.processedAt,
    ownerId: payload.ownerId,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function isStringOrNull(value: unknown): value is string | null {
  return value === null || isString(value);
}

function isReviewStatus(value: unknown): value is ReviewTask["status"] {
  return value === "waiting" || value === "in-progress" || value === "completed";
}

function isReviewJudgment(value: unknown): value is ReviewTask["judgment"] {
  return value === "pending" || value === "approved" || value === "rejected" || value === "hold";
}

function isDepartment(value: unknown): value is Account["department"] {
  return value === "legal" || value === "marketing" || value === "quality" || value === "unknown";
}

function isUserRole(value: unknown): value is Account["role"] {
  return value === "admin" || value === "reviewer" || value === "viewer";
}

function isApiError(value: unknown): value is ApiError {
  return isRecord(value) && (value.kind === "network" || value.kind === "http" || value.kind === "invalid-payload" || value.kind === "unknown");
}
