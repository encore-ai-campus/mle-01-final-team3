import type { CheckFinding } from "../../types/domain";

export function EvidenceCard({ finding }: { finding: CheckFinding }) {
  return <div className="evidence-card"><div><h3>근거</h3>{finding.evidence.length > 0 ? <ul>{finding.evidence.map((item) => <li key={`${item.label}-${item.source}`}>{item.href ? <a href={item.href}>{item.label}</a> : <strong>{item.label}</strong>}<span>{item.source}</span></li>)}</ul> : <p>근거 자료가 없습니다.</p>}</div><div><h3>대안 문구</h3>{finding.alternatives.length > 0 ? <ul>{finding.alternatives.map((alternative) => <li key={alternative}>{alternative}</li>)}</ul> : <p>적용할 대안 문구가 없습니다.</p>}</div></div>;
}
