import { useState } from "react";
import type { DecisionInput, ReviewDetail } from "../../types/domain";
import { Button } from "../ui/Button";
import { DecisionConfirmDialog } from "./DecisionConfirmDialog";
import { RejectReasonDialog } from "./RejectReasonDialog";
import { ReadOnlyDecisionNotice } from "./ReadOnlyDecisionNotice";

export function ReviewDecisionForm({ detail, onSubmit, pending }: { detail: ReviewDetail; onSubmit: (input: DecisionInput) => void; pending: boolean }) {
  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState(detail.decisionReason ?? "");
  if (!detail.canDecide) return <ReadOnlyDecisionNotice reason={detail.readOnlyReason ?? "판정 권한이 없습니다."} />;
  return <div className="decision-form"><div className="decision-form__actions"><Button onClick={() => setApproveOpen(true)} disabled={pending}>적합</Button><Button variant="danger" onClick={() => setRejectOpen(true)} disabled={pending}>부적합</Button></div><DecisionConfirmDialog open={approveOpen} pending={pending} onClose={() => setApproveOpen(false)} onConfirm={() => { setApproveOpen(false); onSubmit({ reviewId: detail.id, decision: "approved" }); }} /><RejectReasonDialog open={rejectOpen} pending={pending} reason={rejectReason} onReasonChange={setRejectReason} onClose={() => setRejectOpen(false)} onConfirm={(reason) => { setRejectOpen(false); onSubmit({ reviewId: detail.id, decision: "rejected", reason }); }} /></div>;
}
