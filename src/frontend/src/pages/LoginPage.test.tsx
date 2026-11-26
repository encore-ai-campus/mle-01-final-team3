import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { AUTH_DEPARTMENT_STORAGE_KEY } from "../auth/context";
import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  afterEach(() => {
    sessionStorage.clear();
  });

  it("requires a department before entering the dashboard", async () => {
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<h1>대시보드</h1>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await user.click(screen.getByRole("button", { name: "로그인" }));

    expect(screen.getByRole("alert")).toHaveTextContent("담당자 유형");
    expect(screen.queryByRole("heading", { name: "대시보드" })).not.toBeInTheDocument();
  });

  it("logs in without requiring email or password and stores the marketing department", async () => {
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<h1>대시보드</h1>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await user.click(screen.getByRole("radio", { name: "마케팅 담당자" }));
    await user.click(screen.getByRole("button", { name: "로그인" }));

    expect(await screen.findByRole("heading", { name: "대시보드" })).toBeInTheDocument();
    expect(sessionStorage.getItem(AUTH_DEPARTMENT_STORAGE_KEY)).toBe("marketing");
  });

  it("stores the legal department when a legal reviewer logs in", async () => {
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<h1>대시보드</h1>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await user.click(screen.getByRole("radio", { name: "법무 담당자" }));
    await user.click(screen.getByRole("button", { name: "로그인" }));

    expect(sessionStorage.getItem(AUTH_DEPARTMENT_STORAGE_KEY)).toBe("legal");
  });

  it("returns to the previous page when the user clicks exit", async () => {
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/previous", "/login"]} initialIndex={1}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/previous" element={<h1>이전 페이지</h1>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    await user.click(screen.getByRole("button", { name: "나가기" }));

    expect(await screen.findByRole("heading", { name: "이전 페이지" })).toBeInTheDocument();
  });
});
