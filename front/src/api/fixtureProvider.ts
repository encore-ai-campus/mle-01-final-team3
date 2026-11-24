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
} from "../types/domain";
import { artifactScenarios, type ArtifactScenarioId } from "../fixtures/artifactScenarios";
import { createApiError } from "./errors";

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

  public constructor(private readonly scenarioId: ArtifactScenarioId = "LG-1", private readonly reviewStatus?: ReviewStatus) {}

  public async getDashboard(): Promise<DataState<DashboardSummary>> {
    if (this.scenarioId === "LG-2") {
      return { status: "empty", message: "접수된 보고서가 없습니다." };
    }

    const tasks = this.scenarioId === "LG-3" ? [] : [createTask("fixture-review-1", "waiting")];
    return {
      status: "ready",
      data: {
        pendingCount: tasks.length,
        inProgressCount: 0,
        completedTodayCount: this.scenarioId === "LG-3" ? 0 : 1,
        tasks,
        recentReports: tasks,
      },
    };
  }

  public async listReviews(query: ReviewQuery): Promise<DataState<ReviewTask[]>> {
    if (this.scenarioId === "LG-9") {
      return { status: "empty", message: "조건에 맞는 검토 보고서가 없습니다." };
    }

    const supportedStatuses: ReviewStatus[] = ["waiting", "in-progress", "completed", "first-review-completed", "second-review-completed", "legal-review"];
    const status = query.processingStatus && supportedStatuses.includes(query.processingStatus as ReviewStatus) ? query.processingStatus as ReviewStatus : this.reviewStatus ?? "first-review-completed";
    const reviews = [createTask("fixture-review-1", status), createTask("fixture-review-2", "second-review-completed"), createTask("fixture-review-3", "legal-review"), createTask("fixture-review-4", "completed")];
    const filtered = query.search ? reviews.filter((review) => review.title.includes(query.search ?? "")) : reviews;
    return filtered.length > 0 ? { status: "ready", data: filtered } : { status: "empty", message: "조건에 맞는 검토 보고서가 없습니다." };
  }

  public async getReviewDetail(reviewId: string): Promise<DataState<ReviewDetail>> {
    const readOnly = this.scenarioId === "LG-17" || this.scenarioId === "LG-30" || this.scenarioId === "LG-31" || this.scenarioId === "LG-32" || this.scenarioId === "LG-33";
    const task = createTask(reviewId, this.reviewStatus ?? (this.scenarioId === "LG-23" ? "in-progress" : statusForReviewId(reviewId)));
    const report = createReviewReport(task.status);
    return {
      status: "ready",
      data: {
        ...task,
        copy: "예시 광고 문구는 실제 API 연결 후 표시됩니다.",
        attachments: ["fixture-attachment.pdf"],
        findings: [{ id: "fixture-finding-1", severity: "violation-suspected", phrase: "효과를 보장합니다", reason: "효과를 단정하는 표현은 확인이 필요합니다.", allowedCopy: "건강한 생활에 도움을 줄 수 있어요", evidence: [{ label: "적용 조항", source: "확인된 API 연결 후 표시됩니다.", href: null }], alternatives: ["건강한 생활에 도움을 줄 수 있어요"] }],
        evidencePath: ["광고 문구", "AI 자동 검사", "적용 조항"],
        report,
        canDecide: !readOnly,
        readOnlyReason: readOnly ? "다른 담당자가 처리했거나 처리 권한이 없습니다." : null,
        decisionReason: this.scenarioId === "LG-20" || this.scenarioId === "LG-27" ? "예시 부적합 사유" : null,
        pdfUrl: null,
      },
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

    return {
      status: "ready",
      data: {
        ...detail.data,
        judgment: input.decision,
        decisionReason: input.reason ?? null,
        status: "completed",
        processedAt: new Date().toISOString(),
      },
    };
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

  public async getReviewReport(_reviewId: string, stage: ReviewReportStage): Promise<DataState<ReviewReport>> { return { status: "ready", data: createReviewReport(stage === "first-review" ? "first-review-completed" : stage === "second-review" ? "second-review-completed" : "legal-review") }; }

  public async listEmployees(search?: string): Promise<DataState<Employee[]>> {
    const filtered = search ? this.employees.filter((employee) => `${employee.name} ${employee.email} ${employee.phone}`.includes(search)) : this.employees;
    return filtered.length > 0 ? { status: "ready", data: filtered } : { status: "empty", message: "조건에 맞는 직원이 없습니다." };
  }

  public async getEmployee(employeeId: string): Promise<DataState<Employee>> {
    const employee = this.employees.find((item) => item.id === employeeId);
    return employee ? { status: "ready", data: employee } : { status: "empty", message: "직원 정보를 찾을 수 없습니다." };
  }

  public async createEmployee(input: EmployeeInput): Promise<DataState<Employee>> {
    const employee = { ...input, id: `fixture-employee-${this.employees.length + 1}`, status: "active" as const };
    this.employees = [...this.employees, employee];
    return { status: "ready", data: employee };
  }

  public async updateEmployee(employeeId: string, input: EmployeeInput): Promise<DataState<Employee>> {
    const current = this.employees.find((item) => item.id === employeeId);
    if (!current) return { status: "empty", message: "직원 정보를 찾을 수 없습니다." };
    const employee = { ...current, ...input };
    this.employees = this.employees.map((item) => item.id === employeeId ? employee : item);
    return { status: "ready", data: employee };
  }

  public async deleteEmployee(employeeId: string): Promise<DataState<EmployeeDeleteResult>> {
    if (!this.employees.some((item) => item.id === employeeId)) return { status: "empty", message: "직원 정보를 찾을 수 없습니다." };
    this.employees = this.employees.filter((item) => item.id !== employeeId);
    return { status: "ready", data: { employeeId } };
  }
}

function createTask(id: string, status: ReviewTask["status"]): ReviewTask {
  const suffix = id.endsWith("2") ? " 2" : id.endsWith("3") ? " 3" : id.endsWith("4") ? " 4" : "";
  return {
    id,
    title: id === "fixture-review-1" ? "예시 검토 보고서" : `예시 광고${suffix}`,
    advertiser: "예시 광고주",
    author: id.endsWith("3") ? "김법무" : "김마케팅",
    category: id.endsWith("3") ? "일반식품" : "건강기능식품",
    submittedAt: "fixture-date",
    sentAt: "fixture-date",
    status,
    judgment: "pending",
    assignee: "예시 담당자",
    processedAt: null,
    ownerId: "fixture-user",
  };
}

function statusForReviewId(id: string): ReviewStatus {
  if (id.endsWith("2")) return "second-review-completed";
  if (id.endsWith("3")) return "legal-review";
  if (id.endsWith("4")) return "completed";
  return "first-review-completed";
}

function createReviewReport(status: ReviewStatus | ReviewReportStage): ReviewReport {
  const stage: ReviewReportStage = status === "first-review-completed" || status === "first-review" ? "first-review" : status === "second-review-completed" || status === "second-review" ? "second-review" : "legal-review";
  const labels = { "first-review": "1차 검토 보고서", "second-review": "2차 검토 보고서", "legal-review": "법무팀 검토 보고서" } as const;
  const references = stage === "first-review" ? [] : stage === "second-review" ? [{ id: "fixture-review-1", label: "1차 검토 보고서", stage: "first-review" as const }] : [{ id: "fixture-review-1", label: "1차 검토 보고서", stage: "first-review" as const }, { id: "fixture-review-2", label: "2차 검토 보고서", stage: "second-review" as const }];
  return { stage, title: labels[stage], summary: `${labels[stage]} 기준으로 광고 문구와 검토 결과를 정리한 예시 보고서입니다.`, sections: [{ label: "검토 의견", value: "확인된 API 연결 후 실제 담당자 의견이 표시됩니다." }, { label: "처리 담당", value: stage === "legal-review" ? "법무팀" : stage === "second-review" ? "RA팀" : "1차 검토 담당자" }], references };
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
