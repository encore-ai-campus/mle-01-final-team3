import { Link, useLocation } from "react-router-dom";
import type { ReviewReportStage } from "../../types/domain";
import { Card } from "../ui/Card";
import { reviewReportStageLabels } from "./reviewStageNavigationData";

interface ReviewStageNavigationProps {
  reviewId: string;
  stages: ReviewReportStage[];
  activeStage?: ReviewReportStage;
}

export function ReviewStageNavigation({ reviewId, stages, activeStage }: ReviewStageNavigationProps) {
  const { search } = useLocation();
  return <Card className="review-stage-navigation"><div className="section-heading"><div><h2>검토 단계</h2><p>단계별 보고서를 확인할 수 있습니다.</p></div></div><nav aria-label="검토 보고서 단계"><ol className="review-stage-navigation__list">{stages.map((stage, index) => <li key={stage} className={stage === activeStage ? "review-stage-navigation__item--active" : undefined}><Link to={`/reviews/${reviewId}/reports/${stage}${search}`} aria-current={stage === activeStage ? "page" : undefined}><span className="review-stage-navigation__index" aria-hidden="true">{index + 1}</span><span>{reviewReportStageLabels[stage]}</span></Link></li>)}</ol></nav></Card>;
}
