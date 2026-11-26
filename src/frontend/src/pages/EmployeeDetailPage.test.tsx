import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import type { DataState, Employee } from "../types/domain";
import { EmployeeDetailPage } from "./EmployeeDetailPage";

describe("EmployeeDetailPage", () => {
  it("edits the current status and only exposes edit and close actions", async () => {
    const user = userEvent.setup();
    const provider = new FixtureProvider();

    render(
      <MemoryRouter initialEntries={["/employees/fixture-marketing"]}>
        <Routes>
          <Route path="/employees/:employeeId" element={<EmployeeDetailPage provider={provider} />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "직원 정보" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "상태" })).toHaveValue("active");
    expect(screen.getByRole("option", { name: "Active" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Inactive" })).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toHaveAttribute("type", "password");
    expect(screen.getByLabelText("비밀번호")).not.toBeRequired();
    expect(screen.getByRole("button", { name: "수정" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "닫기" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "직원 삭제" })).not.toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "상태" }), "inactive");
    await user.type(screen.getByLabelText("비밀번호"), "new-password");
    await user.click(screen.getByRole("button", { name: "수정" }));

    expect(await screen.findByRole("status")).toHaveTextContent("직원 정보가 저장되었습니다.");
    const result = (await provider.getEmployee("fixture-marketing")) as DataState<Employee>;
    expect(result.status).toBe("ready");
    if (result.status === "ready") expect(result.data.status).toBe("inactive");
  });

  it("shows the delete action for an administrator and returns to the employee list", async () => {
    const user = userEvent.setup();
    const provider = new FixtureProvider();

    render(
      <MemoryRouter initialEntries={["/employees/fixture-marketing?role=admin"]}>
        <Routes>
          <Route path="/employees/:employeeId" element={<EmployeeDetailPage provider={provider} canDelete />} />
          <Route path="/employees" element={<h1>직원 목록</h1>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("button", { name: "직원 삭제" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "직원 삭제" }));

    expect(await screen.findByRole("heading", { name: "직원 목록" })).toBeInTheDocument();
    expect((await provider.getEmployee("fixture-marketing")).status).toBe("empty");
  });

  it("does not submit a blank password during an employee edit", async () => {
    const user = userEvent.setup();
    const provider = new FixtureProvider();
    const updateEmployee = vi.spyOn(provider, "updateEmployee");

    render(
      <MemoryRouter initialEntries={["/employees/fixture-marketing"]}>
        <Routes>
          <Route path="/employees/:employeeId" element={<EmployeeDetailPage provider={provider} />} />
        </Routes>
      </MemoryRouter>,
    );

    await screen.findByLabelText("비밀번호");
    await user.click(screen.getByRole("button", { name: /수정/ }));

    expect(updateEmployee).toHaveBeenCalledTimes(1);
    expect("password" in updateEmployee.mock.calls[0][1]).toBe(false);
  });
});
