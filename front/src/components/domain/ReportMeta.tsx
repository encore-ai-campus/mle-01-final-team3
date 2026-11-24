import type { ReviewDetail } from "../../types/domain";
import { Card } from "../ui/Card";
import { ReviewStatusBadge } from "./ReviewStatusBadge";

export function ReportMeta({ detail }: { detail: ReviewDetail }) { return <Card className="report-meta"><div><span>상태</span><ReviewStatusBadge status={detail.status} /></div><div><span>작성자</span><strong>{detail.author}</strong></div><div><span>분류</span><strong>{detail.category}</strong></div><div><span>전송일</span><strong>{detail.sentAt}</strong></div></Card>; }
