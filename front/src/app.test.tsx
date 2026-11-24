import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the app root", async () => {
    render(<App />);

    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(await screen.findByText(/API 연결 설정이 필요합니다/i)).toBeInTheDocument();
  });
});
