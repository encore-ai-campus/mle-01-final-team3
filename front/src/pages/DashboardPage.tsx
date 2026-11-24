import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DashboardSummary, DataState, NotificationFeed } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { SummaryCard } from "../components/domain/SummaryCard";
import { TaskList } from "../components/domain/TaskList";
import { RecentReportTable } from "../components/domain/RecentReportTable";
import { NotificationPanel } from "../components/domain/NotificationPanel";

export function DashboardPage({ provider }: { provider: DataProvider }) {
  const [state, setState] = useState<DataState<DashboardSummary>>({ status: "loading" });
  const [notifications, setNotifications] = useState<DataState<NotificationFeed> | null>(null);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getDashboard().then(setState); }, [provider]);
  useEffect(() => { load(); }, [load]);
  const openNotifications = () => { setNotificationOpen(true); void provider.listNotifications().then(setNotifications); };
  const markAllRead = () => { void provider.markNotificationsRead().then(setNotifications); };

  return <div className="page-stack"><PageHeader eyebrow="FOOD GUARD" title="대시보드" description="식품 광고 심의 후속조치 현황을 확인하세요." actions={<><Link className="button" to="/checks/new">+ 새 광고 문구 검사</Link><Button variant="secondary" onClick={load}>새로고침</Button><Button onClick={openNotifications}>알림 확인</Button></>} />{notificationOpen && notifications ? <NotificationPanel state={notifications} onMarkAllRead={markAllRead} onClose={() => setNotificationOpen(false)} /> : null}{state.status !== "ready" ? <StateView state={state} onRetry={load} /> : <><div className="summary-grid"><SummaryCard label="검토 대기" value={state.data.pendingCount} tone="warning" /><SummaryCard label="검토 중" value={state.data.inProgressCount} tone="info" /><SummaryCard label="오늘 처리 완료" value={state.data.completedTodayCount} tone="success" /></div><div className="dashboard-grid"><TaskList tasks={state.data.tasks} /><RecentReportTable reports={state.data.recentReports} /></div></>}<Card className="quick-link"><strong>검토함에서 전체 보고서를 확인하세요.</strong><Link to="/reviews">검토함에서 보기</Link></Card></div>;
}
