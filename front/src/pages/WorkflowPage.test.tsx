import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { WorkflowPage } from "./WorkflowPage";

describe("WorkflowPage", () => {
  it("renders the workflow stages and current statuses", () => {
    render(<MemoryRouter><WorkflowPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "업무 흐름 시각화" })).toBeInTheDocument();
    expect(screen.getByText("1차 검토")).toBeInTheDocument();
    expect(screen.getByText("법무팀 검토")).toBeInTheDocument();
  });
});
