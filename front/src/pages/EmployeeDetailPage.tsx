import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DataState, Employee, EmployeeDeleteResult, EmployeeInput } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Dialog } from "../components/ui/Dialog";
import { StateView } from "../components/ui/StateView";
import { EmployeeEditor } from "../components/domain/EmployeeEditor";

export function EmployeeDetailPage({ provider }: { provider: DataProvider }) {
  const { employeeId = "" } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<DataState<Employee>>({ status: "loading" });
  const [value, setValue] = useState<EmployeeInput>({ name: "", department: "marketing", email: "", phone: "" });
  const [mutation, setMutation] = useState<DataState<Employee | EmployeeDeleteResult> | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getEmployee(employeeId).then((result) => { setState(result); if (result.status === "ready") setValue({ name: result.data.name, department: result.data.department, email: result.data.email, phone: result.data.phone }); }); }, [employeeId, provider]);
  useEffect(() => { load(); }, [load]);
  const update = (field: keyof EmployeeInput, next: string) => setValue((current) => ({ ...current, [field]: next } as EmployeeInput));
  const save = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setMutation({ status: "loading" }); void provider.updateEmployee(employeeId, value).then(setMutation); };
  const remove = () => { setMutation({ status: "loading" }); void provider.deleteEmployee(employeeId).then((result) => { setMutation(result); if (result.status === "ready") navigate("/employees"); }); };
  return <div className="page-stack"><PageHeader eyebrow="ADMIN" title="직원 정보" description="직원 정보를 수정하거나 삭제합니다." actions={<Link className="button button--secondary" to="/employees">직원 목록</Link>} />{state.status !== "ready" ? <StateView state={state} onRetry={load} /> : <><Card><EmployeeEditor value={value} pending={mutation?.status === "loading"} onChange={update} onSubmit={save} submitLabel="수정 저장" /><div className="employee-danger-zone"><Button variant="danger" onClick={() => setDeleteOpen(true)} disabled={mutation?.status === "loading"}>직원 삭제</Button></div>{mutation?.status === "not-configured" ? <div className="inline-error" role="alert">{mutation.message}</div> : null}{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}{mutation?.status === "ready" && "employeeId" in mutation.data ? <div className="success-banner" role="status">직원이 삭제되었습니다.</div> : null}{mutation?.status === "ready" && "name" in mutation.data ? <div className="success-banner" role="status">직원 정보가 저장되었습니다.</div> : null}</Card><Dialog open={deleteOpen} title="직원 삭제" description="삭제한 직원 정보는 복구할 수 없습니다." onClose={() => setDeleteOpen(false)}><div className="dialog-actions"><Button variant="secondary" onClick={() => setDeleteOpen(false)}>취소</Button><Button variant="danger" onClick={() => { setDeleteOpen(false); remove(); }}>삭제</Button></div></Dialog></>}</div>;
}
