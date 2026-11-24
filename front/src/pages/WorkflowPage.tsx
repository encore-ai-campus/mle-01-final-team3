import { Link } from "react-router-dom";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";

const stages = [
  { label: "문구 작성", owner: "마케팅팀", status: "완료", tone: "success" as const, detail: "광고 문구와 첨부 자료가 접수됩니다." },
  { label: "자동 검사", owner: "AI 에이전트", status: "완료", tone: "success" as const, detail: "위반 의심 문장과 근거를 생성합니다." },
  { label: "1차 검토", owner: "RA팀", status: "진행 중", tone: "info" as const, detail: "광고 문구의 규정 적합성을 검토합니다." },
  { label: "2차 검토", owner: "RA팀", status: "대기", tone: "neutral" as const, detail: "1차 검토 결과에 따라 추가 검토합니다." },
  { label: "법무팀 검토", owner: "법무팀", status: "대기", tone: "neutral" as const, detail: "법적 위험과 최종 승인 여부를 검토합니다." },
  { label: "검토 완료", owner: "시스템", status: "대기", tone: "neutral" as const, detail: "검토 결과를 마케팅팀에 전달합니다." },
];

export function WorkflowPage() {
  return <div className="page-stack"><PageHeader eyebrow="ADMIN" title="업무 흐름 시각화" description="광고 심의 후속조치의 단계와 담당 부서를 확인합니다." actions={<Link className="button button--secondary" to="/">대시보드</Link>} /><div className="workflow-grid" aria-label="업무 흐름 단계">{stages.map((stage, index) => <Card className={`workflow-stage workflow-stage--${stage.tone}`} key={stage.label}><div className="workflow-stage__index">{index + 1}</div><div><div className="workflow-stage__header"><h2>{stage.label}</h2><Badge tone={stage.tone}>{stage.status}</Badge></div><strong>{stage.owner}</strong><p>{stage.detail}</p></div></Card>)}</div></div>;
}
