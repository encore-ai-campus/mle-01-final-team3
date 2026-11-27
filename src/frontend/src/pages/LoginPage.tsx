import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import type { AuthDepartment } from "../auth/context";
import { Button } from "../components/ui/Button";
import { TextField } from "../components/ui/TextField";

interface LoginLocationState {
  from?: string;
}

type LoginRole = AuthDepartment | "admin";

const roleOptions: Array<{ value: LoginRole; label: string }> = [
  { value: "marketing", label: "마케팅 담당자" },
  { value: "legal", label: "법무 담당자" },
  { value: "admin", label: "관리자" },
];

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const useFixtures = import.meta.env.VITE_USE_FIXTURES !== "false";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<LoginRole | "">("");
  const [error, setError] = useState<string | null>(null);
  const state = location.state as LoginLocationState | null;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!role) {
      setError("담당자 유형 또는 관리자 유형을 선택해 주세요.");
      return;
    }

    setError(null);
    try {
      await login({
        email,
        password,
        loginType: role === "admin" ? "ADMIN" : "STAFF",
        department: role === "admin" ? undefined : role,
      });
      navigate(state?.from ?? "/", { replace: true });
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "로그인에 실패했습니다.");
    }
  };

  return (
    <main className="login-page">
      <section className="login-card" aria-labelledby="login-title">
        <div className="login-card__brand" aria-hidden="true">F</div>
        <p className="eyebrow">FOOD GUARD</p>
        <h1 id="login-title">로그인</h1>
        <p className="login-card__description">식품 광고 사전 검토 시스템에 접속합니다.</p>
        <form className="login-form" onSubmit={submit}>
          <TextField label="이메일 주소" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required={!useFixtures} />
          <TextField label="비밀번호" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required={!useFixtures} />
          <fieldset className="login-role-fieldset" aria-describedby={error ? "login-error" : undefined}>
            <legend>로그인 사용자 유형</legend>
            <div className="login-role-options">
              {roleOptions.map((option) => (
                <label className="login-role-option" key={option.value}>
                  <input type="radio" name="role" value={option.value} checked={role === option.value} onChange={() => setRole(option.value)} />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
            {error ? <p id="login-error" className="field__error" role="alert">{error}</p> : null}
          </fieldset>
          <div className="login-form__actions">
            <Button type="submit">로그인</Button>
            <Button type="button" variant="secondary" onClick={() => navigate(-1)}>나가기</Button>
          </div>
        </form>
        {useFixtures ? <p className="login-card__notice">베타 버전에서는 이메일과 비밀번호를 입력하지 않아도 로그인할 수 있습니다.</p> : null}
      </section>
    </main>
  );
}
