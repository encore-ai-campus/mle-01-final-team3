import { useState, type ReactNode } from "react";
import type { DataProvider } from "../../types/api";
import type { WorkDepartment } from "../../utils/workBadge";
import { Sidebar, type ShellUser } from "./Sidebar";
import { WorkBadge } from "./WorkBadge";

interface AppShellProps {
  children: ReactNode;
  currentPath: string;
  currentSearch?: string;
  user: ShellUser;
  onNavigate: (path: string) => void;
  provider?: DataProvider;
  workDepartment?: WorkDepartment;
}

export function AppShell({ children, currentPath, currentSearch = "", user, onNavigate, provider, workDepartment }: AppShellProps) {
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
        currentSearch={currentSearch}
        user={user}
        open={sidebarOpen}
        onNavigate={onNavigate}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="shell__content">
        <header className="shell__header">
          {provider && workDepartment ? <WorkBadge provider={provider} department={workDepartment} currentPath={currentPath} currentSearch={currentSearch} onNavigate={onNavigate} /> : null}
        </header>
        <main className="shell__main">{children}</main>
      </div>
    </div>
  );
}
