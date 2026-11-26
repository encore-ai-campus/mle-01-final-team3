import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DataState, DecisionInput, ReviewDetail, ReviewTask, ReviewUpdateInput, ReviewWorkflowAction, ReviewWorkflowRole } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { ReportMeta } from "../components/domain/ReportMeta";
import { ReviewDecisionForm } from "../components/domain/ReviewDecisionForm";
import { PdfAction } from "../components/domain/PdfAction";
import { ReviewEvidencePanel } from "../components/domain/ReviewEvidencePanel";
import { ReviewFeedbackControls } from "../components/domain/ReviewFeedbackControls";
import { ReviewReportTabs } from "../components/domain/ReviewReportTabs";
import { ReviewEditForm } from "../components/domain/ReviewEditForm";
import { ReviewWorkflowActions } from "../components/domain/ReviewWorkflowActions";
import { reportStagesForStatus } from "../components/domain/reviewStageNavigationData";

export function ReviewDetailPage({ provider, workflowRole = "unknown" }: { provider: DataProvider; workflowRole?: ReviewWorkflowRole }) {
  const { reviewId = "" } = useParams();
  const { search } = useLocation();
  const navigate = useNavigate();
  const editMode = new URLSearchParams(search).get("edit") === "true";
  const [state, setState] = useState<DataState<ReviewDetail>>({ status: "loading" });
  const [mutation, setMutation] = useState<DataState<ReviewDetail> | null>(null);
  const [editMutation, setEditMutation] = useState<DataState<ReviewTask> | null>(null);
  const startRequested = useRef(false);
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getReviewDetail(reviewId).then(setState); }, [provider, reviewId]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (state.status !== "ready" || workflowRole !== "legal" || state.data.status !== "legal-pending" || startRequested.current) return;
    startRequested.current = true;
    setMutation({ status: "loading" });
    void provider.performReviewAction({ reviewId, action: "start-legal-review", role: workflowRole }).then((result) => { setMutation(result); if (result.status === "ready") setState(result); });
  }, [provider, reviewId, state, workflowRole]);
  const submitDecision = (input: DecisionInput) => { setMutation({ status: "loading" }); void provider.submitDecision(input).then((result) => { setMutation(result); if (result.status === "ready") setState(result); }); };
  const performAction = (action: ReviewWorkflowAction, legalOpinion?: string) => { setMutation({ status: "loading" }); void provider.performReviewAction({ reviewId, action, role: workflowRole, legalOpinion }).then((result) => { setMutation(result); if (result.status === "ready") { if (action === "delete-review" || action === "complete-legal-approved" || action === "complete-legal-rejected" || action === "complete-legal-needs-revision" || action === "complete-legal-continuable" || action === "close-review") navigate(`/reviews${search}`); else setState(result); } }); };
  const detailSearch = () => { const params = new URLSearchParams(search); params.delete("edit"); const query = params.toString(); return query ? `?${query}` : ""; };
  const saveEdit = (input: ReviewUpdateInput) => { setEditMutation({ status: "loading" }); void provider.updateReview(reviewId, input).then((result) => { setEditMutation(result); if (result.status === "ready") { navigate(`/reviews/${reviewId}${detailSearch()}`, { replace: true }); void provider.getReviewDetail(reviewId).then(setState); } }); };
  return <div className="page-stack"><PageHeader eyebrow="REVIEW DETAIL" title="검토 보고서" description="보고서 원문과 처리 상태를 확인합니다." actions={<><Link className="button button--secondary" to={`/reviews${search}`}>검토함으로 돌아가기</Link>{state.status === "ready" ? <PdfAction pdfUrl={state.data.pdfUrl} /> : null}</>} />{state.status !== "ready" ? <StateView state={state} onRetry={load} /> : <>{editMode ? <ReviewEditForm detail={state.data} pending={editMutation?.status === "loading"} onSave={saveEdit} onCancel={() => navigate(`/reviews/${reviewId}${detailSearch()}`, { replace: true })} /> : null}{editMutation?.status === "error" ? <div className="inline-error" role="alert">{editMutation.error.message}</div> : null}{editMutation?.status === "ready" ? <div className="success-banner" role="status">보고서 정보가 저장되었습니다.</div> : null}<Card><h2>{state.data.title}</h2><p className="report-copy">{state.data.copy}</p>{state.data.attachments.length > 0 ? <ul>{state.data.attachments.map((attachment) => <li key={attachment}>{attachment}</li>)}</ul> : <p>첨부파일이 없습니다.</p>}</Card><ReportMeta detail={state.data} />{state.data.report ? <ReviewReportTabs provider={provider} reviewId={reviewId} stages={reportStagesForStatus(state.data.status, state.data.report)} activeReport={state.data.report} /> : null}<ReviewEvidencePanel detail={state.data} /><ReviewFeedbackControls />{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}{state.data.report && state.data.canDecide ? <ReviewWorkflowActions reviewId={reviewId} status={state.data.status} judgment={state.data.judgment} role={workflowRole} onAction={performAction} onClose={() => navigate(`/reviews${search}`)} pending={mutation?.status === "loading"} /> : <ReviewDecisionForm detail={state.data} onSubmit={submitDecision} pending={mutation?.status === "loading"} />}{mutation?.status === "ready" ? <div className="success-banner" role="status">처리가 완료되었습니다. <Button variant="ghost" onClick={() => navigate(`/reviews${search}`)}>검토함으로 이동</Button></div> : null}</>}</div>;
}
