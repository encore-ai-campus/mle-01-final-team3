import type { DataProvider, ReviewQuery } from "../types/api";
import type {
  Account,
  DashboardSummary,
  DataState,
  DecisionInput,
  Employee,
  EmployeeDeleteResult,
  EmployeeInput,
  Notification,
  NotificationFeed,
  PasswordUpdateInput,
  PasswordUpdateResult,
  ReviewDetail,
  ReviewReport,
  ReviewReportStage,
  ReviewStatus,
  ReviewTask,
  ReviewUpdateInput,
  ReviewWorkflowActionInput,
} from "../types/domain";
import { artifactScenarios, type ArtifactScenarioId } from "../fixtures/artifactScenarios";
import { createApiError } from "./errors";
import { createFixtureWorkflowStore, type FixtureWorkflowStore } from "./fixtureWorkflowStore";

const fixtureAccount: Account = {
  userId: "fixture-user",
  name: "예시 담당자",
  email: "reviewer@example.invalid",
  department: "legal",
  role: "reviewer",
  needsPasswordChange: false,
};

export class FixtureProvider implements DataProvider {
  private employees: Employee[] = createEmployees();
  private readonly reviewOverrides = new Map<string, { task: ReviewTask; copy: string; deleted: boolean }>();
  private readonly workflowStore: FixtureWorkflowStore;

  public constructor(private readonly scenarioId: ArtifactScenarioId = "LG-1", private readonly reviewStatus?: ReviewStatus, workflowStore?: FixtureWorkflowStore) {
    this.workflowStore = workflowStore ?? createFixtureWorkflowStore();
  }

  public async getDashboard(): Promise<DataState<DashboardSummary>> {
    if (this.scenarioId === "LG-2") {
      return { status: "empty", message: "접수된 보고서가 없습니다." };
    }

    const tasks = this.scenarioId === "LG-3" ? [] : [createTask("fixture-review-1", "waiting")];
    return {
      status: "ready",
      data: {
        pendingCount: this.scenarioId === "LG-3" ? 0 : 14,
        inProgressCount: this.scenarioId === "LG-3" ? 0 : 9,
        completedTodayCount: this.scenarioId === "LG-3" ? 0 : 3,
        tasks,
        recentReports: tasks,
      },
    };
  }

  public async listReviews(query: ReviewQuery): Promise<DataState<ReviewTask[]>> {
    if (this.scenarioId === "LG-9") {
      return { status: "empty", message: "조건에 맞는 검토 보고서가 없습니다." };
    }

    const supportedStatuses: ReviewStatus[] = ["waiting", "in-progress", "completed", "first-review-completed", "second-review-completed", "legal-review", "marketing-completed-approved", "marketing-completed-rejected", "legal-pending", "legal-in-progress", "legal-completed-approved", "legal-completed-rejected", "legal-completed-needs-revision", "legal-completed-continuable", "marketing-cancelled"];
    const scenarioStatus: Partial<Record<ArtifactScenarioId, ReviewStatus>> = { "LG-5": "waiting", "LG-6": "in-progress", "LG-7": "completed" };
    const status = query.processingStatus && supportedStatuses.includes(query.processingStatus as ReviewStatus) ? query.processingStatus as ReviewStatus : this.reviewStatus ?? scenarioStatus[this.scenarioId] ?? "marketing-completed-rejected";
    const reviews = [this.getTask("fixture-review-1", status), this.getTask("fixture-review-2", "marketing-completed-approved"), this.getTask("fixture-review-3", "legal-in-progress"), this.getTask("fixture-review-4", "legal-completed-approved")].filter((review) => !this.reviewOverrides.get(review.id)?.deleted);
    const filtered = query.search ? reviews.filter((review) => review.title.includes(query.search ?? "")) : reviews;
    return filtered.length > 0 ? { status: "ready", data: filtered } : { status: "empty", message: "조건에 맞는 검토 보고서가 없습니다." };
  }

