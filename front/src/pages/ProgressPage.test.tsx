import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureCheckProvider } from "../api/checkProvider";
import { ProgressPage } from "./ProgressPage";

describe("ProgressPage", () => {
  it("renders the current step, history, and report navigation", async () => {
    render(<MemoryRouter initialEntries={["/progress/fixture-check-1"]}><Routes><Route path="/progress/:checkId" element={<ProgressPage provider={new FixtureCheckProvider()} />} /></Routes></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "진행 상황" })).toBeInTheDocument();
    expect(screen.getAllByText("RA 검토").length).toBeGreaterThan(0);
    expect(screen.getByText("자동 검사 완료")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "검토함 보기" })).toHaveAttribute("href", "/reviews");
  });
});
