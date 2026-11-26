import { useCallback, useEffect, useState } from "react";
import type { DataProvider } from "../types/api";
import type { DashboardSummary, DataState } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { StateView } from "../components/ui/StateView";
import { SummaryCard } from "../components/domain/SummaryCard";
import { TaskList } from "../components/domain/TaskList";
import { RecentReportTable } from "../components/domain/RecentReportTable";

export function DashboardPage({ provider }: { provider: DataProvider }) {
  const [state, setState] = useState<DataState<DashboardSummary>>({ status: "loading" });
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getDashboard().then(setState); }, [provider]);
  useEffect(() => { load(); }, [load]);

  return (
    <div className="page-stack">
      <PageHeader eyebrow="FOOD GUARD" title="대시보드" description="식품 광고 심의 후속조치 현황을 확인하세요." />
      {state.status !== "ready" ? <StateView state={state} onRetry={load} /> : (
        <>
          <div className="summary-grid">
            <SummaryCard label="검토 대기" value={state.data.pendingCount} tone="warning" />
            <SummaryCard label="검토 중" value={state.data.inProgressCount} tone="info" />
            <SummaryCard label="오늘 처리 완료" value={state.data.completedTodayCount} tone="success" />
          </div>
          <div className="dashboard-grid">
            <TaskList tasks={state.data.tasks} />
            <RecentReportTable reports={state.data.recentReports} />
          </div>
        </>
      )}
    </div>
  );
}
