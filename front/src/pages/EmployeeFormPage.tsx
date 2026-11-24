import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DataState, Employee, EmployeeInput } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { EmployeeEditor } from "../components/domain/EmployeeEditor";

const initialValue: EmployeeInput = { name: "", department: "marketing", email: "", phone: "" };

export function EmployeeFormPage({ provider }: { provider: DataProvider }) {
  const navigate = useNavigate();
  const [value, setValue] = useState<EmployeeInput>(initialValue);
  const [mutation, setMutation] = useState<DataState<Employee> | null>(null);
  const update = (field: keyof EmployeeInput, next: string) => setValue((current) => ({ ...current, [field]: next } as EmployeeInput));
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setMutation({ status: "loading" }); void provider.createEmployee(value).then((result) => { setMutation(result); if (result.status === "ready") navigate(`/employees/${result.data.id}`); }); };
  return <div className="page-stack"><PageHeader eyebrow="ADMIN" title="신규직원등록" description="검토 업무에 참여할 직원을 등록합니다." actions={<Link className="button button--secondary" to="/employees">직원 목록</Link>} /><Card><EmployeeEditor value={value} pending={mutation?.status === "loading"} onChange={update} onSubmit={submit} submitLabel="직원 등록" />{mutation?.status === "not-configured" ? <div className="inline-error" role="alert">{mutation.message}</div> : null}{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}</Card></div>;
}
