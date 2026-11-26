import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { EmployeeFormPage } from "./EmployeeFormPage";

describe("EmployeeFormPage", () => {
  it("renders the employee registration fields and list navigation", () => {
    render(
      <MemoryRouter initialEntries={["/employees/new"]}>
        <EmployeeFormPage provider={new FixtureProvider()} />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "신규직원등록" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "이름" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "소속부서" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "메일주소" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "연락처" })).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toHaveAttribute("type", "password");
    expect(screen.getByLabelText("비밀번호")).toBeRequired();
    expect(screen.queryByRole("combobox", { name: "상태" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "직원 목록" })).toHaveAttribute("href", "/employees");
  });
});
