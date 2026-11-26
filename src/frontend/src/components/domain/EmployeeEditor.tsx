import type { FormEvent } from "react";
import type { EmployeeInput, EmployeeStatus } from "../../types/domain";
import { Button } from "../ui/Button";
import { Select } from "../ui/Select";
import { TextField } from "../ui/TextField";

interface EmployeeEditorProps {
  value: EmployeeInput;
  pending: boolean;
  onChange: (field: keyof EmployeeInput, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  submitLabel: string;
  showStatus?: boolean;
  onCancel?: () => void;
  showDelete?: boolean;
  onDelete?: () => void;
}

export function EmployeeEditor({ value, pending, onChange, onSubmit, submitLabel, showStatus = false, onCancel, showDelete = false, onDelete }: EmployeeEditorProps) {
  const statusOptions: Array<{ value: EmployeeStatus; label: string }> = [
    { value: "active", label: "Active" },
    { value: "inactive", label: "Inactive" },
  ];

  return (
    <form className="employee-form" onSubmit={onSubmit}>
      <TextField label="이름" required value={value.name} onChange={(event) => onChange("name", event.target.value)} />
      <Select label="소속부서" value={value.department} onChange={(event) => onChange("department", event.target.value)} options={[{ value: "marketing", label: "마케팅팀" }, { value: "legal", label: "법무팀" }]} />
      <TextField label="메일주소" type="email" required value={value.email} onChange={(event) => onChange("email", event.target.value)} />
      <TextField label="연락처" type="tel" required value={value.phone} onChange={(event) => onChange("phone", event.target.value)} />
      <TextField label="비밀번호" type="password" autoComplete="new-password" required={!showStatus} value={value.password ?? ""} onChange={(event) => onChange("password", event.target.value)} />
      {showStatus ? <Select label="상태" value={value.status ?? "active"} onChange={(event) => onChange("status", event.target.value)} options={statusOptions} /> : null}
      <div className="employee-form__actions">
        <Button type="submit" disabled={pending}>{pending ? "저장 중…" : submitLabel}</Button>
        {onCancel ? <Button type="button" variant="secondary" onClick={onCancel} disabled={pending}>닫기</Button> : null}
        {showDelete && onDelete ? <Button type="button" variant="danger" onClick={onDelete} disabled={pending}>직원 삭제</Button> : null}
      </div>
    </form>
  );
}
