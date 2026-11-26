import { useCallback, useEffect, useState } from "react";
import type { DataProvider } from "../types/api";
import type { Account, DataState, PasswordUpdateInput, PasswordUpdateResult } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { TextField } from "../components/ui/TextField";

const initialForm: PasswordUpdateInput = { currentPassword: "", newPassword: "", confirmation: "" };
export function AccountPage({ provider }: { provider: DataProvider }) {
  const [state, setState] = useState<DataState<Account>>({ status: "loading" });
  const [form, setForm] = useState(initialForm);
  const [mutation, setMutation] = useState<DataState<PasswordUpdateResult> | null>(null);
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getAccount().then(setState); }, [provider]);
  useEffect(() => { load(); }, [load]);
  const update = (key: keyof PasswordUpdateInput, value: string) => setForm((current) => ({ ...current, [key]: value }));
  const save = (event: React.FormEvent<HTMLFormElement>) => { event.preventDefault(); setMutation({ status: "loading" }); void provider.updatePassword(form).then((result) => { setMutation(result); if (result.status === "ready") setForm(initialForm); }); };
  return <div className="page-stack"><PageHeader eyebrow="ACCOUNT" title="개인 정보" description="개인 정보와 비밀번호를 관리합니다." />{state.status !== "ready" ? <StateView state={state} onRetry={load} /> : <><Card><h2>{state.data.name}</h2><dl className="account-meta"><div><dt>이메일</dt><dd>{state.data.email}</dd></div><div><dt>부서</dt><dd>{state.data.department}</dd></div><div><dt>권한</dt><dd>{state.data.role}</dd></div></dl>{state.data.needsPasswordChange ? <div className="notice-banner">비밀번호를 바꿔 주세요.</div> : null}</Card><Card><form className="account-form" onSubmit={save}><h2>비밀번호 변경</h2><TextField label="현재 비밀번호" type="password" value={form.currentPassword} onChange={(event) => update("currentPassword", event.target.value)} /><TextField label="새 비밀번호" type="password" value={form.newPassword} onChange={(event) => update("newPassword", event.target.value)} /><TextField label="새 비밀번호 확인" type="password" value={form.confirmation} onChange={(event) => update("confirmation", event.target.value)} /><Button type="submit" disabled={mutation?.status === "loading"}>저장</Button>{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}{mutation?.status === "ready" ? <div className="success-banner" role="status">{mutation.data.message}</div> : null}</form></Card></>}</div>;
}
