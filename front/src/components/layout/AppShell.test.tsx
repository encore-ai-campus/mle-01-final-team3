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
    expect(screen.getByRole("main")).toHaveTextContent("본문");
  });

  it("shows workflow and employee management only for an admin", () => {
    render(
      <AppShell
        currentPath="/workflow"
        user={{ name: "관리자", department: "관리자", role: "admin" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.getByRole("link", { name: "업무 흐름 시각화" })).toHaveAttribute("href", "/workflow");
    expect(screen.getByRole("link", { name: "직원 관리" })).toHaveAttribute("href", "/employees");
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
});
