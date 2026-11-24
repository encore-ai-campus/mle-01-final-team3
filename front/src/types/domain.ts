export type UserRole = "admin" | "reviewer" | "viewer";
export type Department = "legal" | "marketing" | "quality" | "unknown";
export type ReviewJudgment = "pending" | "approved" | "rejected" | "hold";
export type ReviewStatus = "waiting" | "in-progress" | "completed";

export interface ReviewTask {
  id: string;
  title: string;
  advertiser: string;
  submittedAt: string;
  status: ReviewStatus;
  judgment: ReviewJudgment;
  assignee: string | null;
  processedAt: string | null;
  ownerId: string | null;
}

export interface ReviewDetail extends ReviewTask {
  copy: string;
  attachments: string[];
  canDecide: boolean;
  readOnlyReason: string | null;
  decisionReason: string | null;
  pdfUrl: string | null;
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

export type DataState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "empty"; message: string }
  | { status: "error"; error: import("../api/errors").ApiError }
  | { status: "not-configured"; message: string };
