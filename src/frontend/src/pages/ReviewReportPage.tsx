import { useCallback } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { ReviewReport, ReviewReportStage } from "../types/domain";
import { useDataState } from "../hooks/useDataState";
import { PageHeader } from "../components/layout/PageHeader";
import { StateView } from "../components/ui/StateView";
import { ReviewReportPanel } from "../components/domain/ReviewReportPanel";
import { ReviewStageNavigation } from "../components/domain/ReviewStageNavigation";
import { reportStagesForReport } from "../components/domain/reviewStageNavigationData";

const stages: ReviewReportStage[] = ["marketing", "legal"];

export function ReviewReportPage({ provider }: { provider: DataProvider }) {
  const { reviewId = "", reportStage = "marketing" } = useParams();
  const { search } = useLocation();
  const stage: ReviewReportStage = stages.includes(reportStage as ReviewReportStage) ? reportStage as ReviewReportStage : "marketing";
  const load = useCallback(() => provider.getReviewReport(reviewId, stage), [provider, reviewId, stage]);
  const [state, retry] = useDataState<ReviewReport>(load);
  return <div className="page-stack"><PageHeader eyebrow="REFERENCE REPORT" title={state.status === "ready" ? state.data.title : "참조 보고서"} description="검토 과정에서 참조한 보고서 상세입니다." actions={<Link className="button button--secondary" to={`/reviews/${reviewId}${search}`}>돌아가기</Link>} />{state.status !== "ready" ? <StateView state={state} onRetry={retry} /> : <><ReviewStageNavigation reviewId={reviewId} stages={reportStagesForReport(state.data)} activeStage={state.data.stage} /><ReviewReportPanel report={state.data} /></>}</div>;
}
