import { Link } from "react-router-dom";
import type { ReviewTask } from "../../types/domain";
import { DataTable } from "../ui/DataTable";
import { Card } from "../ui/Card";
import { ReviewStatusBadge } from "./ReviewStatusBadge";

export function RecentReportTable({ reports }: { reports: ReviewTask[] }) {
  return <Card><div className="section-heading"><div><h2>최근 접수 내역</h2><p>provider가 반환한 최근 보고서입니다.</p></div></div><DataTable rows={reports} getRowKey={(row) => row.id} emptyState="최근 접수 내역이 없습니다." columns={[{ key: "title", header: "보고서", render: (row) => <Link to={`/reviews/${row.id}`}>{row.title}</Link> }, { key: "advertiser", header: "광고주", render: (row) => row.advertiser }, { key: "status", header: "처리 상태", render: (row) => <ReviewStatusBadge status={row.status} /> }]} /></Card>;
}
