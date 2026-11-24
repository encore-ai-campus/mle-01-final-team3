import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import type { CheckDataProvider } from "../types/api";
import type { CheckProgress } from "../types/domain";
import { useDataState } from "../hooks/useDataState";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { CheckProgressStepper } from "../components/domain/CheckProgressStepper";

export function ProgressPage({ provider }: { provider: CheckDataProvider }) {
  const { checkId = "fixture-check-1" } = useParams();
  const load = useCallback(() => provider.getProgress(checkId), [checkId, provider]);
  const [state, retry] = useDataState<CheckProgress>(load);
  return <div className="page-stack"><PageHeader eyebrow="PROGRESS" title="진행 상황" description="광고 심의 업무가 지금 어디까지 진행됐는지 확인합니다." actions={<><Link className="button button--secondary" to={`/checks/${checkId}`}>검사 결과</Link><Link className="button" to="/reviews">검토함 보기</Link></>} />{state.status !== "ready" ? <StateView state={state} onRetry={retry} /> : <><Card><h2>{state.data.title}</h2><p>현재 단계: <strong>{state.data.steps.find((step) => step.id === state.data.currentStep)?.label ?? state.data.currentStep}</strong></p><CheckProgressStepper steps={state.data.steps} currentStep={state.data.currentStep} /></Card><Card><h2>처리 기록</h2><ul className="history-list">{state.data.history.map((item) => <li key={item.id}><time>{item.createdAt}</time><span><strong>{item.actor}</strong>{item.action}</span></li>)}</ul></Card></>}</div>;
}