  public async getReviewDetail(reviewId: string): Promise<DataState<ReviewDetail>> {
    const readOnly = this.scenarioId === "LG-17" || this.scenarioId === "LG-30" || this.scenarioId === "LG-31" || this.scenarioId === "LG-32" || this.scenarioId === "LG-33";
    const stored = this.workflowStore.getReview(reviewId);
    if (stored) {
      return { status: "ready", data: { ...stored, report: stored.report ?? createReviewReportForDetail(stored.status, stored.judgment, stored.id, stored.legalOpinion ?? null), canDecide: !readOnly, readOnlyReason: readOnly ? "다른 담당자가 처리했거나 처리 권한이 없습니다." : null } };
    }
    const task = this.getTask(reviewId, this.reviewStatus ?? (this.scenarioId === "LG-23" ? "in-progress" : statusForReviewId(reviewId)));
    const override = this.reviewOverrides.get(reviewId);
    if (override?.deleted) return { status: "empty", message: "삭제된 검토 보고서입니다." };
    const detail: ReviewDetail = {
      ...task,
      copy: override?.copy ?? "하루 한 포로 가볍게, 부담 없이 건강한 에너지를 채워 보세요.",
      attachments: ["저당-에너지바-광고시안.pdf"],
      findings: [{ id: "fixture-finding-1", severity: "violation-suspected", phrase: "효과를 보장합니다", reason: "효과를 단정하는 표현은 확인이 필요합니다.", allowedCopy: "건강한 생활에 도움을 줄 수 있어요", evidence: [{ label: "적용 조항", source: "확인된 API 연결 후 표시됩니다.", href: null }], alternatives: ["건강한 생활에 도움을 줄 수 있어요"] }],
      evidencePath: ["광고 문구", "AI 자동 검사", "적용 조항"],
      report: createReviewReportForDetail(task.status, task.judgment, task.id, null),
      canDecide: !readOnly,
      readOnlyReason: readOnly ? "다른 담당자가 처리했거나 처리 권한이 없습니다." : null,
      decisionReason: this.scenarioId === "LG-20" || this.scenarioId === "LG-27" ? "예시 부적합 사유" : null,
      legalOpinion: null,
      pdfUrl: null,
    };
    this.saveReview(detail);
    return {
      status: "ready",
      data: detail,
    };
  }

  public async submitDecision(input: DecisionInput): Promise<DataState<ReviewDetail>> {
    if (this.scenarioId === "LG-15" || this.scenarioId === "LG-22") {
      return {
        status: "error",
        error: createApiError("http", "판정 저장에 실패했습니다.", { reason: input.reason }),
      };
    }

    const detail = await this.getReviewDetail(input.reviewId);
    if (detail.status !== "ready") {
      return detail;
    }

    const next = { ...detail.data, judgment: input.decision, decisionReason: input.reason ?? null, status: "completed" as const, processedAt: new Date().toISOString(), report: createReviewReportForDetail("completed", input.decision, detail.data.id, detail.data.legalOpinion ?? null) };
    this.saveReview(next);
    return { status: "ready", data: next };
  }

  public async updateReview(reviewId: string, input: ReviewUpdateInput): Promise<DataState<ReviewTask>> {
    const detail = await this.getReviewDetail(reviewId);
    if (detail.status !== "ready") return detail.status === "empty" ? detail : { status: "error", error: createApiError("unknown", "검토 항목을 수정하지 못했습니다.") };
    const next = { ...detail.data, title: input.title, category: input.category };
    this.saveReview({ ...detail.data, ...next, copy: input.copy });
    return { status: "ready", data: next };
  }

