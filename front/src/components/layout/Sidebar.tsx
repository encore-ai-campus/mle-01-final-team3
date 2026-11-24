import type { ReactNode } from "react";

export interface ShellUser {
  name: string;
  department: string;
}

interface SidebarProps {
  currentPath: string;
  user: ShellUser;
  open: boolean;
  onNavigate: (path: string) => void;
  onClose: () => void;
}

const navItems = [
  { path: "/", label: "대시보드", icon: "⌂" },
  { path: "/checks/new", label: "광고 문구 검사", icon: "✎" },
  { path: "/progress", label: "진행 상황", icon: "◷" },
  { path: "/reviews", label: "검토함", icon: "▤" },
  { path: "/notifications", label: "알림", icon: "●" },
  { path: "/account", label: "마이페이지", icon: "◎" },
];

export function Sidebar({ currentPath, user, open, onNavigate, onClose }: SidebarProps) {
  const isCurrent = (path: string) => path === "/" ? currentPath === path : currentPath === path || currentPath.startsWith(`${path}/`);

  return (
    <aside className={`sidebar ${open ? "sidebar--open" : ""}`} aria-label="사이드바">
      <div className="sidebar__brand">
        <span className="sidebar__logo" aria-hidden="true">F</span>
        <span>Food Guard</span>
      </div>
      <nav className="sidebar__nav" aria-label="주요 메뉴">
        {navItems.map((item) => (
          <a
            key={item.path}
            href={item.path}
            className={`sidebar__link ${isCurrent(item.path) ? "sidebar__link--active" : ""}`}
            aria-current={isCurrent(item.path) ? "page" : undefined}
            onClick={(event) => {
              event.preventDefault();
              onNavigate(item.path);
              onClose();
            }}
          >
            <span aria-hidden="true">{item.icon}</span>
            <span>{item.label}</span>
          </a>
        ))}
      </nav>
      <div className="sidebar__user">
        <span className="avatar" aria-hidden="true">{user.name.slice(0, 1)}</span>
        <span>
          <strong>{user.name}</strong>
          <small>{user.department}</small>
        </span>
      </div>
    </aside>
  );
}

export function SidebarOverlay({ children }: { children?: ReactNode }) {
  return <>{children}</>;
}
