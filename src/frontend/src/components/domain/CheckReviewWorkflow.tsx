import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { CheckDataProvider } from "../../types/api";
import type { CheckInput, CheckRecommendationResult, CheckResult, DataState, ReviewReport } from "../../types/domain";
import { withRouteContext } from "../../utils/routeContext";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { ReviewReportPanel } from "./ReviewReportPanel";
import { RecommendationDialog } from "./RecommendationDialog";

interface CheckReviewWorkflowProps {
  result: CheckResult;
  provider: CheckDataProvider;
}

export function CheckReviewWorkflow({ result, provider }: CheckReviewWorkflowProps) {
  const navigate = useNavigate();
  const { search } = useLocation();
  const [mutation, setMutation] = useState<DataState<CheckResult> | null>(null);
  const [recommendationState, setRecommendationState] = useState<DataState<CheckRecommendationResult> | null>(null);
  const [recommendationOpen, setRecommendationOpen] = useState(false);
  const judgment = result.marketingJudgment ?? (result.findings.some((finding) => finding.severity === "violation-suspected") ? "rejected" : "approved");
  const report = useMemo<ReviewReport>(() => ({
    stage: "marketing",
    title: "[마케팅]광고 문구 검토 보고서",
    summary: "광고 문구 검사 Agent가 생성한 마케팅 검토 결과입니다.",
    sections: [
      { label: "검토 결과", value: judgment === "approved" ? "적합" : "부적합" },
      { label: "광고 문구", value: result.copy },
      { label: "검토 안내", value: judgment === "approved" ? "법무팀 검토 요청 또는 검토함 저장을 선택하세요." : "추천 광고 문구를 확인하거나 심의를 취소할 수 있습니다." },
      ...(judgment === "rejected" && result.recommendations?.[0] ? [{ label: "추천 광고 문구", value: result.recommendations[0] }] : []),
    ],
    references: [],
  }), [judgment, result.copy]);

  const close = () => navigate(withRouteContext("/reviews", search));
  const runMarketingAction = async (action: "request-legal-review" | "cancel-review") => {
    setMutation({ status: "loading" });
    const next = await provider.performMarketingAction({ checkId: result.id, reviewId: result.reviewId ?? "", action });
    setMutation(next);
    if (next.status === "ready") close();
  };
  const requestRecommendation = async () => {
    setRecommendationState({ status: "loading" });
    const next = await provider.requestRecommendation(result.id);
    setRecommendationState(next);
    if (next.status === "ready") setRecommendationOpen(true);
  };
  const requestAdCheck = async () => {
    const recommendation = recommendationState?.status === "ready" ? recommendationState.data.selectedRecommendation : "";
    if (!recommendation) return;
    const input: CheckInput = { title: result.title, productType: result.productType, ingredient: result.ingredient, channel: result.channel, copy: recommendation, attachments: result.attachments };
    setRecommendationState({ status: "loading" });
    const next = await provider.requestAdCheck(input);
    if (next.status === "ready") {
      setRecommendationState({ status: "ready", data: { checkId: next.data.checkId, recommendations: [recommendation], selectedRecommendation: recommendation } });
      navigate(withRouteContext(`/checks/${next.data.checkId}`, search));
    } else {
      setRecommendationState(next);
    }
  };
  const error = mutation?.status === "error" ? mutation.error.message : recommendationState?.status === "error" ? recommendationState.error.message : null;

  return (
    <>
      <Card className="check-review-workflow">
        <div className="section-heading">
          <div><h3>{report.title}</h3><p>검토 결과를 확인하고 다음 업무를 진행하세요.</p></div>
          <Badge tone={judgment === "approved" ? "success" : "danger"}>{judgment === "approved" ? "적합" : "부적합"}</Badge>
        </div>
        <ReviewReportPanel report={report} />
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <div className="workflow-actions">
          {judgment === "approved" ? <Button onClick={() => void runMarketingAction("request-legal-review")} disabled={mutation?.status === "loading"}>법무팀 검토 요청</Button> : <><Button variant="danger" onClick={() => void runMarketingAction("cancel-review")} disabled={mutation?.status === "loading"}>심의 취소</Button><Button onClick={() => void requestRecommendation()} disabled={recommendationState?.status === "loading"}>AI 추천 요청</Button></>}
          <Button variant="secondary" onClick={close} disabled={mutation?.status === "loading"}>닫기</Button>
        </div>
      </Card>
      <RecommendationDialog open={recommendationOpen && recommendationState?.status === "ready"} recommendation={recommendationState?.status === "ready" ? recommendationState.data.selectedRecommendation : ""} pending={recommendationState?.status === "loading"} onRequestCheck={() => void requestAdCheck()} onClose={close} />
    </>
  );
}