  public async performReviewAction(input: ReviewWorkflowActionInput): Promise<DataState<ReviewDetail>> {
    if ((input.action === "approve-legal" || input.action === "reject-legal" || input.action === "start-legal-review" || input.action === "complete-legal-approved" || input.action === "complete-legal-rejected" || input.action === "complete-legal-needs-revision" || input.action === "complete-legal-continuable" || input.action === "close-review") && input.role !== "legal") {
      return { status: "error", error: createApiError("http", "법무팀 직원만 법무 검토를 처리할 수 있습니다.", undefined, 403) };
    }
    if (input.action === "delete-review") {
      const detail = await this.getReviewDetail(input.reviewId);
      if (detail.status !== "ready") return detail;
      this.reviewOverrides.set(input.reviewId, { task: detail.data, copy: detail.data.copy, deleted: true });
      return { status: "ready", data: detail.data };
    }
    const detail = await this.getReviewDetail(input.reviewId);
    if (detail.status !== "ready") return detail;
    const task = { ...detail.data };
    if (input.action === "request-second-review") { task.status = "second-review-completed"; task.judgment = "approved"; task.hasSecondReview = true; }
    if (input.action === "request-legal-review") { task.status = "legal-pending"; task.judgment = "pending"; }
    if (input.action === "cancel-review") { task.status = "marketing-cancelled"; }
    if (input.action === "start-legal-review") {
      task.status = "legal-in-progress";
      task.judgment = "pending";
    }
    if (input.action === "close-review") { task.status = "legal-in-progress"; task.judgment = "pending"; }
    if (input.action === "complete-legal-approved" || input.action === "complete-legal-rejected" || input.action === "complete-legal-needs-revision" || input.action === "complete-legal-continuable") {
      if (!input.legalOpinion?.trim()) return { status: "error", error: createApiError("http", "법무 검토 의견을 입력해 주세요.") };
      if (detail.data.status !== "legal-pending" && detail.data.status !== "legal-in-progress") return { status: "error", error: createApiError("http", "법무 검토 대기 또는 진행 중인 문서만 결과를 처리할 수 있습니다.") };
      task.status = input.action === "complete-legal-approved" ? "legal-completed-approved" : input.action === "complete-legal-rejected" ? "legal-completed-rejected" : input.action === "complete-legal-needs-revision" ? "legal-completed-needs-revision" : "legal-completed-continuable";
      task.judgment = input.action === "complete-legal-approved" || input.action === "complete-legal-continuable" ? "approved" : "rejected";
      task.processedAt = new Date().toISOString();
    }
    if (input.action === "approve-legal") { task.status = "completed"; task.judgment = "approved"; task.processedAt = new Date().toISOString(); }
    if (input.action === "reject-legal") { task.status = "completed"; task.judgment = "rejected"; task.processedAt = new Date().toISOString(); }
    const next = { ...detail.data, ...task, legalOpinion: input.legalOpinion?.trim() || detail.data.legalOpinion || null, report: createReviewReportForDetail(task.status, task.judgment, task.id, input.legalOpinion?.trim() || detail.data.legalOpinion || null) };
    this.saveReview(next);
    return { status: "ready", data: next };
  }

  public async getAccount(): Promise<DataState<Account>> {
    return {
      status: "ready",
      data: { ...fixtureAccount, needsPasswordChange: this.scenarioId === "LG-40" },
    };
  }

  public async updatePassword(input: PasswordUpdateInput): Promise<DataState<PasswordUpdateResult>> {
    if (this.scenarioId === "LG-39" && input.newPassword === input.confirmation) {
      return { status: "ready", data: { account: fixtureAccount, message: "비밀번호가 변경되었습니다." } };
    }

    return {
      status: "error",
      error: createApiError("http", "비밀번호를 변경하지 못했습니다.", { inputPreserved: true }),
    };
  }

