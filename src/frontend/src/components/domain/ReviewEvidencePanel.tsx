import type { ReviewDetail } from "../../types/domain";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { EvidenceCard } from "./EvidenceCard";

const severityLabels = { "violation-suspected": "위반 의심", ambiguous: "애매", safe: "안전" } as const;
const severityTones = { "violation-suspected": "danger", ambiguous: "warning", safe: "success" } as const;

export function ReviewEvidencePanel({ detail }: { detail: ReviewDetail }) {
  const findings = detail.findings ?? [];
  return <Card className="review-evidence"><div className="section-heading"><div><h2>검토 근거</h2><p>AI가 표시한 문장과 적용 경로를 확인하고 담당자 판단에 참고하세요.</p></div></div>{detail.evidencePath && detail.evidencePath.length > 0 ? <ol className="evidence-path" aria-label="근거 확인 경로">{detail.evidencePath.map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}</ol> : null}{findings.length > 0 ? <div className="review-evidence__list">{findings.map((finding) => <article className="review-evidence__item" key={finding.id}><div className="finding-card__header"><Badge tone={severityTones[finding.severity]}>{severityLabels[finding.severity]}</Badge><strong>{finding.phrase}</strong></div><p>{finding.reason}</p><EvidenceCard finding={finding} /></article>)}</div> : <p className="notice-banner">연결된 AI 근거가 없습니다. 원문과 담당자 검토 기준을 확인해 주세요.</p>}</Card>;
}
