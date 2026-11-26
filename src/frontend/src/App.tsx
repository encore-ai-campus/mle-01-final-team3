import { useMemo } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { createDataProvider } from "./api/providerFactory";
import { createCheckProvider } from "./api/checkProvider";
import { createFixtureWorkflowStore } from "./api/fixtureWorkflowStore";
import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/useAuth";
import { isArtifactScenarioId } from "./fixtures/artifactScenarios";
import { AppShell } from "./components/layout/AppShell";
import { AccountPage } from "./pages/AccountPage";
import { DashboardPage } from "./pages/DashboardPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { ReviewDetailPage } from "./pages/ReviewDetailPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { CheckFormPage } from "./pages/CheckFormPage";
import { CheckResultPage } from "./pages/CheckResultPage";
import { ProgressPage } from "./pages/ProgressPage";
import { WorkflowPage } from "./pages/WorkflowPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { EmployeeFormPage } from "./pages/EmployeeFormPage";
import { EmployeeDetailPage } from "./pages/EmployeeDetailPage";
import { ReviewReportPage } from "./pages/ReviewReportPage";
import { LoginPage } from "./pages/LoginPage";
import type { ReviewWorkflowRole } from "./types/domain";

function AppRoutes() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, department: workDepartment } = useAuth();
  const [searchParams] = useSearchParams();
  const scenarioValue = searchParams.get("scenario");
  const scenario = isArtifactScenarioId(scenarioValue) ? scenarioValue : "LG-1";
  const useFixtures = import.meta.env.VITE_USE_FIXTURES !== "false" || searchParams.get("demo") === "true";
  const roleGatingEnabled = import.meta.env.VITE_ROLE_GATING === "true";
  const isAdmin = !roleGatingEnabled || searchParams.get("role") === "admin";
  const workflowRole: ReviewWorkflowRole = roleGatingEnabled && searchParams.get("team") === "marketing" ? "marketing" : "legal";
  const workflowStore = useMemo(() => createFixtureWorkflowStore(), [scenario]);
  const provider = useMemo(() => createDataProvider(scenario, useFixtures, workflowStore), [scenario, useFixtures, workflowStore]);
  const checkProvider = useMemo(() => createCheckProvider(scenario, useFixtures, workflowStore), [scenario, useFixtures, workflowStore]);

  if (!isAuthenticated) {
    const from = `${location.pathname}${location.search}${location.hash}`;
    return <Routes><Route path="/login" element={<LoginPage />} /><Route path="*" element={<Navigate to="/login" replace state={{ from }} />} /></Routes>;
  }

  if (location.pathname === "/login") return <Navigate to="/" replace />;

  const department = isAdmin ? "관리자" : workflowRole === "legal" ? "법무팀" : workflowRole === "marketing" ? "마케팅팀" : "소속 확인 필요";
  return <AppShell currentPath={location.pathname} currentSearch={location.search} user={{ name: isAdmin ? "관리자" : "로그인 사용자", department, role: isAdmin ? "admin" : "reviewer" }} onNavigate={(path) => navigate(path)} provider={provider} workDepartment={workDepartment}><Routes><Route path="/" element={<DashboardPage provider={provider} />} /><Route path="/checks/new" element={<CheckFormPage provider={checkProvider} />} /><Route path="/checks/:checkId" element={<CheckResultPage provider={checkProvider} />} /><Route path="/progress" element={<ProgressPage provider={checkProvider} />} /><Route path="/progress/:checkId" element={<ProgressPage provider={checkProvider} />} /><Route path="/reviews" element={<ReviewsPage provider={provider} />} /><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={provider} workflowRole={workflowRole} />} /><Route path="/reviews/:reviewId/reports/:reportStage" element={<ReviewReportPage provider={provider} />} /><Route path="/workflow" element={isAdmin ? <WorkflowPage /> : <AccessDeniedPage />} /><Route path="/employees" element={isAdmin ? <EmployeesPage provider={provider} /> : <AccessDeniedPage />} /><Route path="/employees/new" element={isAdmin ? <EmployeeFormPage provider={provider} /> : <AccessDeniedPage />} /><Route path="/employees/:employeeId" element={isAdmin ? <EmployeeDetailPage provider={provider} canDelete /> : <AccessDeniedPage />} /><Route path="/account" element={<AccountPage provider={provider} />} /><Route path="/notifications" element={<NotificationsPage provider={provider} />} /><Route path="*" element={<NotFoundPage />} /></Routes></AppShell>;
}

function AccessDeniedPage() {
  return <section className="state-panel"><span className="eyebrow">ADMIN</span><h1>관리자 권한이 필요합니다</h1><p>직원 관리와 업무 흐름은 관리자 계정으로 확인할 수 있습니다.</p></section>;
}

function NotFoundPage() {
  return <section className="state-panel"><span className="eyebrow">404</span><h1>페이지를 찾을 수 없습니다</h1><p>요청한 화면이 존재하지 않습니다.</p></section>;
}

export default function App() {
  return <BrowserRouter><AuthProvider><AppRoutes /></AuthProvider></BrowserRouter>;
}
