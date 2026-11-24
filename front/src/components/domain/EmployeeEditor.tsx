import type { FormEvent } from "react";
import type { EmployeeInput } from "../../types/domain";
import { Button } from "../ui/Button";
import { Select } from "../ui/Select";
import { TextField } from "../ui/TextField";

interface EmployeeEditorProps { value: EmployeeInput; pending: boolean; onChange: (field: keyof EmployeeInput, value: string) => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; submitLabel: string; }

export function EmployeeEditor({ value, pending, onChange, onSubmit, submitLabel }: EmployeeEditorProps) {
  return <form className="employee-form" onSubmit={onSubmit}><TextField label="이름" required value={value.name} onChange={(event) => onChange("name", event.target.value)} /><Select label="소속부서" value={value.department} onChange={(event) => onChange("department", event.target.value)} options={[{ value: "marketing", label: "마케팅팀" }, { value: "legal", label: "법무팀" }]} /><TextField label="메일주소" type="email" required value={value.email} onChange={(event) => onChange("email", event.target.value)} /><TextField label="연락처" type="tel" required value={value.phone} onChange={(event) => onChange("phone", event.target.value)} /><Button type="submit" disabled={pending}>{pending ? "저장 중…" : submitLabel}</Button></form>;
}
