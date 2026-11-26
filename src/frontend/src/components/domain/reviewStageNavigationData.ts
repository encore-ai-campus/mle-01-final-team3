import type { ReviewReport, ReviewReportStage, ReviewStatus } from "../../types/domain";

export const reviewReportStageLabels: Record<ReviewReportStage, string> = {
  "first-review": "1차 검토 보고서",
  "second-review": "2차 검토 보고서",
  "legal-review": "법무팀 검토 보고서",
  completed: "검토 완료 보고서",
  marketing: "[마케팅]광고 문구 검토 보고서",
  legal: "[법무]광고 문구 검토 보고서",
};

const reportStageOrder: ReviewReportStage[] = ["marketing", "legal"];

export function reportStagesForReport(report: ReviewReport): ReviewReportStage[] {
  const available = new Set<ReviewReportStage>([report.stage, ...report.references.map((reference) => reference.stage)]);
  return reportStageOrder.filter((stage) => available.has(stage));
}

export function reportStagesForStatus(status: ReviewStatus, report?: ReviewReport): ReviewReportStage[] {
  if (report) return reportStagesForReport(report);
  if (status === "legal-pending" || status === "legal-in-progress" || status === "legal-completed-approved" || status === "legal-completed-rejected" || status === "legal-completed-needs-revision" || status === "legal-completed-continuable" || status === "legal-review" || status === "completed") return ["marketing", "legal"];
  return ["marketing"];
}
