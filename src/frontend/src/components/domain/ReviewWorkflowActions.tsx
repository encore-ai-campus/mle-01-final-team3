import { useState } from "react";
import type { ReviewJudgment, ReviewStatus, ReviewWorkflowAction, ReviewWorkflowRole } from "../../types/domain";
import { Button } from "../ui/Button";

interface ReviewWorkflowActionsProps {
  reviewId: string;
  status: ReviewStatus;
  judgment: ReviewJudgment;
  role: ReviewWorkflowRole;
  onAction: (action: ReviewWorkflowAction, legalOpinion?: string) => void;
  onClose: () => void;
  pending?: boolean;
}

export function ReviewWorkflowActions({ status, judgment, role, onAction, onClose, pending = false }: ReviewWorkflowActionsProps) {
  const [message, setMessage] = useState<string | null>(null);
  const [legalOpinion, setLegalOpinion] = useState("");
  const action = (next: ReviewWorkflowAction, label: string) => { setMessage(`${label} 처리를 진행했습니다.`); if (legalOpinion.trim()) onAction(next, legalOpinion); else onAction(next); };
  const resultPendingNotice = judgment === "pending" ? <p className="field__hint" role="status">검토 결과를 불러오는 중입니다.</p> : null;

  const legalReview = status === "legal-pending" || status === "legal-in-progress";
  if (legalReview && role === "legal") {
    const complete = (next: "complete-legal-needs-revision" | "complete-legal-continuable", label: string) => {
      if (!legalOpinion.trim()) { setMessage("의견을 입력해 주세요."); return; }
      action(next, label);
    };
    return <div className="workflow-actions"><label className="field"><span>의견 <span aria-hidden="true">*</span></span><textarea aria-label="의견" value={legalOpinion} onChange={(event) => setLegalOpinion(event.target.value)} required disabled={pending} /></label><div className="workflow-actions"><Button onClick={() => complete("complete-legal-needs-revision", "보완 필요")} disabled={pending}>보완 필요</Button><Button onClick={() => complete("complete-legal-continuable", "진행 가능")} disabled={pending}>진행 가능</Button><Button variant="secondary" onClick={() => action("close-review", "닫기")} disabled={pending}>닫기</Button></div>{message ? <p role="status">{message}</p> : null}</div>;
  }
  if (legalReview) return <div className="workflow-actions"><Button variant="secondary" onClick={onClose}>닫기</Button><p className="field__hint">법무팀 직원만 검토 결과를 처리할 수 있습니다.</p></div>;

  if (status === "completed") return <div className="workflow-actions"><Button variant="secondary" onClick={onClose}>닫기</Button></div>;
  if (status === "first-review-completed") return <div className="workflow-actions">{judgment === "approved" ? <Button onClick={() => action("request-legal-review", "법무팀 검토 요청")} disabled={pending}>법무팀 검토 요청</Button> : judgment === "rejected" ? <Button variant="danger" onClick={() => action("request-second-review", "2차 검토 요청")} disabled={pending}>2차 검토 요청</Button> : resultPendingNotice}<Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
  if (status === "second-review-completed") return <div className="workflow-actions">{judgment === "approved" ? <Button onClick={() => action("request-legal-review", "법무팀 검토 요청")} disabled={pending}>법무팀 검토 요청</Button> : judgment === "rejected" ? <Button variant="danger" onClick={() => action("delete-review", "삭제")} disabled={pending}>삭제</Button> : resultPendingNotice}<Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
  if (status === "legal-review" && role === "legal") return <div className="workflow-actions"><Button onClick={() => action("approve-legal", "승인")} disabled={pending}>승인</Button><Button variant="danger" onClick={() => action("reject-legal", "반려")} disabled={pending}>반려</Button><Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
  if (status === "legal-review") return <div className="workflow-actions"><Button variant="secondary" onClick={onClose}>닫기</Button><p className="field__hint">법무팀 직원만 승인 또는 반려할 수 있습니다.</p></div>;
  return <div className="workflow-actions"><Button variant="secondary" onClick={onClose}>닫기</Button>{message ? <p role="status">{message}</p> : null}</div>;
}
