import type { DataState } from "../../types/domain";
import { Button } from "./Button";

interface StateViewProps<T> {
  state: DataState<T>;
  onRetry?: () => void;
}

export function StateView<T>({ state, onRetry }: StateViewProps<T>) {
  if (state.status === "ready") return null;
  if (state.status === "loading") return <div className="state-view" role="status">불러오는 중입니다…</div>;
  if (state.status === "empty") return <div className="state-view"><strong>표시할 데이터가 없습니다.</strong><p>{state.message}</p></div>;
  if (state.status === "not-configured") return <div className="state-view"><strong>API 연결 설정이 필요합니다.</strong><p>{state.message}</p></div>;
  return <div className="state-view state-view--error"><strong>데이터를 불러오지 못했습니다.</strong><p>{state.error.message}</p>{onRetry ? <Button variant="secondary" onClick={onRetry}>다시 시도</Button> : null}</div>;
}
