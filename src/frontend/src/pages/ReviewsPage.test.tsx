import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ApiProvider } from "../api/apiProvider";
import { FixtureProvider } from "../api/fixtureProvider";
import { ReviewsPage } from "./ReviewsPage";

describe("ReviewsPage", () => {
  it("renders review rows and synchronizes filters", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><ReviewsPage provider={new FixtureProvider("LG-8")} /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "검토함" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "광고명" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "작성자" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "분류" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "상태" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "전송일" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "상세 보기" }).length).toBeGreaterThan(0);
    expect(screen.getAllByText("[마케팅]검토 완료(부적합)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("부적합").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "수정" })[0]).toHaveAttribute("href", expect.stringContaining("edit=true"));
    await user.selectOptions(screen.getByLabelText("처리 상태"), "legal-in-progress");
    expect(screen.getByLabelText("처리 상태")).toHaveValue("legal-in-progress");
  });

  it("renders the provider empty state", async () => {
    render(<MemoryRouter><ReviewsPage provider={new FixtureProvider("LG-9")} /></MemoryRouter>);
    expect(await screen.findByText("조건에 맞는 검토 보고서가 없습니다.")).toBeInTheDocument();
  });

  it("offers an explicit demo report entry when the API is not configured", async () => {
    render(<MemoryRouter><ReviewsPage provider={new ApiProvider()} /></MemoryRouter>);
    expect(await screen.findByText(/검증된 API 연결이 설정되지 않았습니다/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "데모 보고서 확인" })).toHaveAttribute("href", "/reviews?demo=true");
  });

  it("shows the new marketing and legal status labels in the list filter", async () => {
    render(<MemoryRouter><ReviewsPage provider={new FixtureProvider("LG-1")} /></MemoryRouter>);

    expect(await screen.findByRole("option", { name: "[마케팅]검토 완료(부적합)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[마케팅]검토 완료(적합)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[법무]검토 대기" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[법무]검토 중" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[법무]검토 완료(적합)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[법무]검토 완료(부적합)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[법무]검토 완료(보완 필요)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[법무]검토 완료(진행 가능)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "[마케팅]심의 취소" })).toBeInTheDocument();
  });
});
