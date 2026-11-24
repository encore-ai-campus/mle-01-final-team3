import { Link } from "react-router-dom";
import type { ReviewTask } from "../../types/domain";
import { DataTable } from "../ui/DataTable";
import { ReviewStatusBadge } from "./ReviewStatusBadge";

export function ReviewTaskTable({ rows }: { rows: ReviewTask[] }) { return <DataTable rows={rows} getRowKey={(row) => row.id} emptyState="검토 보고서가 없습니다." columns={[{ key: "title", header: "보고서", render: (row) => <Link to={`/reviews/${row.id}`}>{row.title}</Link> }, { key: "advertiser", header: "광고주", render: (row) => row.advertiser }, { key: "assignee", header: "담당자", render: (row) => row.assignee ?? "미지정" }, { key: "status", header: "처리 상태", render: (row) => <ReviewStatusBadge status={row.status} /> }, { key: "date", header: "접수일", render: (row) => row.submittedAt }]} />; }
