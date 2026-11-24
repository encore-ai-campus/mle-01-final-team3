import { useCallback, useEffect, useState } from "react";
import type { DataProvider } from "../types/api";
import type { DataState, NotificationFeed } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { NotificationPanel } from "../components/domain/NotificationPanel";

export function NotificationsPage({ provider }: { provider: DataProvider }) {
  const [state, setState] = useState<DataState<NotificationFeed>>({ status: "loading" });
  const load = useCallback(() => { setState({ status: "loading" }); void provider.listNotifications().then(setState); }, [provider]);
  useEffect(() => { load(); }, [load]);
  const markAllRead = () => { void provider.markNotificationsRead().then(setState); };
  return <div className="page-stack"><PageHeader eyebrow="ACTIVITY" title="알림" description="새로운 작업과 처리 결과를 확인하세요." /><NotificationPanel state={state} onMarkAllRead={markAllRead} onClose={() => undefined} /></div>;
}
