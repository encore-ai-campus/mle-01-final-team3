import type { CheckFinding, CheckFindingSeverity } from "../../types/domain";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { EvidenceCard } from "./EvidenceCard";

const labels: Record<CheckFindingSeverity, string> = {
  "violation-suspected": "위반 의심",
  ambiguous: "애매",
  safe: "안전",
};

const tones: Record<CheckFindingSeverity, "danger" | "warning" | "success"> = {
  "violation-suspected": "danger",
  ambiguous: "warning",
  safe: "success",
};

export function FindingList({ findings }: { findings: CheckFinding[] }) {
  return <div className="finding-list">{findings.map((finding) => <Card className={`finding-card finding-card--${finding.severity}`} key={finding.id}><div className="finding-card__header"><Badge tone={tones[finding.severity]}>{labels[finding.severity]}</Badge><strong>{finding.phrase}</strong></div><p>{finding.reason}</p><EvidenceCard finding={finding} /></Card>)}</div>;
}
