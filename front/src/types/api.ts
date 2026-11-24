import type {
  Account,
  CheckDraftResult,
  CheckInput,
  CheckProgress,
  CheckResult,
  CheckStartResult,
  DashboardSummary,
  DecisionInput,
  NotificationFeed,
  PasswordUpdateInput,
  PasswordUpdateResult,
  ReviewDetail,
  ReviewTask,
} from "./domain";

export interface ReviewQuery {
  search?: string;
  aiJudgment?: string;
  processingStatus?: string;
  assignee?: string;
  processingDate?: string;
}

export interface ApiContract {
  getDashboard?: () => Promise<unknown>;
  listReviews?: (query: ReviewQuery) => Promise<unknown>;
  getReviewDetail?: (reviewId: string) => Promise<unknown>;
  submitDecision?: (input: DecisionInput) => Promise<unknown>;
  getAccount?: () => Promise<unknown>;
  updatePassword?: (input: PasswordUpdateInput) => Promise<unknown>;
  listNotifications?: () => Promise<unknown>;
  markNotificationsRead?: () => Promise<unknown>;
}

export interface ApiProviderOptions {
  contract?: ApiContract;
}

export interface DataProvider {
  getDashboard(): Promise<import("./domain").DataState<DashboardSummary>>;
  listReviews(query: ReviewQuery): Promise<import("./domain").DataState<ReviewTask[]>>;
  getReviewDetail(reviewId: string): Promise<import("./domain").DataState<ReviewDetail>>;
  submitDecision(input: DecisionInput): Promise<import("./domain").DataState<ReviewDetail>>;
  getAccount(): Promise<import("./domain").DataState<Account>>;
  updatePassword(
    input: PasswordUpdateInput,
  ): Promise<import("./domain").DataState<PasswordUpdateResult>>;
  listNotifications(): Promise<import("./domain").DataState<NotificationFeed>>;
  markNotificationsRead(): Promise<import("./domain").DataState<NotificationFeed>>;
}

export interface CheckDataProvider {
  getResult(checkId: string): Promise<import("./domain").DataState<CheckResult>>;
  saveDraft(input: CheckInput): Promise<import("./domain").DataState<CheckDraftResult>>;
  startCheck(input: CheckInput): Promise<import("./domain").DataState<CheckStartResult>>;
  getProgress(checkId: string): Promise<import("./domain").DataState<CheckProgress>>;
}
