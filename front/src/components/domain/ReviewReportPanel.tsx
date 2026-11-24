import { Link } from "react-router-dom";
import type { ReviewReport } from "../../types/domain";
import { Card } from "../ui/Card";

export function ReviewReportPanel({ report }: { report: ReviewReport }) {
  return <Card className="workflow-report"><div className="section-heading"><div><h2>{report.title}</h2><p>{report.summary}</p></div></div><dl className="report-sections">{report.sections.map((section) => <div key={section.label}><dt>{section.label}</dt><dd>{section.value}</dd></div>)}</dl>{report.references.length > 0 ? <div><h3>참조 문서</h3><ul className="reference-list">{report.references.map((reference) => <li key={`${reference.id}-${reference.stage}`}><Link to={`/reviews/${reference.id}/reports/${reference.stage}`}>{reference.label}</Link></li>)}</ul></div> : <p className="field__hint">참조 문서가 없습니다.</p>}</Card>;
}
