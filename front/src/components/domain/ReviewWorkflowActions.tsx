import { useState } from "react";
import type { ReviewStatus } from "../../types/domain";
import { Button } from "../ui/Button";

interface ReviewWorkflowActionsProps { status: ReviewStatus; role: "legal" | "marketing"; onClose: () => void; }

export function ReviewWorkflowActions({ status, role, onClose }: ReviewWorkflowActionsProps) {
  const [message, setMessage] = useState<string | null>(null);
  const action = (label: string) => setMessage(`${label} 작업은 확인된 API 연결 후 저장됩니다.`);
  if (status === "completed") return <div className="workflow-actions"><Button variant="secondary" onClick={onClose}>닫기</Button></div>;
  if (status === "first-review-completed") return <div className="workflow-actions"><Button onClick={() => action("법무팀 검토 요청")}>법무팀 검토 요청</Button><Button variant="danger" onClick={() => action("2차 검토 요청")}>2차 검토 요청</Button><Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
  if (status === "second-review-completed") return <div className="workflow-actions"><Button onClick={() => action("법무팀 검토 요청")}>법무팀 검토 요청</Button><Button variant="danger" onClick={() => action("2차 검토 부적합")}>부적합</Button><Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
  if (status === "legal-review" && role === "legal") return <div className="workflow-actions"><Button onClick={() => action("승인")}>승인</Button><Button variant="danger" onClick={() => action("반려")}>반려</Button><Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
  return <div className="workflow-actions"><Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
}
