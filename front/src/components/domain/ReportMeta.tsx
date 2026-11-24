import type { ReviewDetail } from "../../types/domain";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { ReviewStatusBadge } from "./ReviewStatusBadge";

export function ReportMeta({ detail }: { detail: ReviewDetail }) { return <Card className="report-meta"><div><span>처리 상태</span><ReviewStatusBadge status={detail.status} /></div><div><span>AI 판정</span><Badge tone={detail.judgment === "rejected" ? "danger" : detail.judgment === "approved" ? "success" : "warning"}>{detail.judgment}</Badge></div><div><span>담당자</span><strong>{detail.assignee ?? "미지정"}</strong></div><div><span>접수일</span><strong>{detail.submittedAt}</strong></div></Card>; }
