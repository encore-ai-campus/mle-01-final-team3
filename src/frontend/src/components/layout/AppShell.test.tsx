import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("renders navigation labels and current route state", () => {
    render(
      <AppShell
        currentPath="/reviews"
        user={{ name: "담당자", department: "legal", role: "reviewer" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.getByRole("navigation", { name: "주요 메뉴" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "검토함" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "광고 문구 검사" })).toHaveAttribute("href", "/checks/new");
    expect(screen.queryByRole("link", { name: "진행 상황" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "마이페이지" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "담당자 개인 정보 보기" })).toHaveAttribute("href", "/account");
    expect(screen.getByRole("main")).toHaveTextContent("본문");
  });

  it("shows employee management only for an admin", () => {
    render(
      <AppShell
        currentPath="/workflow"
        user={{ name: "관리자", department: "관리자", role: "admin" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.queryByRole("link", { name: "업무 흐름 시각화" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "직원 관리" })).toHaveAttribute("href", "/employees");
    expect(screen.getByRole("link", { name: "직원 목록" })).toHaveAttribute("href", "/employees");
    expect(screen.getByRole("link", { name: "직원 등록" })).toHaveAttribute("href", "/employees/new");
  });

  it("does not render a demo-mode menu in the shell", () => {
    render(
      <AppShell
        currentPath="/"
        user={{ name: "담당자", department: "legal", role: "reviewer" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.queryByRole("region", { name: "시연 모드" })).not.toBeInTheDocument();
  });

  it("hides employee navigation from non-admin users", () => {
    render(
      <AppShell
        currentPath="/"
        user={{ name: "담당자", department: "legal", role: "reviewer" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.queryByRole("link", { name: "직원 관리" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "직원 목록" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "직원 등록" })).not.toBeInTheDocument();
  });

  it("opens and closes the mobile navigation with an accessible button", async () => {
    const user = userEvent.setup();
    render(
      <AppShell
        currentPath="/"
        user={{ name: "담당자", department: "legal", role: "reviewer" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    const menuButton = screen.getByRole("button", { name: "메뉴 열기" });
    await user.click(menuButton);
    expect(screen.getByRole("button", { name: "메뉴 닫기" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "메뉴 닫기" }));
    expect(screen.getByRole("button", { name: "메뉴 열기" })).toBeInTheDocument();
  });

  it("shows employee list and registration links with route-specific active state for admins", () => {
    const { rerender } = render(
      <AppShell
        currentPath="/employees"
        user={{ name: "관리자", department: "관리자", role: "admin" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.getByRole("link", { name: "직원 관리" })).toHaveAttribute("href", "/employees");
    expect(screen.getByRole("group", { name: "직원 관리" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "직원 목록" })).toHaveAttribute("href", "/employees");
    expect(screen.getByRole("link", { name: "직원 등록" })).toHaveAttribute("href", "/employees/new");
    expect(screen.getByRole("link", { name: "직원 목록" })).toHaveAttribute("aria-current", "page");

    rerender(
      <AppShell
        currentPath="/employees/new"
        user={{ name: "관리자", department: "관리자", role: "admin" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.getByRole("link", { name: "직원 관리" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "직원 등록" })).toHaveAttribute("aria-current", "page");
  });

  it("preserves demo and admin context in sidebar links", () => {
    render(
      <AppShell
        currentPath="/employees"
        currentSearch="?demo=true&role=admin"
        user={{ name: "관리자", department: "관리자", role: "admin" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.getByRole("link", { name: "직원 등록" })).toHaveAttribute("href", "/employees/new?demo=true&role=admin");
  });

  it("navigates to employee registration and closes the mobile admin menu", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    render(
      <AppShell
        currentPath="/"
        user={{ name: "관리자", department: "관리자", role: "admin" }}
        onNavigate={onNavigate}
      >
        <p>본문</p>
      </AppShell>,
    );

    await user.click(screen.getByRole("button", { name: "메뉴 열기" }));
    await user.click(screen.getByRole("link", { name: "직원 등록" }));

    expect(onNavigate).toHaveBeenCalledWith("/employees/new");
    expect(screen.getByRole("button", { name: "메뉴 열기" })).toBeInTheDocument();
  });
});
