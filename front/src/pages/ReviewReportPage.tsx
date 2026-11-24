import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { ReviewReport, ReviewReportStage } from "../types/domain";
import { useDataState } from "../hooks/useDataState";
import { PageHeader } from "../components/layout/PageHeader";
import { StateView } from "../components/ui/StateView";
import { ReviewReportPanel } from "../components/domain/ReviewReportPanel";

const stages: ReviewReportStage[] = ["first-review", "second-review", "legal-review"];

export function ReviewReportPage({ provider }: { provider: DataProvider }) {
  const { reviewId = "", reportStage = "first-review" } = useParams();
  const stage: ReviewReportStage = stages.includes(reportStage as ReviewReportStage) ? reportStage as ReviewReportStage : "first-review";
  const load = useCallback(() => provider.getReviewReport(reviewId, stage), [provider, reviewId, stage]);
  const [state, retry] = useDataState<ReviewReport>(load);
  return <div className="page-stack"><PageHeader eyebrow="REFERENCE REPORT" title="참조 보고서" description="검토 과정에서 참조한 보고서 상세입니다." actions={<Link className="button button--secondary" to={`/reviews/${reviewId}`}>돌아가기</Link>} />{state.status !== "ready" ? <StateView state={state} onRetry={retry} /> : <ReviewReportPanel report={state.data} />}</div>;
}
