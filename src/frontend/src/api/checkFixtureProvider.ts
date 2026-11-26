import type { CheckDataProvider } from "../types/api";
import type {
  CheckDraftResult,
  CheckInput,
  CheckProgress,
  CheckResult,
  CheckStartResult,
  CheckRecommendationResult,
  MarketingWorkflowActionInput,
  DataState,
  ReviewDetail,
} from "../types/domain";
import type { ArtifactScenarioId } from "../fixtures/artifactScenarios";
import type { FixtureWorkflowStore } from "./fixtureWorkflowStore";
import { createFixtureWorkflowStore } from "./fixtureWorkflowStore";

export class FixtureCheckProvider implements CheckDataProvider {
  private readonly workflowStore: FixtureWorkflowStore;
  private recheckSequence = 0;

  public constructor(private readonly scenarioId: ArtifactScenarioId = "LG-1", workflowStore?: FixtureWorkflowStore) {
    this.workflowStore = workflowStore ?? createFixtureWorkflowStore();
  }

  public async getResult(checkId: string): Promise<DataState<CheckResult>> {
    const stored = this.workflowStore.getCheckResult(checkId) ?? createFixtureResult(checkId);
    this.workflowStore.saveCheckResult(stored);
    return { status: "ready", data: stored };
  }

  public async saveDraft(input: CheckInput): Promise<DataState<CheckDraftResult>> {
    void input;
    return { status: "ready", data: { draftId: "fixture-draft-1" } };
  }

  public async startCheck(input: CheckInput): Promise<DataState<CheckStartResult>> {
    const result = createFixtureResult("fixture-check-1", input);
    this.workflowStore.saveCheckResult(result);
    return { status: "ready", data: { checkId: result.id, progressId: result.id, reviewId: result.reviewId ?? undefined } };
  }

  public async getProgress(checkId: string): Promise<DataState<CheckProgress>> {
    return { status: "ready", data: createFixtureProgress(checkId) };
  }

  public async requestRecommendation(checkId: string): Promise<DataState<CheckRecommendationResult>> {
    const result = await this.getResult(checkId);
    const recommendations = result.status === "ready" ? result.data.recommendations ?? ["건강한 생활에 도움을 줄 수 있어요"] : ["건강한 생활에 도움을 줄 수 있어요"];
    return { status: "ready", data: { checkId, recommendations, selectedRecommendation: recommendations[0] ?? "건강한 생활에 도움을 줄 수 있어요" } };
  }

  public async requestAdCheck(input: CheckInput): Promise<DataState<CheckStartResult>> {
    const checkId = `fixture-check-recheck-${++this.recheckSequence}`;
    const result = createFixtureResult(checkId, input);
    this.workflowStore.saveCheckResult(result);
    return { status: "ready", data: { checkId, progressId: checkId, reviewId: result.reviewId ?? undefined } };
  }

  public async performMarketingAction(input: MarketingWorkflowActionInput): Promise<DataState<CheckResult>> {
    const result = await this.getResult(input.checkId);
    if (result.status !== "ready") return result;
    if (!input.reviewId) return { status: "error", error: { kind: "unknown", message: "연결된 검토 문서를 찾을 수 없습니다." } };
    const existing = this.workflowStore.getReview(input.reviewId);
    const current = existing ?? createReviewFromCheckResult(result.data, input.reviewId);
    const nextStatus = input.action === "request-legal-review" ? "legal-pending" : "marketing-cancelled";
    this.workflowStore.saveReview({
      ...current,
      status: nextStatus,
      judgment: input.action === "cancel-review" ? "rejected" : "pending",
      report: undefined,
    });
    return { status: "ready", data: result.data };
  }
}

