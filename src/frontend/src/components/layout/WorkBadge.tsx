import { useEffect, useState } from "react";
import type { DataProvider } from "../../types/api";
import { withRouteContext } from "../../utils/routeContext";
import { countActionableReviews, type WorkDepartment } from "../../utils/workBadge";

interface WorkBadgeProps {
  provider: DataProvider;
  department: WorkDepartment;
  currentPath: string;
  currentSearch: string;
  onNavigate: (path: string) => void;
}

export function WorkBadge({ provider, department, currentPath, currentSearch, onNavigate }: WorkBadgeProps) {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    setCount(null);
    void provider.listReviews({}).then((result) => {
      if (!active) return;
      setCount(result.status === "ready" ? countActionableReviews(result.data, department) : null);
    }).catch(() => {
      if (active) setCount(null);
    });
    return () => {
      active = false;
    };
  }, [currentPath, department, provider]);

  const label = count === null ? "처리할 업무 확인" : count === 0 ? "처리할 업무 없음" : `처리할 업무 ${count}건`;
  const displayCount = count === null || count === 0 ? null : count >= 100 ? "99+" : String(count);
  const destination = withRouteContext("/reviews", currentSearch);

  return (
    <button
      type="button"
      className="work-badge"
      aria-label={label}
      title={label}
      onClick={() => onNavigate(destination)}
    >
      <svg className="work-badge__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
      </svg>
      {displayCount ? <span className="work-badge__count" aria-hidden="true">{displayCount}</span> : null}
      <span className="sr-only">{label}</span>
    </button>
  );
}
