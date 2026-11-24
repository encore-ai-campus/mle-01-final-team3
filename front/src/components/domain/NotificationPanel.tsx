import type { DataState } from "../../types/domain";
import type { NotificationFeed } from "../../types/domain";
import { Button } from "../ui/Button";
import { StateView } from "../ui/StateView";
import { NotificationEmptyState } from "./NotificationEmptyState";

interface NotificationPanelProps {
  state: DataState<NotificationFeed>;
  onMarkAllRead: () => void;
  onClose: () => void;
}

export function NotificationPanel({ state, onMarkAllRead, onClose }: NotificationPanelProps) {
  return <aside className="notification-panel" aria-label="알림 패널"><div className="section-heading"><div><h2>알림</h2><p>새로운 작업과 처리 결과를 확인하세요.</p></div><Button variant="ghost" aria-label="알림 닫기" onClick={onClose}>닫기</Button></div>{state.status === "ready" ? state.data.notifications.length === 0 ? <NotificationEmptyState message="확인할 알림이 없습니다." /> : <><ul className="notification-list">{state.data.notifications.map((item) => <li key={item.id} className={item.read ? "notification-list__item" : "notification-list__item notification-list__item--new"}><strong>{item.title}</strong><p>{item.message}</p><small>{item.createdAt}</small></li>)}</ul><Button variant="secondary" onClick={onMarkAllRead}>모두 읽음 처리</Button></> : state.status === "empty" ? <NotificationEmptyState message={state.message} /> : <StateView state={state} />}</aside>;
}
