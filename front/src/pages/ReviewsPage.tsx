import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { DataProvider, ReviewQuery } from "../types/api";
import type { DataState, ReviewTask } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { EmptyReviewState } from "../components/domain/EmptyReviewState";
import { ReviewFilterBar } from "../components/domain/ReviewFilterBar";
import { ReviewTaskTable } from "../components/domain/ReviewTaskTable";

function paramsToQuery(params: URLSearchParams): ReviewQuery { return { search: params.get("search") ?? undefined, aiJudgment: params.get("aiJudgment") ?? undefined, processingStatus: params.get("processingStatus") ?? undefined, assignee: params.get("assignee") ?? undefined, processingDate: params.get("processingDate") ?? undefined }; }
function queryToParams(query: ReviewQuery): URLSearchParams { const params = new URLSearchParams(); Object.entries(query).forEach(([key, value]) => { if (value) params.set(key, value); }); return params; }

export function ReviewsPage({ provider }: { provider: DataProvider }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = useMemo(() => paramsToQuery(searchParams), [searchParams]);
  const [state, setState] = useState<DataState<ReviewTask[]>>({ status: "loading" });
  const load = useCallback(() => { setState({ status: "loading" }); void provider.listReviews(query).then(setState); }, [provider, query]);
  useEffect(() => { load(); }, [load]);
  const updateQuery = (nextQuery: ReviewQuery) => setSearchParams(queryToParams(nextQuery));
  return <div className="page-stack"><PageHeader eyebrow="REVIEW WORKSPACE" title="검토함" description="접수된 광고 심의 보고서를 필터링하고 확인합니다." actions={<Button variant="secondary" onClick={load}>새로고침</Button>} /><Card><ReviewFilterBar value={query} onChange={updateQuery} /></Card>{state.status === "ready" ? <Card><ReviewTaskTable rows={state.data} /></Card> : state.status === "empty" ? <EmptyReviewState message={state.message} /> : <StateView state={state} onRetry={load} />}</div>;
}
