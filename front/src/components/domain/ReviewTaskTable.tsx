import { Link } from "react-router-dom";
import type { ReviewTask } from "../../types/domain";
import { DataTable } from "../ui/DataTable";
import { ReviewStatusBadge } from "./ReviewStatusBadge";

export function ReviewTaskTable({ rows }: { rows: ReviewTask[] }) { return <DataTable rows={rows} getRowKey={(row) => row.id} emptyState="검토 보고서가 없습니다." columns={[{ key: "title", header: "광고명", render: (row) => row.title }, { key: "author", header: "작성자", render: (row) => row.author }, { key: "category", header: "분류", render: (row) => row.category }, { key: "status", header: "상태", render: (row) => <ReviewStatusBadge status={row.status} /> }, { key: "sentAt", header: "전송일", render: (row) => row.sentAt }, { key: "detail", header: "상세 보기", render: (row) => <Link className="button button--secondary button--compact" to={`/reviews/${row.id}`}>상세 보기</Link> }]} />; }
