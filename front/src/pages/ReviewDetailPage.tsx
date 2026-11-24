import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DataState, DecisionInput, ReviewDetail } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { ReportMeta } from "../components/domain/ReportMeta";
import { ReviewDecisionForm } from "../components/domain/ReviewDecisionForm";
import { PdfAction } from "../components/domain/PdfAction";

export function ReviewDetailPage({ provider }: { provider: DataProvider }) {
  const { reviewId = "" } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<DataState<ReviewDetail>>({ status: "loading" });
  const [mutation, setMutation] = useState<DataState<ReviewDetail> | null>(null);
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getReviewDetail(reviewId).then(setState); }, [provider, reviewId]);
  useEffect(() => { load(); }, [load]);
  const submitDecision = (input: DecisionInput) => { setMutation({ status: "loading" }); void provider.submitDecision(input).then((result) => { setMutation(result); if (result.status === "ready") setState(result); }); };
  return <div className="page-stack"><PageHeader eyebrow="REVIEW DETAIL" title="검토 보고서" description="보고서 원문과 처리 상태를 확인합니다." actions={<><Link className="button button--secondary" to="/reviews">검토함으로 돌아가기</Link>{state.status === "ready" ? <PdfAction pdfUrl={state.data.pdfUrl} /> : null}</>} />{state.status !== "ready" ? <StateView state={state} onRetry={load} /> : <><Card><h2>{state.data.title}</h2><p className="report-copy">{state.data.copy}</p>{state.data.attachments.length > 0 ? <ul>{state.data.attachments.map((attachment) => <li key={attachment}>{attachment}</li>)}</ul> : <p>첨부파일이 없습니다.</p>}</Card><ReportMeta detail={state.data} />{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}<ReviewDecisionForm detail={state.data} onSubmit={submitDecision} pending={mutation?.status === "loading"} />{mutation?.status === "ready" ? <div className="success-banner" role="status">처리가 완료되었습니다. <Button variant="ghost" onClick={() => navigate("/reviews")}>검토함으로 이동</Button></div> : null}</>}</div>;
}
