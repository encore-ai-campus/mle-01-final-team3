import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the app root", async () => {
    vi.stubEnv("VITE_USE_FIXTURES", "false");
    sessionStorage.setItem("food-ad-review:authenticated", "true");
    render(<App />);

    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "로그인" })).toBeInTheDocument();
  });
});
