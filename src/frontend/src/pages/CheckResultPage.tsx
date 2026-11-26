import { useCallback } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import type { CheckDataProvider } from "../types/api";
import type { CheckResult } from "../types/domain";
import { useDataState } from "../hooks/useDataState";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { Badge } from "../components/ui/Badge";
import { FindingList } from "../components/domain/FindingList";
import { CheckReviewWorkflow } from "../components/domain/CheckReviewWorkflow";

export function CheckResultPage({ provider }: { provider: CheckDataProvider }) {
  const { checkId = "" } = useParams();
  const { search } = useLocation();
  const load = useCallback(() => provider.getResult(checkId), [checkId, provider]);
  const [state, retry] = useDataState<CheckResult>(load);
  return <div className="page-stack"><PageHeader eyebrow="AD CHECK › RESULT" title="검사 결과" description="법적 판단이 아닌 위반 의심 사전 점검 결과입니다." actions={<><Link className="button button--secondary" to={`/checks/new${search}`}>다시 검사하기</Link>{state.status === "ready" ? <Link className="button" to={`/progress/${state.data.id}${search}`}>진행 상황 보기</Link> : null}</>} />{state.status !== "ready" ? <StateView state={state} onRetry={retry} /> : <ResultContent result={state.data} search={search} provider={provider} />}</div>;
}

function ResultContent({ result, search, provider }: { result: CheckResult; search: string; provider: CheckDataProvider }) {
  const counts = { violation: result.findings.filter((finding) => finding.severity === "violation-suspected").length, ambiguous: result.findings.filter((finding) => finding.severity === "ambiguous").length, safe: result.findings.filter((finding) => finding.severity === "safe").length };
  return <><div className="result-summary"><Badge tone="danger">{`위반 의심 ${counts.violation}`}</Badge><Badge tone="warning">{`애매 ${counts.ambiguous}`}</Badge><Badge tone="success">{`안전 ${counts.safe}`}</Badge></div><Card><p className="page-header__eyebrow">내 광고 문구</p><h2>{result.title}</h2><p className="report-copy">{result.copy}</p><p>{result.productType} · {result.ingredient} · {result.channel}</p></Card><FindingList findings={result.findings} />{result.reviewId ? <CheckReviewWorkflow result={result} provider={provider} /> : null}<Card className="next-step"><strong>다음 단계</strong><p>{result.nextStep}</p><div className="next-step__actions">{result.reviewId ? <Link className="button" to={`/reviews/${result.reviewId}${search}`}>검토 보고서 보기</Link> : null}<Link className="button button--secondary" to={`/reviews${search}`}>검토함 보기</Link></div></Card></>;
}
