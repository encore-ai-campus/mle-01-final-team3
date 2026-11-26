import { Link, useLocation } from "react-router-dom";
import type { ReviewTask } from "../../types/domain";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { withRouteContext } from "../../utils/routeContext";

export function TaskList({ tasks }: { tasks: ReviewTask[] }) {
  const { search } = useLocation();
  return <Card><div className="section-heading"><div><h2>할 일</h2><p>처리가 필요한 검토 업무입니다.</p></div><Link to={withRouteContext("/reviews", search)}>전체 보기</Link></div>{tasks.length === 0 ? <p>처리할 할 일이 없습니다.</p> : <ul className="task-list">{tasks.map((task) => <li key={task.id}><div><strong>{task.title}</strong><small>{task.advertiser}</small></div><Badge tone={task.status === "in-progress" ? "info" : "warning"}>{task.status}</Badge><Link to={withRouteContext(`/reviews/${task.id}`, search)}>열기</Link></li>)}</ul>}</Card>;
}
