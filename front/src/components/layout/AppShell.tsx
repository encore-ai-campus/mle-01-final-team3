import { useState, type ReactNode } from "react";
import { Sidebar, type ShellUser } from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
  currentPath: string;
  user: ShellUser;
  onNavigate: (path: string) => void;
}

export function AppShell({ children, currentPath, user, onNavigate }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="shell">
      <button
        type="button"
        className="shell__menu-button"
        aria-label={sidebarOpen ? "메뉴 닫기" : "메뉴 열기"}
        aria-expanded={sidebarOpen}
        onClick={() => setSidebarOpen((value) => !value)}
      >
        <span aria-hidden="true">☰</span>
      </button>
      {sidebarOpen ? (
        <button type="button" className="shell__backdrop" aria-label="배경 닫기" onClick={() => setSidebarOpen(false)} />
      ) : null}
      <Sidebar
        currentPath={currentPath}
        user={user}
        open={sidebarOpen}
        onNavigate={onNavigate}
        onClose={() => setSidebarOpen(false)}
      />
      <main className="shell__main">{children}</main>
    </div>
  );
}