  public async listNotifications(): Promise<DataState<NotificationFeed>> {
    if (this.scenarioId === "LG-37") {
      return { status: "empty", message: "새로운 알림이 없습니다." };
    }

    const notifications: Notification[] = this.scenarioId === "LG-36"
      ? [{ id: "fixture-notification-old", title: "지난 알림", message: "처리 완료된 보고서가 있습니다.", createdAt: "fixture-date", read: true }]
      : [{ id: "fixture-notification-new", title: "새 알림", message: "확인이 필요한 보고서가 있습니다.", createdAt: "fixture-date", read: false }];
    return { status: "ready", data: { notifications, scenarioId: this.scenarioId } };
  }

  public async markNotificationsRead(): Promise<DataState<NotificationFeed>> {
    const result = await this.listNotifications();
    if (result.status !== "ready") {
      return result;
    }

    return { status: "ready", data: { ...result.data, notifications: result.data.notifications.map((item) => ({ ...item, read: true })) } };
  }

  public async getReviewReport(reviewId: string, stage: ReviewReportStage): Promise<DataState<ReviewReport>> {
    const detail = await this.getReviewDetail(reviewId);
    if (detail.status !== "ready") return detail.status === "empty" ? detail : { status: "error", error: createApiError("unknown", "보고서를 불러오지 못했습니다.") };
    return { status: "ready", data: createReviewReportForDetail(stage, detail.data.judgment, reviewId, detail.data.legalOpinion ?? null) };
  }

  public async listEmployees(search?: string): Promise<DataState<Employee[]>> {
    const filtered = search ? this.employees.filter((employee) => `${employee.name} ${employee.email} ${employee.phone}`.includes(search)) : this.employees;
    return filtered.length > 0 ? { status: "ready", data: filtered } : { status: "empty", message: "조건에 맞는 직원이 없습니다." };
  }

  public async getEmployee(employeeId: string): Promise<DataState<Employee>> {
    const employee = this.employees.find((item) => item.id === employeeId);
    return employee ? { status: "ready", data: employee } : { status: "empty", message: "직원 정보를 찾을 수 없습니다." };
  }

  public async createEmployee(input: EmployeeInput): Promise<DataState<Employee>> {
    const employeeFields = { ...input };
    delete employeeFields.password;
    const employee = { ...employeeFields, id: `fixture-employee-${this.employees.length + 1}`, status: "active" as const };
    this.employees = [...this.employees, employee];
    return { status: "ready", data: employee };
  }

  public async updateEmployee(employeeId: string, input: EmployeeInput): Promise<DataState<Employee>> {
    const current = this.employees.find((item) => item.id === employeeId);
    if (!current) return { status: "empty", message: "직원 정보를 찾을 수 없습니다." };
    const employeeFields = { ...input };
    delete employeeFields.password;
    const employee = { ...current, ...employeeFields };
    this.employees = this.employees.map((item) => item.id === employeeId ? employee : item);
    return { status: "ready", data: employee };
  }

  public async deleteEmployee(employeeId: string): Promise<DataState<EmployeeDeleteResult>> {
    if (!this.employees.some((item) => item.id === employeeId)) return { status: "empty", message: "직원 정보를 찾을 수 없습니다." };
    this.employees = this.employees.filter((item) => item.id !== employeeId);
    return { status: "ready", data: { employeeId } };
  }

  private getTask(id: string, status: ReviewStatus): ReviewTask {
    const stored = this.workflowStore.getReview(id);
    if (stored) return { ...stored };
    const override = this.reviewOverrides.get(id);
    return override ? { ...override.task } : createTask(id, status);
  }

  private saveReview(detail: ReviewDetail): void {
    this.reviewOverrides.set(detail.id, { task: { ...detail }, copy: detail.copy, deleted: false });
    this.workflowStore.saveReview(detail);
  }
}

