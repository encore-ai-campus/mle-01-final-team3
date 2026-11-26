import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { ReviewDetailPage } from "./ReviewDetailPage";

describe("ReviewDetailPage", () => {
  it("renders report detail and read-only state", async () => {
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-1"]}><Routes><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={new FixtureProvider("LG-17")} />} /></Routes></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "검토 보고서" })).toBeInTheDocument();
    expect(screen.getByText("다른 담당자가 처리했거나 처리 권한이 없습니다.")).toBeInTheDocument();
  });
});
