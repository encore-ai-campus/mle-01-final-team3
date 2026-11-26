import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReviewDetailPage } from "./ReviewDetailPage";
import { FixtureProvider } from "../api/fixtureProvider";
import { MemoryRouter } from "react-router-dom";

describe("ReviewDetailPage evidence and feedback", () => {
  it("shows AI evidence and reviewer feedback controls", async () => {
    window.history.pushState({}, "", "/reviews/fixture-review-1");
    render(<MemoryRouter initialEntries={["/reviews/fixture-review-1"]}><ReviewDetailPage provider={new FixtureProvider()} /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "검토 근거" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "맞음" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "다름" })).toBeInTheDocument();
  });
});
