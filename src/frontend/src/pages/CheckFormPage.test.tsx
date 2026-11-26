import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureCheckProvider } from "../api/checkProvider";
import { CheckFormPage } from "./CheckFormPage";
import { CheckResultPage } from "./CheckResultPage";

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

  it("shows the approved marketing report and legal request action for compliant copy", async () => {
    const user = userEvent.setup();
    const provider = new FixtureCheckProvider();
    render(<MemoryRouter initialEntries={["/checks/new"]}><Routes><Route path="/checks/new" element={<CheckFormPage provider={provider} />} /><Route path="/checks/:checkId" element={<CheckResultPage provider={provider} />} /></Routes></MemoryRouter>);

    await user.type(screen.getByLabelText("광고명"), "안전 광고");
    await user.type(screen.getByRole("textbox", { name: /광고 문구/ }), "건강한 생활에 도움을 줄 수 있어요");
    await user.click(screen.getByRole("button", { name: "자동 검사 시작" }));

    expect(await screen.findByRole("heading", { name: "[마케팅]광고 문구 검토 보고서", level: 2 })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "법무팀 검토 요청" })).toBeInTheDocument();
  });

  it("accepts an allowed attachment and displays the selected file", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><CheckFormPage provider={new FixtureCheckProvider()} /></MemoryRouter>);
    const file = new File(["광고 문서"], "광고문서.pdf", { type: "application/pdf" });

    await user.upload(screen.getByLabelText("첨부 파일"), file);

    expect(screen.getByText("광고문서.pdf")).toBeInTheDocument();
  });
});
