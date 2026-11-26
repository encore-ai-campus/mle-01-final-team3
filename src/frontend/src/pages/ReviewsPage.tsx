import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
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
export function ReviewsPage({ provider }: { provider: DataProvider }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = useMemo(() => paramsToQuery(searchParams), [searchParams]);
  const [state, setState] = useState<DataState<ReviewTask[]>>({ status: "loading" });
  const load = useCallback(() => { setState({ status: "loading" }); void provider.listReviews(query).then(setState); }, [provider, query]);
  useEffect(() => { load(); }, [load]);
  const updateQuery = (nextQuery: ReviewQuery) => {
    const nextParams = new URLSearchParams(searchParams);
    ["search", "aiJudgment", "processingStatus", "assignee", "processingDate"].forEach((key) => nextParams.delete(key));
    Object.entries(nextQuery).forEach(([key, value]) => { if (value) nextParams.set(key, value); });
    setSearchParams(nextParams);
  };
  return <div className="page-stack"><PageHeader eyebrow="REVIEW WORKSPACE" title="검토함" description="접수된 광고 심의 보고서를 필터링하고 확인합니다." actions={<Button variant="secondary" onClick={load}>새로고침</Button>} /><Card><ReviewFilterBar value={query} onChange={updateQuery} /></Card>{state.status === "ready" ? <Card><ReviewTaskTable rows={state.data} /></Card> : state.status === "empty" ? <EmptyReviewState message={state.message} /> : state.status === "not-configured" ? <><StateView state={state} onRetry={load} /><Card className="demo-entry"><strong>화면 흐름을 확인하려면</strong><p>실제 API 연결 전에는 데모 데이터로 보고서 화면을 확인할 수 있습니다.</p><Link className="button" to="/reviews?demo=true">데모 보고서 확인</Link></Card></> : <StateView state={state} onRetry={load} />}</div>;
}
