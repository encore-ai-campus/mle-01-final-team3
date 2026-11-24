export const artifactScenarioIds = [
  "LG-1", "LG-2", "LG-3", "LG-4", "LG-5", "LG-6", "LG-7", "LG-8", "LG-9", "LG-10",
  "LG-11", "LG-12", "LG-13", "LG-14", "LG-15", "LG-16", "LG-17", "LG-18", "LG-19", "LG-20",
  "LG-21", "LG-22", "LG-23", "LG-24", "LG-25", "LG-26", "LG-27", "LG-28", "LG-29", "LG-30",
  "LG-31", "LG-32", "LG-33", "LG-34", "LG-35", "LG-36", "LG-37", "LG-38", "LG-39", "LG-40",
  "LG-41",
] as const;

export type ArtifactScenarioId = (typeof artifactScenarioIds)[number];

export interface ArtifactScenario {
  id: ArtifactScenarioId;
  title: string;
  route: "/" | "/reviews" | "/reviews/:reviewId" | "/account" | "/notifications";
  expectedState: string;
  expectedInteraction: string;
}

const scenarios: Record<ArtifactScenarioId, Omit<ArtifactScenario, "id">> = {
  "LG-1": { title: "대시보드 · 할 일 바로가기", route: "/", expectedState: "ready", expectedInteraction: "할 일 선택" },
  "LG-2": { title: "대시보드 · 접수 내역 없음", route: "/", expectedState: "empty", expectedInteraction: "빈 상태 확인" },
  "LG-3": { title: "대시보드 · 할 일 모두 처리", route: "/", expectedState: "ready-empty-tasks", expectedInteraction: "완료 상태 확인" },
  "LG-4": { title: "검토함 · 계정 메뉴", route: "/account", expectedState: "menu-open", expectedInteraction: "마이페이지 또는 로그아웃 선택" },
  "LG-5": { title: "할 일 · 검토 대기", route: "/reviews", expectedState: "filtered", expectedInteraction: "검토 대기 필터" },
  "LG-6": { title: "할 일 · 검토 중", route: "/reviews", expectedState: "filtered", expectedInteraction: "검토 중 필터" },
  "LG-7": { title: "할 일 · 오늘 처리 완료", route: "/reviews", expectedState: "filtered", expectedInteraction: "오늘 처리 필터" },
  "LG-8": { title: "검토함", route: "/reviews", expectedState: "ready", expectedInteraction: "보고서 선택" },
  "LG-9": { title: "검토함 · 비어 있음", route: "/reviews", expectedState: "empty", expectedInteraction: "빈 상태 확인" },
  "LG-10": { title: "검토함 · 담당자 필터", route: "/reviews", expectedState: "filtered", expectedInteraction: "담당자 필터" },
  "LG-11": { title: "검토함 · 판단 보류 필터", route: "/reviews", expectedState: "filtered", expectedInteraction: "판단 보류 필터" },
  "LG-12": { title: "검토 보고서 · 검토 중", route: "/reviews/:reviewId", expectedState: "ready", expectedInteraction: "판정 선택" },
  "LG-13": { title: "적합 처리 확인창", route: "/reviews/:reviewId", expectedState: "dialog", expectedInteraction: "적합 확인" },
  "LG-14": { title: "적합 처리 완료", route: "/reviews", expectedState: "success", expectedInteraction: "검토함과 알림 확인" },
  "LG-15": { title: "적합 처리 저장 실패", route: "/reviews/:reviewId", expectedState: "error", expectedInteraction: "오류 확인" },
  "LG-16": { title: "PDF 저장 완료", route: "/reviews/:reviewId", expectedState: "success", expectedInteraction: "PDF 저장" },
  "LG-17": { title: "다른 담당자가 검토 중", route: "/reviews/:reviewId", expectedState: "read-only", expectedInteraction: "보고서 열람" },
  "LG-18": { title: "부적합 사유 입력", route: "/reviews/:reviewId", expectedState: "dialog", expectedInteraction: "사유 입력" },
  "LG-19": { title: "부적합 사유 입력 안내", route: "/reviews/:reviewId", expectedState: "validation", expectedInteraction: "사유 없이 제출" },
  "LG-20": { title: "부적합 사유 입력 완료", route: "/reviews/:reviewId", expectedState: "ready", expectedInteraction: "부적합 제출" },
  "LG-21": { title: "부적합 처리 완료", route: "/reviews", expectedState: "success", expectedInteraction: "검토함과 알림 확인" },
  "LG-22": { title: "부적합 처리 저장 실패", route: "/reviews/:reviewId", expectedState: "error", expectedInteraction: "입력 사유 유지" },
  "LG-23": { title: "판단 보류 보고서", route: "/reviews/:reviewId", expectedState: "ready", expectedInteraction: "판정 선택" },
  "LG-24": { title: "판단 보류 적합 확인창", route: "/reviews/:reviewId", expectedState: "dialog", expectedInteraction: "적합 확인" },
  "LG-25": { title: "판단 보류 적합 완료", route: "/reviews", expectedState: "success", expectedInteraction: "검토함과 알림 확인" },
  "LG-26": { title: "판단 보류 부적합 사유", route: "/reviews/:reviewId", expectedState: "dialog", expectedInteraction: "사유 입력" },
  "LG-27": { title: "판단 보류 부적합 입력 완료", route: "/reviews/:reviewId", expectedState: "ready", expectedInteraction: "부적합 제출" },
  "LG-28": { title: "판단 보류 부적합 완료", route: "/reviews", expectedState: "success", expectedInteraction: "검토함과 알림 확인" },
  "LG-29": { title: "검토 중 보고서 다시 열기", route: "/reviews/:reviewId", expectedState: "ready", expectedInteraction: "보고서 재열기" },
  "LG-30": { title: "검토 적합 보고서 보기", route: "/reviews/:reviewId", expectedState: "read-only", expectedInteraction: "보고서 열람" },
  "LG-31": { title: "검토 부적합 보고서 보기", route: "/reviews/:reviewId", expectedState: "read-only", expectedInteraction: "보고서 열람" },
  "LG-32": { title: "판단 보류 적합 보고서 보기", route: "/reviews/:reviewId", expectedState: "read-only", expectedInteraction: "보고서 열람" },
  "LG-33": { title: "판단 보류 부적합 보고서 보기", route: "/reviews/:reviewId", expectedState: "read-only", expectedInteraction: "보고서 열람" },
  "LG-34": { title: "새 보고서 접수", route: "/reviews/:reviewId", expectedState: "notification", expectedInteraction: "알림 확인" },
  "LG-35": { title: "알림 내역", route: "/notifications", expectedState: "ready", expectedInteraction: "알림 확인" },
  "LG-36": { title: "지난 알림만", route: "/notifications", expectedState: "historical", expectedInteraction: "알림 확인" },
  "LG-37": { title: "알림 없음", route: "/notifications", expectedState: "empty", expectedInteraction: "빈 상태 확인" },
  "LG-38": { title: "마이페이지 · 비밀번호 변경", route: "/account", expectedState: "ready", expectedInteraction: "비밀번호 입력" },
  "LG-39": { title: "비밀번호 변경 완료", route: "/account", expectedState: "success", expectedInteraction: "저장" },
  "LG-40": { title: "새 담당자 첫 로그인", route: "/account", expectedState: "notification", expectedInteraction: "알림 확인" },
  "LG-41": { title: "비밀번호 변경 알림", route: "/notifications", expectedState: "ready", expectedInteraction: "알림 확인" },
};

export const artifactScenarios: Record<ArtifactScenarioId, ArtifactScenario> = Object.fromEntries(
  artifactScenarioIds.map((id) => [id, { id, ...scenarios[id] }]),
) as Record<ArtifactScenarioId, ArtifactScenario>;
