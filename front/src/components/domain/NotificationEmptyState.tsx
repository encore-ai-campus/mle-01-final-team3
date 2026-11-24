export function NotificationEmptyState({ message }: { message: string }) {
  return <div className="notification-empty"><span aria-hidden="true">✓</span><strong>새로운 알림이 없습니다.</strong><p>{message}</p></div>;
}
