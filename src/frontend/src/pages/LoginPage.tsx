import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import type { AuthDepartment } from "../auth/context";
import { Button } from "../components/ui/Button";
import { TextField } from "../components/ui/TextField";

interface LoginLocationState {
  from?: string;
}

const departmentOptions: Array<{ value: AuthDepartment; label: string }> = [
  { value: "marketing", label: "마케팅 담당자" },
  { value: "legal", label: "법무 담당자" },
];

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [department, setDepartment] = useState<AuthDepartment | "">("");
  const [departmentError, setDepartmentError] = useState<string | null>(null);
  const state = location.state as LoginLocationState | null;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!department) {
      setDepartmentError("로그인할 담당자 유형을 선택해 주세요.");
      return;
    }
    setDepartmentError(null);
    login(department);
    navigate(state?.from ?? "/", { replace: true });
  };

  const exit = () => {
    navigate(-1);
  };

  return (
    <main className="login-page">
      <section className="login-card" aria-labelledby="login-title">
        <div className="login-card__brand" aria-hidden="true">F</div>
        <p className="eyebrow">FOOD GUARD</p>
        <h1 id="login-title">로그인</h1>
        <p className="login-card__description">식품 광고 심의 후속조치 시스템에 접속합니다.</p>
        <form className="login-form" onSubmit={submit}>
          <TextField label="이메일주소" type="email" autoComplete="username" />
          <TextField label="비밀번호" type="password" autoComplete="current-password" />
          <fieldset className="login-role-fieldset" aria-describedby={departmentError ? "department-error" : undefined}>
            <legend>로그인 사용자 유형</legend>
            <div className="login-role-options">
              {departmentOptions.map((option) => (
                <label className="login-role-option" key={option.value}>
                  <input
                    type="radio"
                    name="department"
                    value={option.value}
                    checked={department === option.value}
                    onChange={() => setDepartment(option.value)}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
            {departmentError ? <p id="department-error" className="field__error" role="alert">{departmentError}</p> : null}
          </fieldset>
          <div className="login-form__actions">
            <Button type="submit">로그인</Button>
            <Button type="button" variant="secondary" onClick={exit}>나가기</Button>
          </div>
        </form>
        <p className="login-card__notice">베타 버전에서는 이메일과 비밀번호를 입력하지 않아도 로그인할 수 있습니다.</p>
      </section>
    </main>
  );
}
