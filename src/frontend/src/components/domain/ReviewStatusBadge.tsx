import { Badge } from "../ui/Badge";
import type { ReviewJudgment, ReviewStatus } from "../../types/domain";

const labels: Record<ReviewStatus, string> = {
  waiting: "검토 대기",
  "in-progress": "검토 중",
  completed: "검토 완료",
  "first-review-completed": "1차 검토 완료",
  "second-review-completed": "2차 검토 완료",
  "legal-review": "법무팀 검토",
  "marketing-completed-approved": "[마케팅]검토 완료(적합)",
  "marketing-completed-rejected": "[마케팅]검토 완료(부적합)",
  "legal-pending": "[법무]검토 대기",
  "legal-in-progress": "[법무]검토 중",
  "legal-completed-approved": "[법무]검토 완료(적합)",
  "legal-completed-rejected": "[법무]검토 완료(부적합)",
  "legal-completed-needs-revision": "[법무]검토 완료(보완 필요)",
  "legal-completed-continuable": "[법무]검토 완료(진행 가능)",
  "marketing-cancelled": "[마케팅]심의 취소",
};
function resultLabel(status: ReviewStatus, judgment?: ReviewJudgment): string | null {
  if (judgment !== "approved" && judgment !== "rejected") return null;
  if (status === "first-review-completed" || status === "second-review-completed") return judgment === "approved" ? "적합" : "부적합";
  if (status === "completed") return judgment === "approved" ? "승인" : "반려";
  if (status === "legal-completed-needs-revision") return "보완 필요";
  if (status === "legal-completed-continuable") return "진행 가능";
  return null;
}

export function ReviewStatusBadge({ status, judgment }: { status: ReviewStatus; judgment?: ReviewJudgment }) {
  const result = resultLabel(status, judgment);
  const tone = status === "marketing-cancelled" || status === "marketing-completed-rejected" || status === "legal-completed-rejected" || status === "legal-completed-needs-revision" ? "danger" : status === "marketing-completed-approved" || status === "legal-completed-approved" || status === "legal-completed-continuable" || status === "completed" ? "success" : status === "legal-pending" || status === "legal-in-progress" || status === "legal-review" || status === "in-progress" ? "info" : "warning";
  return <span className="status-badge-group"><Badge tone={tone}>{labels[status]}</Badge>{result ? <Badge tone={judgment === "approved" ? "success" : "danger"}>{result}</Badge> : null}</span>;
}
