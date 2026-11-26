import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DataState, Employee, EmployeeDeleteResult, EmployeeInput } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { EmployeeEditor } from "../components/domain/EmployeeEditor";
import { withRouteContext } from "../utils/routeContext";

export function EmployeeDetailPage({ provider, canDelete = false }: { provider: DataProvider; canDelete?: boolean }) {
  const { employeeId = "" } = useParams();
  const navigate = useNavigate();
  const { search } = useLocation();
  const [state, setState] = useState<DataState<Employee>>({ status: "loading" });
  const [value, setValue] = useState<EmployeeInput>({ name: "", department: "marketing", email: "", phone: "", password: "", status: "active" });
  const [mutation, setMutation] = useState<DataState<Employee> | null>(null);
  const [deleteMutation, setDeleteMutation] = useState<DataState<EmployeeDeleteResult> | null>(null);
  const load = useCallback(() => { setState({ status: "loading" }); void provider.getEmployee(employeeId).then((result) => { setState(result); if (result.status === "ready") setValue({ name: result.data.name, department: result.data.department, email: result.data.email, phone: result.data.phone, password: "", status: result.data.status }); }); }, [employeeId, provider]);
  useEffect(() => { load(); }, [load]);
  const update = (field: keyof EmployeeInput, next: string) => setValue((current) => ({ ...current, [field]: next } as EmployeeInput));
  const save = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMutation({ status: "loading" });
    const input = { ...value };
    if (!input.password) delete input.password;
    void provider.updateEmployee(employeeId, input).then(setMutation);
  };
  const remove = () => { setDeleteMutation({ status: "loading" }); void provider.deleteEmployee(employeeId).then((result) => { setDeleteMutation(result); if (result.status === "ready") navigate(withRouteContext("/employees", search)); }); };
  const pending = mutation?.status === "loading" || deleteMutation?.status === "loading";
  return <div className="page-stack"><PageHeader eyebrow="ADMIN" title="직원 정보" description="직원 정보를 수정합니다." actions={<Link className="button button--secondary" to={withRouteContext("/employees", search)}>직원 목록</Link>} />{state.status !== "ready" ? <StateView state={state} onRetry={load} /> : <Card><EmployeeEditor value={value} pending={pending} onChange={update} onSubmit={save} submitLabel="수정" showStatus showDelete={canDelete} onDelete={remove} onCancel={() => navigate(withRouteContext("/employees", search))} />{mutation?.status === "not-configured" ? <div className="inline-error" role="alert">{mutation.message}</div> : null}{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}{mutation?.status === "ready" ? <div className="success-banner" role="status">직원 정보가 저장되었습니다.</div> : null}{deleteMutation?.status === "not-configured" ? <div className="inline-error" role="alert">{deleteMutation.message}</div> : null}{deleteMutation?.status === "error" ? <div className="inline-error" role="alert">{deleteMutation.error.message}</div> : null}</Card>}</div>;
}
