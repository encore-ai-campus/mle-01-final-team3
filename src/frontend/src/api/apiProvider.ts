import { ContractApiClient } from "./client";
import { createApiError, toApiError, type ApiError } from "./errors";
import type { RestClient } from "./restClient";
import type { ApiProviderOptions, DataProvider, ReviewQuery } from "../types/api";
import type {
  Account,
  CheckFinding,
  DashboardSummary,
  DataState,
  DecisionInput,
  Employee,
  EmployeeDeleteResult,
  EmployeeInput,
  NotificationFeed,
  PasswordUpdateInput,
  PasswordUpdateResult,
  ReviewDetail,
  ReviewReport,
  ReviewReportStage,
  ReviewTask,
  ReviewUpdateInput,
  ReviewWorkflowActionInput,
} from "../types/domain";

const notConfiguredMessage = "검증된 API 연결이 설정되지 않았습니다.";

export class ApiProvider implements DataProvider {
  private readonly client: ContractApiClient | null;
  private readonly restClient: RestClient | null;
  private readonly authApi: ApiProviderOptions["authApi"];
  public readonly reviewFlow: NonNullable<ApiProviderOptions["reviewFlow"]> | undefined;

  public constructor(options: ApiProviderOptions = {}) {
    this.client = options.contract ? new ContractApiClient(options.contract) : null;
    this.restClient = options.restClient ?? null;
    this.reviewFlow = options.reviewFlow ?? undefined;
    this.authApi = options.authApi ?? null;
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
    if (this.authApi) return this.run("getAccount", () => this.authApi?.me(), parseAccount, true);
    return this.run("getAccount", () => this.client?.getAccount(), parseAccount);
  }

