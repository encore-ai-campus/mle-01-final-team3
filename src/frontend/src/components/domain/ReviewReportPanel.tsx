import { Link, useLocation } from "react-router-dom";
import type { ReviewReport } from "../../types/domain";
import { Card } from "../ui/Card";

export function ReviewReportPanel({ report }: { report: ReviewReport }) {
  const { search } = useLocation();
  const result = report.sections.find((section) => section.label === "검토 결과")?.value;
  const visibleResult = result === "검토 결과 대기" ? "검토 대기" : result;
  return <Card className="workflow-report">{visibleResult ? <div className="report-result" role="status"><span>검토 결과</span><strong>{visibleResult}</strong></div> : null}<div className="section-heading"><div><h2>{report.title}</h2><p>{report.summary}</p></div></div><dl className="report-sections">{report.sections.map((section) => <div key={section.label}><dt>{section.label}</dt><dd>{section.value}</dd></div>)}</dl>{report.references.length > 0 ? <div><h3>참조 문서</h3><ul className="reference-list">{report.references.map((reference) => <li key={`${reference.id}-${reference.stage}`}><Link to={`/reviews/${reference.id}/reports/${reference.stage}${search}`}>{reference.label}</Link></li>)}</ul></div> : <p className="field__hint">참조 문서가 없습니다.</p>}</Card>;
}
