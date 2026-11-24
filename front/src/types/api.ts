import type {
  Account,
  CheckDraftResult,
  CheckInput,
  CheckProgress,
  CheckResult,
  CheckStartResult,
  DashboardSummary,
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
  listEmployees?: (search?: string) => Promise<unknown>;
  getEmployee?: (employeeId: string) => Promise<unknown>;
  createEmployee?: (input: EmployeeInput) => Promise<unknown>;
  updateEmployee?: (employeeId: string, input: EmployeeInput) => Promise<unknown>;
  deleteEmployee?: (employeeId: string) => Promise<unknown>;
  getReviewReport?: (reviewId: string, stage: ReviewReportStage) => Promise<unknown>;
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
  listEmployees(search?: string): Promise<import("./domain").DataState<Employee[]>>;
  getEmployee(employeeId: string): Promise<import("./domain").DataState<Employee>>;
  createEmployee(input: EmployeeInput): Promise<import("./domain").DataState<Employee>>;
  updateEmployee(employeeId: string, input: EmployeeInput): Promise<import("./domain").DataState<Employee>>;
  deleteEmployee(employeeId: string): Promise<import("./domain").DataState<EmployeeDeleteResult>>;
  getReviewReport(reviewId: string, stage: ReviewReportStage): Promise<import("./domain").DataState<ReviewReport>>;
}

export interface CheckDataProvider {
  getResult(checkId: string): Promise<import("./domain").DataState<CheckResult>>;
  saveDraft(input: CheckInput): Promise<import("./domain").DataState<CheckDraftResult>>;
  startCheck(input: CheckInput): Promise<import("./domain").DataState<CheckStartResult>>;
  getProgress(checkId: string): Promise<import("./domain").DataState<CheckProgress>>;
}
