export type UserRole = "admin" | "reviewer" | "viewer";
export type Department = "legal" | "marketing" | "quality" | "unknown";
export type ReviewJudgment = "pending" | "approved" | "rejected" | "hold";
export type ReviewStatus = "waiting" | "in-progress" | "completed" | "first-review-completed" | "second-review-completed" | "legal-review" | "marketing-completed-approved" | "marketing-completed-rejected" | "legal-pending" | "legal-in-progress" | "legal-completed-approved" | "legal-completed-rejected" | "legal-completed-needs-revision" | "legal-completed-continuable" | "marketing-cancelled";
export type ReviewReportStage = "first-review" | "second-review" | "legal-review" | "completed" | "marketing" | "legal";
export type ReviewWorkflowRole = "legal" | "marketing" | "unknown";
export type ReviewWorkflowAction = "request-second-review" | "request-legal-review" | "approve-legal" | "reject-legal" | "delete-review" | "start-legal-review" | "complete-legal-approved" | "complete-legal-rejected" | "complete-legal-needs-revision" | "complete-legal-continuable" | "cancel-review" | "close-review";
export type MarketingWorkflowAction = "request-legal-review" | "cancel-review";
export type EmployeeDepartment = "marketing" | "legal";
export type EmployeeStatus = "active" | "inactive";

export interface ReviewTask {
  id: string;
  title: string;
  advertiser: string;
  author: string;
  category: string;
  submittedAt: string;
  sentAt: string;
  status: ReviewStatus;
  judgment: ReviewJudgment;
  assignee: string | null;
  processedAt: string | null;
  ownerId: string | null;
  copy?: string;
  hasSecondReview?: boolean;
}

export interface ReviewUpdateInput {
  title: string;
  category: string;
  copy: string;
}

export interface ReviewWorkflowActionInput {
  reviewId: string;
  action: ReviewWorkflowAction;
  role?: ReviewWorkflowRole;
  legalOpinion?: string;
}

export interface MarketingWorkflowActionInput {
  checkId: string;
  reviewId: string;
  action: MarketingWorkflowAction;
}

export interface ReviewDetail extends ReviewTask {
  copy: string;
  attachments: string[];
  findings?: CheckFinding[];
  evidencePath?: string[];
  canDecide: boolean;
  readOnlyReason: string | null;
  decisionReason: string | null;
  legalOpinion?: string | null;
  pdfUrl: string | null;
  report?: ReviewReport;
}

export interface ReviewReferenceDocument {
  id: string;
  label: string;
  stage: ReviewReportStage;
}

export interface ReviewReportSection {
  label: string;
  value: string;
}

export interface ReviewReport {
  stage: ReviewReportStage;
  title: string;
  summary: string;
  sections: ReviewReportSection[];
  references: ReviewReferenceDocument[];
}

export interface DashboardSummary {
  pendingCount: number;
  inProgressCount: number;
  completedTodayCount: number;
  tasks: ReviewTask[];
  recentReports: ReviewTask[];
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  createdAt: string;
  read: boolean;
}

export interface NotificationFeed {
  notifications: Notification[];
  scenarioId?: string;
}

export interface Account {
  userId: string;
  name: string;
  email: string;
  department: Department;
  role: UserRole;
  needsPasswordChange: boolean;
}

export interface DecisionInput {
  reviewId: string;
  decision: "approved" | "rejected";
  reason?: string;
}

export interface PasswordUpdateInput {
  currentPassword: string;
  newPassword: string;
  confirmation: string;
}

export interface PasswordUpdateResult {
  account: Account;
  message: string;
}

export type CheckProductType = "general-food" | "health-functional-food";
export type CheckFindingSeverity = "violation-suspected" | "ambiguous" | "safe";
export type CheckProgressStatus = "completed" | "in-progress" | "skipped" | "waiting";

export interface CheckInput {
  title: string;
  productType: CheckProductType;
  ingredient: string;
  channel: string;
  copy: string;
  attachments: CheckAttachment[];
}

export interface CheckAttachment {
  id: string;
  name: string;
  size: number;
  type: string;
}

export interface EvidenceReference {
  label: string;
  source: string;
  href: string | null;
}

export interface CheckFinding {
  id: string;
  severity: CheckFindingSeverity;
  phrase: string;
  reason: string;
  allowedCopy: string | null;
  evidence: EvidenceReference[];
  alternatives: string[];
}

export interface CheckResult extends CheckInput {
  id: string;
  findings: CheckFinding[];
  reviewId: string | null;
  nextStep: string;
  reviewJudgments?: {
    first: "approved" | "rejected";
    second: "approved" | "rejected";
  };
  marketingJudgment?: "approved" | "rejected";
  recommendations?: string[];
}

export interface CheckStartResult {
  checkId: string;
  progressId: string;
  reviewId?: string;
}

export interface CheckRecommendationResult {
  checkId: string;
  recommendations: string[];
  selectedRecommendation: string;
}

export interface CheckDraftResult {
  draftId: string;
}

export interface CheckProgressStep {
  id: string;
  label: string;
  status: CheckProgressStatus;
  owner: string;
  detail: string;
}

export interface CheckProgressHistoryItem {
  id: string;
  actor: string;
  action: string;
  createdAt: string;
}

export interface CheckProgress {
  id: string;
  title: string;
  currentStep: string;
  owner: string;
  requestedAt: string;
  steps: CheckProgressStep[];
  history: CheckProgressHistoryItem[];
}

export interface Employee {
  id: string;
  name: string;
  department: EmployeeDepartment;
  email: string;
  phone: string;
  status: EmployeeStatus;
}

export interface EmployeeInput {
  name: string;
  department: EmployeeDepartment;
  email: string;
  phone: string;
  password?: string;
  status?: EmployeeStatus;
}

export interface EmployeeDeleteResult {
  employeeId: string;
}

export type DataState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "empty"; message: string }
  | { status: "error"; error: import("../api/errors").ApiError }
  | { status: "not-configured"; message: string };
