import { useEffect, useState } from "react";
import type { DataProvider } from "../../types/api";
import type { ReviewReport, ReviewReportStage } from "../../types/domain";
import { reviewReportStageLabels } from "./reviewStageNavigationData";
import { ReviewReportPanel } from "./ReviewReportPanel";

interface ReviewReportTabsProps {
  provider: DataProvider;
  reviewId: string;
  activeReport: ReviewReport;
  stages: ReviewReportStage[];
}

export function ReviewReportTabs({ provider, reviewId, activeReport, stages }: ReviewReportTabsProps) {
  const [selectedStage, setSelectedStage] = useState<ReviewReportStage>(activeReport.stage);
  const [reports, setReports] = useState<Partial<Record<ReviewReportStage, ReviewReport>>>({ [activeReport.stage]: activeReport });
  const [loadingStage, setLoadingStage] = useState<ReviewReportStage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedStage(activeReport.stage);
    setReports({ [activeReport.stage]: activeReport });
    setLoadingStage(null);
    setError(null);
  }, [activeReport, reviewId]);

  const selectStage = (stage: ReviewReportStage) => {
    setSelectedStage(stage);
    setError(null);
    if (reports[stage]) return;

    setLoadingStage(stage);
    void provider.getReviewReport(reviewId, stage).then((result) => {
      setLoadingStage(null);
      if (result.status === "ready") {
        setReports((current) => ({ ...current, [stage]: result.data }));
      } else if (result.status === "error" || result.status === "not-configured") {
        setError(result.status === "error" ? result.error.message : result.message);
      } else if (result.status === "empty") {
        setError(result.message);
      } else {
        setError("보고서를 불러오지 못했습니다.");
      }
    });
  };

  const report = reports[selectedStage] ?? activeReport;

  return <section className="review-report-tabs" aria-label="보고서 목록"><div className="review-report-tabs__list" role="tablist" aria-label="검토 보고서">{stages.map((stage) => <button key={stage} className={`review-report-tabs__tab${selectedStage === stage ? " review-report-tabs__tab--active" : ""}`} type="button" role="tab" aria-selected={selectedStage === stage} aria-controls={`review-report-tabpanel-${stage}`} onClick={() => selectStage(stage)}>{reviewReportStageLabels[stage]}</button>)}</div>{loadingStage ? <p className="field__hint" role="status">{reviewReportStageLabels[loadingStage]}를 불러오는 중입니다.</p> : null}{error ? <p className="inline-error" role="alert">{error}</p> : null}<div id={`review-report-tabpanel-${selectedStage}`} role="tabpanel" aria-label={reviewReportStageLabels[selectedStage]}><ReviewReportPanel report={report} /></div></section>;
}
