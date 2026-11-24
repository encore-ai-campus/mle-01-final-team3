import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { DataProvider } from "../types/api";
import type { DataState, Employee } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateView } from "../components/ui/StateView";
import { TextField } from "../components/ui/TextField";
import { DataTable } from "../components/ui/DataTable";

const departmentLabels = { marketing: "마케팅팀", legal: "법무팀" } as const;
const statusLabels = { active: "Active", inactive: "Inactive" } as const;

export function EmployeesPage({ provider }: { provider: DataProvider }) {
  const [search, setSearch] = useState("");
  const [state, setState] = useState<DataState<Employee[]>>({ status: "loading" });
  const load = useCallback(() => { setState({ status: "loading" }); void provider.listEmployees(search).then(setState); }, [provider, search]);
  useEffect(() => { load(); }, [load]);
  return <div className="page-stack"><PageHeader eyebrow="ADMIN" title="직원 관리" description="검토 업무에 참여하는 직원 정보를 관리합니다." actions={<><Link className="button" to="/employees/new">신규직원등록</Link><Button variant="secondary" onClick={load}>새로고침</Button></>} /><Card><TextField label="직원 검색" value={search} placeholder="이름, 메일주소, 연락처 검색" onChange={(event) => setSearch(event.target.value)} /></Card>{state.status === "ready" ? <Card><DataTable rows={state.data} getRowKey={(row) => row.id} emptyState="등록된 직원이 없습니다." columns={[{ key: "name", header: "이름", render: (row) => <Link to={`/employees/${row.id}`}>{row.name}</Link> }, { key: "department", header: "소속부서", render: (row) => departmentLabels[row.department] }, { key: "email", header: "메일주소", render: (row) => row.email }, { key: "phone", header: "연락처", render: (row) => row.phone }, { key: "status", header: "상태", render: (row) => statusLabels[row.status] }]} /></Card> : state.status === "empty" ? <div className="table-empty">{state.message}</div> : <StateView state={state} onRetry={load} />}</div>;
}
