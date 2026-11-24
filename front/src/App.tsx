import { useMemo } from "react";
import { BrowserRouter, Route, Routes, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { createDataProvider } from "./api/providerFactory";
import { createCheckProvider } from "./api/checkProvider";
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

function AppRoutes() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const scenarioValue = searchParams.get("scenario");
  const scenario = isArtifactScenarioId(scenarioValue) ? scenarioValue : "LG-1";
  const provider = useMemo(() => createDataProvider(scenario), [scenario]);
  const checkProvider = useMemo(() => createCheckProvider(scenario), [scenario]);

  return <AppShell currentPath={location.pathname} user={{ name: "로그인 사용자", department: "부서 미확인" }} onNavigate={(path) => navigate(path)}><Routes><Route path="/" element={<DashboardPage provider={provider} />} /><Route path="/checks/new" element={<CheckFormPage provider={checkProvider} />} /><Route path="/checks/:checkId" element={<CheckResultPage provider={checkProvider} />} /><Route path="/progress" element={<ProgressPage provider={checkProvider} />} /><Route path="/progress/:checkId" element={<ProgressPage provider={checkProvider} />} /><Route path="/reviews" element={<ReviewsPage provider={provider} />} /><Route path="/reviews/:reviewId" element={<ReviewDetailPage provider={provider} />} /><Route path="/account" element={<AccountPage provider={provider} />} /><Route path="/notifications" element={<NotificationsPage provider={provider} />} /><Route path="*" element={<NotFoundPage />} /></Routes></AppShell>;
}

function NotFoundPage() {
  return <section className="state-panel"><span className="eyebrow">404</span><h1>페이지를 찾을 수 없습니다</h1><p>요청한 화면이 존재하지 않습니다.</p></section>;
}

export default function App() {
  return <BrowserRouter><AppRoutes /></BrowserRouter>;
}
