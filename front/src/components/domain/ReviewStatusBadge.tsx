import { Badge } from "../ui/Badge";
import type { ReviewStatus } from "../../types/domain";

const labels: Record<ReviewStatus, string> = { waiting: "검토 대기", "in-progress": "검토 중", completed: "처리 완료" };
export function ReviewStatusBadge({ status }: { status: ReviewStatus }) { return <Badge tone={status === "completed" ? "success" : status === "in-progress" ? "info" : "warning"}>{labels[status]}</Badge>; }
