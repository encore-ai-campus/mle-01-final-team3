import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App routes", () => {
  it("renders the unknown route state", () => {
    window.history.pushState({}, "", "/unknown");
    render(<App />);
    expect(screen.getByRole("heading", { name: "페이지를 찾을 수 없습니다" })).toBeInTheDocument();
  });
});
