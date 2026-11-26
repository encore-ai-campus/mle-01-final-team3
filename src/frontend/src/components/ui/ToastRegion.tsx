import type { ReactNode } from "react";

export interface ToastMessage { id: string; tone: "success" | "error" | "info"; message: string; }

export function ToastRegion({ messages }: { messages: ToastMessage[] }) {
  return <div className="toast-region" aria-live="polite" aria-atomic="true">{messages.map((toast) => <div key={toast.id} className={`toast toast--${toast.tone}`}>{toast.message}</div>)}</div>;
}

export function ToastContent({ children }: { children: ReactNode }) {
  return <span>{children}</span>;
}
