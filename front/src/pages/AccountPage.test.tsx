import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureProvider } from "../api/fixtureProvider";
import { AccountPage } from "./AccountPage";

describe("AccountPage", () => {
  it("loads the account and keeps failed password input visible", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><AccountPage provider={new FixtureProvider("LG-38")} /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "마이페이지" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("새 비밀번호"), "password");
    await user.type(screen.getByLabelText("새 비밀번호 확인"), "different");
    await user.click(screen.getByRole("button", { name: "저장" }));
    expect(await screen.findByText("비밀번호를 변경하지 못했습니다.")).toBeInTheDocument();
    expect(screen.getByLabelText("새 비밀번호")).toHaveValue("password");
  });
});
