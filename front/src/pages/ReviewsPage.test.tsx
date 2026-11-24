import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
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
    await user.selectOptions(screen.getByLabelText("처리 상태"), "in-progress");
    expect(screen.getByLabelText("처리 상태")).toHaveValue("in-progress");
  });

  it("renders the provider empty state", async () => {
    render(<MemoryRouter><ReviewsPage provider={new FixtureProvider("LG-9")} /></MemoryRouter>);
    expect(await screen.findByText("조건에 맞는 검토 보고서가 없습니다.")).toBeInTheDocument();
  });
});