  public updatePassword(
    input: PasswordUpdateInput,
  ): Promise<DataState<PasswordUpdateResult>> {
    if (this.authApi) {
      return this.run(
        "updatePassword",
        async () => ({ account: await this.authApi?.changePassword(input), message: "비밀번호가 변경되었습니다." }),
        parsePasswordUpdateResult,
        true,
      );
    }
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

  public listEmployees(search?: string): Promise<DataState<Employee[]>> { return this.run("listEmployees", () => this.client?.listEmployees(search), parseEmployeeList); }
  public getEmployee(employeeId: string): Promise<DataState<Employee>> { return this.run("getEmployee", () => this.client?.getEmployee(employeeId), parseEmployee); }
  public createEmployee(input: EmployeeInput): Promise<DataState<Employee>> { return this.run("createEmployee", () => this.client?.createEmployee(input), parseEmployee); }
  public updateEmployee(employeeId: string, input: EmployeeInput): Promise<DataState<Employee>> { return this.run("updateEmployee", () => this.client?.updateEmployee(employeeId, input), parseEmployee); }
  public deleteEmployee(employeeId: string): Promise<DataState<EmployeeDeleteResult>> { return this.run("deleteEmployee", () => this.client?.deleteEmployee(employeeId), parseEmployeeDeleteResult); }
  public getReviewReport(reviewId: string, stage: ReviewReportStage): Promise<DataState<ReviewReport>> { return this.run("getReviewReport", () => this.client?.getReviewReport(reviewId, stage), parseReviewReport); }
  public updateReview(reviewId: string, input: ReviewUpdateInput): Promise<DataState<ReviewTask>> { return this.run("updateReview", () => this.client?.updateReview(reviewId, input), parseReviewTask); }
  public performReviewAction(input: ReviewWorkflowActionInput): Promise<DataState<ReviewDetail>> { return this.run("performReviewAction", () => this.client?.performReviewAction(input), parseReviewDetail); }

  private async run<T>(
    operation: string,
    request: () => Promise<unknown> | undefined,
    parse: (payload: unknown) => T,
    configured = this.client !== null,
  ): Promise<DataState<T>> {
    if (!configured) {
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
  if (!isRecord(payload) || !isString(payload.copy) || !Array.isArray(payload.attachments) || !isBoolean(payload.canDecide) || !isStringOrNull(payload.readOnlyReason) || !isStringOrNull(payload.decisionReason) || !isStringOrNull(payload.pdfUrl) || (payload.legalOpinion !== undefined && !isStringOrNull(payload.legalOpinion))) {
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
    findings: payload.findings === undefined ? [] : parseCheckFindings(payload.findings),
    evidencePath: payload.evidencePath === undefined ? [] : parseStringArray(payload.evidencePath, "근거 경로"),
    canDecide: payload.canDecide,
    readOnlyReason: payload.readOnlyReason,
    decisionReason: payload.decisionReason,
    legalOpinion: payload.legalOpinion === undefined ? null : payload.legalOpinion,
    pdfUrl: payload.pdfUrl,
    report: payload.report === undefined ? undefined : parseReviewReport(payload.report),
  };
}

function parseReviewReport(payload: unknown): ReviewReport {
  if (!isRecord(payload) || !isReviewReportStage(payload.stage) || !isString(payload.title) || !isString(payload.summary) || !Array.isArray(payload.sections) || !Array.isArray(payload.references)) {
    throw createApiError("invalid-payload", "검토 보고서 응답 형식이 올바르지 않습니다.", payload);
  }
  const sections = payload.sections.map((item) => {
    if (!isRecord(item) || !isString(item.label) || !isString(item.value)) throw createApiError("invalid-payload", "검토 보고서 항목 형식이 올바르지 않습니다.", item);
    return { label: item.label, value: item.value };
  });
  const references = payload.references.map((item) => {
    if (!isRecord(item) || !isString(item.id) || !isString(item.label) || !isReviewReportStage(item.stage)) throw createApiError("invalid-payload", "참조 문서 형식이 올바르지 않습니다.", item);
    return { id: item.id, label: item.label, stage: item.stage };
  });
  return { stage: payload.stage, title: payload.title, summary: payload.summary, sections, references };
}

function parseCheckFindings(payload: unknown): CheckFinding[] {
  if (!Array.isArray(payload)) {
    throw createApiError("invalid-payload", "검토 근거 응답 형식이 올바르지 않습니다.", payload);
  }

  return payload.map((item) => {
    if (!isRecord(item) || !isString(item.id) || !isCheckFindingSeverity(item.severity) || !isString(item.phrase) || !isString(item.reason) || !isStringOrNull(item.allowedCopy) || !Array.isArray(item.evidence) || !Array.isArray(item.alternatives) || !item.alternatives.every(isString)) {
      throw createApiError("invalid-payload", "검토 근거 항목 형식이 올바르지 않습니다.", item);
    }

    const evidence = item.evidence.map((reference) => {
      if (!isRecord(reference) || !isString(reference.label) || !isString(reference.source) || !isStringOrNull(reference.href)) {
        throw createApiError("invalid-payload", "검토 근거 출처 형식이 올바르지 않습니다.", reference);
      }
      return { label: reference.label, source: reference.source, href: reference.href };
    });

    return { id: item.id, severity: item.severity, phrase: item.phrase, reason: item.reason, allowedCopy: item.allowedCopy, evidence, alternatives: item.alternatives };
  });
}

function parseStringArray(payload: unknown, label: string): string[] {
  if (!Array.isArray(payload) || !payload.every(isString)) {
    throw createApiError("invalid-payload", `${label} 응답 형식이 올바르지 않습니다.`, payload);
  }
  return payload;
}

function parseAccount(payload: unknown): Account {
  if (!isRecord(payload) || !isString(payload.userId) || !isString(payload.name) || !isString(payload.email) || !isDepartment(payload.department) || !isUserRole(payload.role) || !isBoolean(payload.needsPasswordChange)) {
    throw createApiError("invalid-payload", "계정 응답 형식이 올바르지 않습니다.", payload);
  }

  return {
    userId: payload.userId,
    name: payload.name,
    email: payload.email,
    department: payload.department,
    role: payload.role,
    needsPasswordChange: payload.needsPasswordChange,
  };
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

    return {
      id: item.id,
      title: item.title,
      message: item.message,
      createdAt: item.createdAt,
      read: item.read,
    };
  });

  return { notifications };
}

function parseReviewArray(payload: unknown[]): ReviewTask[] {
  return payload.map(parseReviewTask);
}

function parseReviewTask(payload: unknown): ReviewTask {
  const title = isRecord(payload) && isString(payload.title) ? payload.title : isRecord(payload) && isString(payload.adName) ? payload.adName : null;
  const sentAt = isRecord(payload) && isString(payload.sentAt) ? payload.sentAt : isRecord(payload) && isString(payload.submittedAt) ? payload.submittedAt : null;
  if (!isRecord(payload) || !isString(payload.id) || !title || !sentAt || !isReviewStatus(payload.status) || !isReviewJudgment(payload.judgment) || !isStringOrNull(payload.assignee) || !isStringOrNull(payload.processedAt) || !isStringOrNull(payload.ownerId)) {
    throw createApiError("invalid-payload", "검토 항목 응답 형식이 올바르지 않습니다.", payload);
  }

  return {
    id: payload.id,
    title,
    advertiser: isString(payload.advertiser) ? payload.advertiser : "미지정",
    author: isString(payload.author) ? payload.author : payload.assignee ?? "미지정",
    category: isString(payload.category) ? payload.category : "미분류",
    submittedAt: sentAt,
    sentAt,
    status: payload.status,
    judgment: payload.judgment,
    assignee: payload.assignee,
    processedAt: payload.processedAt,
    ownerId: payload.ownerId,
    copy: isString(payload.copy) ? payload.copy : undefined,
  };
}

function parseEmployeeList(payload: unknown): Employee[] {
  if (!Array.isArray(payload)) throw createApiError("invalid-payload", "직원 목록 응답 형식이 올바르지 않습니다.", payload);
  return payload.map(parseEmployee);
}

function parseEmployee(payload: unknown): Employee {
  if (!isRecord(payload) || !isString(payload.id) || !isString(payload.name) || !isEmployeeDepartment(payload.department) || !isString(payload.email) || !isString(payload.phone) || !isEmployeeStatus(payload.status)) throw createApiError("invalid-payload", "직원 응답 형식이 올바르지 않습니다.", payload);
  return { id: payload.id, name: payload.name, department: payload.department, email: payload.email, phone: payload.phone, status: payload.status };
}

function parseEmployeeDeleteResult(payload: unknown): EmployeeDeleteResult {
  if (!isRecord(payload) || !isString(payload.employeeId)) throw createApiError("invalid-payload", "직원 삭제 응답 형식이 올바르지 않습니다.", payload);
  return { employeeId: payload.employeeId };
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
  return value === "waiting" || value === "in-progress" || value === "completed" || value === "first-review-completed" || value === "second-review-completed" || value === "legal-review" || value === "marketing-completed-approved" || value === "marketing-completed-rejected" || value === "legal-pending" || value === "legal-in-progress" || value === "legal-completed-approved" || value === "legal-completed-rejected" || value === "legal-completed-needs-revision" || value === "legal-completed-continuable" || value === "marketing-cancelled";
}

function isReviewReportStage(value: unknown): value is ReviewReportStage { return value === "first-review" || value === "second-review" || value === "legal-review" || value === "completed" || value === "marketing" || value === "legal"; }
function isEmployeeDepartment(value: unknown): value is Employee["department"] { return value === "marketing" || value === "legal"; }
function isEmployeeStatus(value: unknown): value is Employee["status"] { return value === "active" || value === "inactive"; }

function isReviewJudgment(value: unknown): value is ReviewTask["judgment"] {
  return value === "pending" || value === "approved" || value === "rejected" || value === "hold";
}

function isCheckFindingSeverity(value: unknown): value is CheckFinding["severity"] {
  return value === "violation-suspected" || value === "ambiguous" || value === "safe";
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
