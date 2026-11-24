import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { FixtureCheckProvider } from "../api/checkProvider";
import type { CheckDataProvider } from "../types/api";
import type { CheckResult, DataState } from "../types/domain";
import { CheckResultPage } from "./CheckResultPage";

describe("CheckResultPage", () => {
  it("renders findings, evidence, alternatives, and report links", async () => {
    render(
      <MemoryRouter initialEntries={["/checks/fixture-check-1"]}>
        <Routes>
          <Route path="/checks/:checkId" element={<CheckResultPage provider={new FixtureCheckProvider()} />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: "검사 결과" })).toBeInTheDocument();
    expect(screen.getByText("위반 의심")).toBeInTheDocument();
    expect(screen.getByText("적용 조항")).toBeInTheDocument();
    expect(screen.getByText("건강한 생활에 도움을 줄 수 있어요")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "검토 보고서 보기" })).toHaveAttribute("href", "/reviews/fixture-review-1");
    expect(screen.getByRole("link", { name: "진행 상황 보기" })).toHaveAttribute("href", "/progress/fixture-check-1");
  });

  it("explains when a finding has no evidence or alternatives", async () => {
    const result: CheckResult = {
      id: "check-empty-evidence",
      title: "검사 결과",
      productType: "general-food",
      ingredient: "원료",
      channel: "SNS",
      copy: "문구",
      findings: [{ id: "finding-1", severity: "safe", phrase: "문구", reason: "안전", allowedCopy: null, evidence: [], alternatives: [] }],
      reviewId: null,
      nextStep: "확인",
    };
    const provider: CheckDataProvider = {
      getResult: async (): Promise<DataState<CheckResult>> => ({ status: "ready", data: result }),
      saveDraft: async () => ({ status: "not-configured", message: "미설정" }),
      startCheck: async () => ({ status: "not-configured", message: "미설정" }),
      getProgress: async () => ({ status: "not-configured", message: "미설정" }),
    };

    render(<MemoryRouter initialEntries={["/checks/check-empty-evidence"]}><Routes><Route path="/checks/:checkId" element={<CheckResultPage provider={provider} />} /></Routes></MemoryRouter>);

    expect(await screen.findByText("근거 자료가 없습니다.")).toBeInTheDocument();
    expect(screen.getByText("적용할 대안 문구가 없습니다.")).toBeInTheDocument();
  });
});
