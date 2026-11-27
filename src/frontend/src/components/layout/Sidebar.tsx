import type { ReactNode } from "react";
import type { UserRole } from "../../types/domain";
import { withRouteContext } from "../../utils/routeContext";

export interface ShellUser {
  name: string;
  department: string;
  role?: UserRole;
}

interface SidebarProps {
  currentPath: string;
  currentSearch: string;
  user: ShellUser;
  open: boolean;
  onNavigate: (path: string) => void;
  onClose: () => void;
  onLogout?: () => void;
}

interface NavigationItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavigationItem[] = [
  { path: "/", label: "대시보드", icon: "⌂" },
  { path: "/checks/new", label: "광고 문구 검사", icon: "✎" },
  { path: "/reviews", label: "검토함", icon: "▤" },
];

const employeeItems: NavigationItem[] = [
  { path: "/employees", label: "직원 목록", icon: "▤" },
  { path: "/employees/new", label: "직원 등록", icon: "＋" },
];

function SidebarLink({ item, active, currentSearch, onNavigate, onClose, className = "" }: { item: NavigationItem; active: boolean; currentSearch: string; onNavigate: (path: string) => void; onClose: () => void; className?: string }) {
  const href = withRouteContext(item.path, currentSearch);
  return (
    <a
      href={href}
      className={`sidebar__link ${className} ${active ? "sidebar__link--active" : ""}`}
      aria-current={active ? "page" : undefined}
      onClick={(event) => {
        event.preventDefault();
        onNavigate(href);
        onClose();
      }}
    >
      <span aria-hidden="true">{item.icon}</span>
      <span>{item.label}</span>
    </a>
  );
}

export function Sidebar({ currentPath, currentSearch, user, open, onNavigate, onClose, onLogout }: SidebarProps) {
  const isCurrent = (path: string) => path === "/" ? currentPath === path : currentPath === path || currentPath.startsWith(`${path}/`);
  return (
    <aside className={`sidebar ${open ? "sidebar--open" : ""}`} aria-label="사이드바">
      <div className="sidebar__brand">
        <span className="sidebar__logo" aria-hidden="true">F</span>
        <span>Food Guard</span>
      </div>
      <nav className="sidebar__nav" aria-label="주요 메뉴">
        {navItems.map((item) => <SidebarLink key={item.path} item={item} currentSearch={currentSearch} active={isCurrent(item.path)} onNavigate={onNavigate} onClose={onClose} />)}
        {user.role === "admin" ? <>
          <div className="sidebar__group" role="group" aria-label="직원 관리">
            <SidebarLink item={{ path: "/employees", label: "직원 관리", icon: "♙" }} currentSearch={currentSearch} active={isCurrent("/employees")} onNavigate={onNavigate} onClose={onClose} />
            <div className="sidebar__submenu" aria-label="직원 관리 하위 메뉴">
              {employeeItems.map((item) => <SidebarLink key={item.path} item={item} currentSearch={currentSearch} active={item.path === "/employees" ? currentPath === "/employees" : isCurrent(item.path)} onNavigate={onNavigate} onClose={onClose} className="sidebar__link--nested" />)}
            </div>
          </div>
        </> : null}
      </nav>
      <a className={`sidebar__user ${currentPath === "/account" ? "sidebar__user--active" : ""}`} href={withRouteContext("/account", currentSearch)} onClick={(event) => { event.preventDefault(); onNavigate(withRouteContext("/account", currentSearch)); onClose(); }} aria-label={`${user.name} 개인 정보 보기`}>
        <span className="avatar" aria-hidden="true">{user.name.slice(0, 1)}</span>
        <span>
          <strong>{user.name}</strong>
          <small>{user.department}</small>
        </span>
      </a>
      {onLogout ? <button type="button" className="sidebar__logout" onClick={onLogout}>로그아웃</button> : null}
    </aside>
  );
}

export function SidebarOverlay({ children }: { children?: ReactNode }) {
  return <>{children}</>;
}
