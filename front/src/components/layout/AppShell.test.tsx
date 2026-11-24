import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("renders navigation labels and current route state", () => {
    render(
      <AppShell
        currentPath="/reviews"
        user={{ name: "담당자", department: "legal" }}
        onNavigate={vi.fn()}
      >
        <p>본문</p>
      </AppShell>,
    );

    expect(screen.getByRole("navigation", { name: "주요 메뉴" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "검토함" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "광고 문구 검사" })).toHaveAttribute("href", "/checks/new");
    expect(screen.getByRole("link", { name: "진행 상황" })).toHaveAttribute("href", "/progress");
    expect(screen.getByRole("main")).toHaveTextContent("본문");
  });

  it("opens and closes the mobile navigation with an accessible button", async () => {
    const user = userEvent.setup();
    render(
      <AppShell
        currentPath="/"
        user={{ name: "담당자", department: "legal" }}
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