function createFixtureResult(id: string, input?: CheckInput): CheckResult {
  const rejected = !input || /(보장|치료|완치|최고)/.test(input.copy);
  return {
    id,
    title: input?.title ?? "저당 에너지바 광고",
    productType: input?.productType ?? "health-functional-food",
    ingredient: input?.ingredient ?? "난소화성말토덱스트린",
    channel: input?.channel ?? "상세페이지",
    copy: input?.copy ?? "하루 한 포로 가볍게, 부담 없이 건강한 에너지를 채워 보세요.",
    attachments: input?.attachments ?? [{ id: "fixture-attachment-1", name: "저당-에너지바-광고시안.pdf", size: 128000, type: "application/pdf" }],
    findings: rejected ? [
      {
        id: "fixture-finding-1",
        severity: "violation-suspected",
        phrase: "효과를 보장합니다",
        reason: "효과를 단정하는 표현은 확인이 필요합니다.",
        allowedCopy: "건강한 생활에 도움을 줄 수 있어요",
        evidence: [{ label: "적용 조항", source: "확인된 API 연결 후 표시됩니다.", href: null }],
        alternatives: ["건강한 생활에 도움을 줄 수 있어요"],
      },
      {
        id: "fixture-finding-2",
        severity: "ambiguous",
        phrase: "매일 꼭 필요한",
        reason: "문맥에 따라 판단이 달라질 수 있습니다.",
        allowedCopy: null,
        evidence: [],
        alternatives: [],
      },
      {
        id: "fixture-finding-3",
        severity: "safe",
        phrase: "예시 원료 함유",
        reason: "원료 정보를 사실대로 표시한 문장입니다.",
        allowedCopy: null,
        evidence: [],
        alternatives: [],
      },
    ] : [{ id: "fixture-finding-safe", severity: "safe", phrase: "건강한 생활에 도움을 줄 수 있어요", reason: "효과를 단정하지 않는 표현입니다.", allowedCopy: null, evidence: [], alternatives: [] }],
    reviewId: "fixture-review-1",
    nextStep: rejected ? "위반 의심이 있어 법무팀 검토 또는 AI 추천을 진행합니다." : "적합 결과를 확인하고 법무팀 검토를 요청할 수 있습니다.",
    reviewJudgments: { first: rejected ? "rejected" : "approved", second: "approved" },
    marketingJudgment: rejected ? "rejected" : "approved",
    recommendations: rejected ? ["건강한 생활에 도움을 줄 수 있어요"] : [],
  };
}

function createReviewFromCheckResult(result: CheckResult, reviewId: string): ReviewDetail {
  return {
    id: reviewId,
    title: result.title,
    advertiser: "푸드가드 식품",
    author: "김마케팅",
    category: result.productType === "health-functional-food" ? "건강기능식품" : "일반식품",
    submittedAt: new Date().toISOString(),
    sentAt: new Date().toISOString(),
    status: result.marketingJudgment === "approved" ? "marketing-completed-approved" : "marketing-completed-rejected",
    judgment: result.marketingJudgment === "approved" ? "approved" : "rejected",
    assignee: "예시 담당자",
    processedAt: null,
    ownerId: "fixture-user",
    copy: result.copy,
    attachments: result.attachments.map((attachment) => attachment.name),
    findings: result.findings,
    evidencePath: ["광고 문구", "AI 자동 검사"],
    canDecide: true,
    readOnlyReason: null,
    decisionReason: null,
    legalOpinion: null,
    pdfUrl: null,
  };
}

function createFixtureProgress(id: string): CheckProgress {
  return {
    id,
    title: "저당 에너지바 광고",
    currentStep: "ra-review",
    owner: "예시 담당자",
    requestedAt: "fixture-date",
    steps: [
      { id: "copy", label: "문구 작성", status: "completed", owner: "마케팅팀", detail: "문구가 제출되었습니다." },
      { id: "check", label: "자동 검사", status: "completed", owner: "AI 에이전트", detail: "위반 의심과 애매 문장을 확인했습니다." },
      { id: "ra-review", label: "RA 검토", status: "in-progress", owner: "RA팀", detail: "담당자 검토를 기다리고 있습니다." },
      { id: "legal-review", label: "법무 검토", status: "skipped", owner: "법무팀", detail: "질병·의약품 오인 의심 시 진행됩니다." },
      { id: "approval", label: "팀장 승인", status: "waiting", owner: "마케팅팀장", detail: "앞 단계 완료 후 진행됩니다." },
      { id: "publish", label: "게시", status: "waiting", owner: "마케팅팀", detail: "승인 후 게시할 수 있습니다." },
    ],
    history: [
      { id: "history-1", actor: "마케팅팀", action: "문구 제출", createdAt: "fixture-date" },
      { id: "history-2", actor: "AI 에이전트", action: "자동 검사 완료", createdAt: "fixture-date" },
      { id: "history-3", actor: "시스템", action: "RA팀 검토 배정", createdAt: "fixture-date" },
    ],
  };
}
