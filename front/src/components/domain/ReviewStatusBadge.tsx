import { Badge } from "../ui/Badge";
import type { ReviewStatus } from "../../types/domain";

const labels: Record<ReviewStatus, string> = { waiting: "검토 대기", "in-progress": "검토 중", completed: "검토 완료", "first-review-completed": "1차 검토 완료", "second-review-completed": "2차 검토 완료", "legal-review": "법무팀 검토" };
export function ReviewStatusBadge({ status }: { status: ReviewStatus }) { return <Badge tone={status === "completed" ? "success" : status === "legal-review" ? "info" : status === "second-review-completed" ? "info" : status === "first-review-completed" ? "success" : status === "in-progress" ? "info" : "warning"}>{labels[status]}</Badge>; }
