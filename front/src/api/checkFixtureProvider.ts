import type { CheckDataProvider } from "../types/api";
import type {
  CheckDraftResult,
  CheckInput,
  CheckProgress,
  CheckResult,
  CheckStartResult,
  DataState,
} from "../types/domain";

export class FixtureCheckProvider implements CheckDataProvider {
  public async getResult(checkId: string): Promise<DataState<CheckResult>> {
    return { status: "ready", data: createFixtureResult(checkId) };
  }

  public async saveDraft(input: CheckInput): Promise<DataState<CheckDraftResult>> {
    void input;
    return { status: "ready", data: { draftId: "fixture-draft-1" } };
  }

  public async startCheck(input: CheckInput): Promise<DataState<CheckStartResult>> {
    void input;
    return { status: "ready", data: { checkId: "fixture-check-1", progressId: "fixture-check-1" } };
  }

  public async getProgress(checkId: string): Promise<DataState<CheckProgress>> {
    return { status: "ready", data: createFixtureProgress(checkId) };
  }
}

function createFixtureResult(id: string): CheckResult {
  return {
    id,
    title: "예시 광고 상세페이지",
    productType: "health-functional-food",
    ingredient: "예시 원료",
    channel: "상세페이지",
    copy: "예시 광고 문구는 실제 API 연결 후 표시됩니다.",
    attachments: [],
    findings: [
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
    ],
    reviewId: "fixture-review-1",
    nextStep: "위반 의심이 있어 RA팀 검토를 요청합니다.",
  };
}

function createFixtureProgress(id: string): CheckProgress {
  return {
    id,
    title: "예시 광고 상세페이지",
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
