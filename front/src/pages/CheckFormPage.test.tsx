import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureCheckProvider } from "../api/checkProvider";
import { CheckFormPage } from "./CheckFormPage";

describe("CheckFormPage", () => {
  it("requires an ad title and copy before starting a check", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><CheckFormPage provider={new FixtureCheckProvider()} /></MemoryRouter>);

    await user.click(screen.getByRole("button", { name: "자동 검사 시작" }));

    expect(screen.getByRole("alert")).toHaveTextContent("광고명을 입력해 주세요.");
    expect(screen.getByRole("alert")).toHaveTextContent("광고 문구를 입력해 주세요.");
  });

  it("moves to the result report after a fixture check starts", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/checks/new"]}>
        <Routes>
          <Route path="/checks/new" element={<CheckFormPage provider={new FixtureCheckProvider()} />} />
          <Route path="/checks/:checkId" element={<h1>검사 결과</h1>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("광고명"), "예시 광고");
    await user.type(screen.getByRole("textbox", { name: /광고 문구/ }), "예시 광고 문구");
    await user.click(screen.getByRole("button", { name: "자동 검사 시작" }));

    expect(await screen.findByRole("heading", { name: "검사 결과" })).toBeInTheDocument();
  });
});
