import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { EmployeesPage } from "./EmployeesPage";
import { FixtureProvider } from "../api/fixtureProvider";

describe("EmployeesPage", () => {
  it("filters employees and links names to details", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><EmployeesPage provider={new FixtureProvider()} /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "직원 관리" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "연락처" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "김마케팅" })).toHaveAttribute("href", "/employees/fixture-marketing");
    await user.type(screen.getByRole("textbox", { name: "직원 검색" }), "김법무");
    expect(screen.getByRole("link", { name: "김법무" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "김마케팅" })).not.toBeInTheDocument();
  });
});
