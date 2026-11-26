import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App routes", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_USE_FIXTURES", "true");
    sessionStorage.setItem("food-ad-review:authenticated", "true");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    sessionStorage.clear();
  });

  it("redirects unauthenticated visitors to the login page", async () => {
    sessionStorage.clear();
    window.history.pushState({}, "", "/reviews");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "로그인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "나가기" })).toBeInTheDocument();
  });

  it("renders the ad check route", () => {
    window.history.pushState({}, "", "/checks/new");
    render(<App />);
    expect(screen.getByRole("heading", { name: "광고 문구 검사" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "자동 검사 시작" })).toBeInTheDocument();
  });

  it("renders the unknown route state", () => {
    window.history.pushState({}, "", "/unknown");
    render(<App />);
    expect(screen.getByRole("heading", { name: "페이지를 찾을 수 없습니다" })).toBeInTheDocument();
  });

  it("exposes admin pages without a role query in the default access mode", async () => {
    window.history.pushState({}, "", "/employees?demo=true");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "직원 관리" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "직원 등록" })).toBeInTheDocument();
  });

  it("keeps admin pages available with the explicit admin context", async () => {
    window.history.pushState({}, "", "/employees?demo=true&role=admin");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "직원 관리" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "신규직원등록" })).toHaveAttribute("href", "/employees/new?demo=true&role=admin");
  });

  it("keeps employee routes reachable in API mode without a role query", async () => {
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    window.history.pushState({}, "", "/employees");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "직원 관리" })).toBeInTheDocument();
  });

  it("shows legal outcome actions regardless of the team query in the default access mode", async () => {
    window.history.pushState({}, "", "/reviews/fixture-review-3?team=marketing");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "[법무]광고 문구 검토 보고서" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "진행 가능" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "보완 필요" })).toBeInTheDocument();
  });

  it("restores the admin and legal restrictions when role gating is enabled", async () => {
    vi.stubEnv("VITE_ROLE_GATING", "true");
    window.history.pushState({}, "", "/employees");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "관리자 권한이 필요합니다" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "직원 관리" })).not.toBeInTheDocument();

    window.history.pushState({}, "", "/reviews/fixture-review-3?team=marketing");
    render(<App />);
    expect(await screen.findByRole("heading", { name: "[법무]광고 문구 검토 보고서" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "진행 가능" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "보완 필요" })).not.toBeInTheDocument();
  });

  it("keeps the existing admin query context in gated API mode", async () => {
    vi.stubEnv("VITE_ROLE_GATING", "true");
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    window.history.pushState({}, "", "/employees?role=admin");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "직원 관리" })).toBeInTheDocument();
  });

  it("keeps the existing legal default when gated review URLs omit a team", async () => {
    vi.stubEnv("VITE_ROLE_GATING", "true");
    window.history.pushState({}, "", "/reviews/fixture-review-3");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "[법무]광고 문구 검토 보고서" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "진행 가능" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "보완 필요" })).toBeInTheDocument();
  });

  it("uses virtual data without rendering a demo-mode menu", async () => {
    window.history.pushState({}, "", "/reviews/fixture-review-3?demo=true");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "[법무]광고 문구 검토 보고서" })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "시연 모드" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "진행 가능" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "보완 필요" })).toBeInTheDocument();
  });

  it("enables fixture reports only through the explicit demo query", async () => {
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    window.history.pushState({}, "", "/reviews?demo=true");
    render(<App />);

    expect(await screen.findByRole("heading", { name: "검토함" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "상세 보기" }).length).toBeGreaterThan(0);
  });

  it("keeps demo mode while opening a report detail", async () => {
    const user = userEvent.setup();
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    window.history.pushState({}, "", "/reviews?demo=true");
    render(<App />);

    await user.click((await screen.findAllByRole("link", { name: "상세 보기" }))[0]);
    expect(await screen.findByRole("heading", { name: "[마케팅]광고 문구 검토 보고서" })).toBeInTheDocument();
  });
});
