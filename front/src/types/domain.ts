export type UserRole = "admin" | "reviewer" | "viewer";
export type Department = "legal" | "marketing" | "quality" | "unknown";
export type ReviewJudgment = "pending" | "approved" | "rejected" | "hold";
export type ReviewStatus = "waiting" | "in-progress" | "completed" | "first-review-completed" | "second-review-completed" | "legal-review";
export type ReviewReportStage = "first-review" | "second-review" | "legal-review";
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
}

export interface ReviewDetail extends ReviewTask {
  copy: string;
  attachments: string[];
  findings?: CheckFinding[];
  evidencePath?: string[];
  canDecide: boolean;
  readOnlyReason: string | null;
  decisionReason: string | null;
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
}

export interface CheckStartResult {
  checkId: string;
  progressId: string;
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