function createTask(id: string, status: ReviewTask["status"]): ReviewTask {
  return {
    id,
    title: id === "fixture-review-1" ? "저당 에너지바 광고" : id === "fixture-review-2" ? "키즈 초코우유 광고" : id === "fixture-review-3" ? "어린이 비타민 젤리 광고" : "무설탕 탄산수 광고",
    advertiser: id === "fixture-review-3" ? "푸드가드 헬스케어" : "푸드가드 식품",
    author: id.endsWith("3") ? "김법무" : "김마케팅",
    category: id.endsWith("3") ? "일반식품" : "건강기능식품",
    submittedAt: "2026-11-24 09:20",
    sentAt: "2026-11-24 10:00",
    status,
    judgment: judgmentForTask(id, status),
    assignee: "예시 담당자",
    processedAt: null,
    ownerId: "fixture-user",
    copy: "하루 한 포로 가볍게, 부담 없이 건강한 에너지를 채워 보세요.",
    hasSecondReview: status === "second-review-completed" || (status === "completed" && !id.endsWith("5")) || (status === "legal-review" && id.endsWith("3")),
  };
}

function statusForReviewId(id: string): ReviewStatus {
  if (id.endsWith("2")) return "marketing-completed-approved";
  if (id.endsWith("3")) return "legal-in-progress";
  if (id.endsWith("5")) return "legal-pending";
  if (id.endsWith("4")) return "legal-completed-approved";
  return "marketing-completed-rejected";
}

function judgmentForTask(id: string, status: ReviewStatus): ReviewTask["judgment"] {
  if (status === "first-review-completed" || status === "marketing-completed-rejected") return "rejected";
  if (status === "marketing-completed-approved" || status === "second-review-completed" || status === "completed" || status === "legal-completed-approved" || status === "legal-completed-continuable") return "approved";
  if (status === "legal-completed-rejected" || status === "legal-completed-needs-revision") return "rejected";
  return "pending";
}

function reportStageForStatus(status: ReviewStatus | ReviewReportStage): "marketing" | "legal" {
  if (status === "marketing" || status === "first-review" || status === "second-review" || status === "first-review-completed" || status === "second-review-completed" || status === "marketing-completed-approved" || status === "marketing-completed-rejected" || status === "marketing-cancelled") return "marketing";
  return "legal";
}

function createReviewReportForDetail(status: ReviewStatus | ReviewReportStage, judgment: ReviewTask["judgment"] = "pending", reviewId = "fixture-review-1", legalOpinion: string | null = null): ReviewReport {
  const stage = reportStageForStatus(status);
  const title = stage === "marketing" ? "[마케팅]광고 문구 검토 보고서" : "[법무]광고 문구 검토 보고서";
  const result = status === "legal-completed-needs-revision" ? "보완 필요" : status === "legal-completed-continuable" ? "진행 가능" : judgment === "pending" || judgment === "hold" ? status === "legal-in-progress" ? "검토 중" : "검토 대기" : judgment === "approved" ? "적합" : "부적합";
  const sections = [
    { label: "검토 결과", value: result },
    { label: "광고 문구", value: "하루 한 포로 가볍게, 부담 없이 건강한 에너지를 채워 보세요." },
    { label: "처리 담당", value: stage === "legal" ? "법무팀" : "마케팅팀" },
    { label: "검토 의견", value: stage === "legal" ? legalOpinion ?? "법무 검토 의견이 아직 없습니다." : "AI 검사 결과와 검토 근거를 확인해 주세요." },
  ];
  const references = stage === "legal" ? [{ id: reviewId, label: "[마케팅]광고 문구 검토 보고서", stage: "marketing" as const }] : [];
  return { stage, title, summary: `${title} 내용을 확인하는 시연용 보고서입니다.`, sections, references };
}

function createEmployees(): Employee[] {
  return [
    { id: "fixture-marketing", name: "김마케팅", department: "marketing", email: "marketing@example.invalid", phone: "010-0000-0001", status: "active" },
    { id: "fixture-legal", name: "김법무", department: "legal", email: "legal@example.invalid", phone: "010-0000-0002", status: "inactive" },
  ];
}

export function getFixtureScenarioTitle(id: ArtifactScenarioId): string {
  return artifactScenarios[id].title;
}
