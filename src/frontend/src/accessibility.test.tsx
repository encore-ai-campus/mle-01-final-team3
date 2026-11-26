import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "./components/layout/AppShell";
import { Dialog } from "./components/ui/Dialog";

describe("accessibility smoke checks", () => {
  it("has one main landmark and labelled navigation", () => {
    render(<AppShell currentPath="/" user={{ name: "사용자", department: "부서" }} onNavigate={vi.fn()}><p>내용</p></AppShell>);
    expect(screen.getAllByRole("main")).toHaveLength(1);
    expect(screen.getByRole("navigation", { name: "주요 메뉴" })).toBeInTheDocument();
  });

  it("labels the dialog and its close control", () => {
    render(<Dialog open title="확인" description="설명" onClose={vi.fn()}><button type="button">확인</button></Dialog>);
    expect(screen.getByRole("dialog", { name: "확인" })).toHaveAttribute("aria-describedby");
    expect(screen.getByRole("button", { name: "닫기" })).toBeInTheDocument();
  });
});
