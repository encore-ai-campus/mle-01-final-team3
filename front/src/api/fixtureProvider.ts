import type { DataProvider, ReviewQuery } from "../types/api";
import type {
  Account,
  DashboardSummary,
  DataState,
  DecisionInput,
  Notification,
  NotificationFeed,
  PasswordUpdateInput,
  PasswordUpdateResult,
  ReviewDetail,
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
  public constructor(private readonly scenarioId: ArtifactScenarioId = "LG-1") {}

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

    const status = query.processingStatus === "in-progress" ? "in-progress" : query.processingStatus === "completed" ? "completed" : "waiting";
    const reviews = [createTask("fixture-review-1", status), createTask("fixture-review-2", "completed")];
    const filtered = query.search ? reviews.filter((review) => review.title.includes(query.search ?? "")) : reviews;
    return filtered.length > 0 ? { status: "ready", data: filtered } : { status: "empty", message: "조건에 맞는 검토 보고서가 없습니다." };
  }

  public async getReviewDetail(reviewId: string): Promise<DataState<ReviewDetail>> {
    const readOnly = this.scenarioId === "LG-17" || this.scenarioId === "LG-30" || this.scenarioId === "LG-31" || this.scenarioId === "LG-32" || this.scenarioId === "LG-33";
    const task = createTask(reviewId, this.scenarioId === "LG-23" ? "in-progress" : "waiting");
    return {
      status: "ready",
      data: {
        ...task,
        copy: "예시 광고 문구는 실제 API 연결 후 표시됩니다.",
        attachments: ["fixture-attachment.pdf"],
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
}

function createTask(id: string, status: ReviewTask["status"]): ReviewTask {
  return {
    id,
    title: "예시 검토 보고서",
    advertiser: "예시 광고주",
    submittedAt: "fixture-date",
    status,
    judgment: "pending",
    assignee: "예시 담당자",
    processedAt: null,
    ownerId: "fixture-user",
  };
}

export function getFixtureScenarioTitle(id: ArtifactScenarioId): string {
  return artifactScenarios[id].title;
}
