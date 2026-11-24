import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { TextField } from "../ui/TextField";

export function RejectReasonDialog({ open, onClose, onConfirm, pending, reason, onReasonChange }: { open: boolean; onClose: () => void; onConfirm: (reason: string) => void; pending: boolean; reason: string; onReasonChange: (reason: string) => void }) {
  const error = reason.trim() ? undefined : "부적합 사유를 입력해 주세요.";
  return <Dialog open={open} title="부적합 사유 입력" description="처리 결과에 남길 사유를 입력하세요." onClose={onClose}><TextField label="부적합 사유" value={reason} error={reason.length > 0 && !reason.trim() ? error : undefined} onChange={(event) => onReasonChange(event.target.value)} /><div className="dialog-actions"><Button variant="secondary" onClick={onClose} disabled={pending}>취소</Button><Button variant="danger" onClick={() => { if (reason.trim()) onConfirm(reason.trim()); }} disabled={pending || !reason.trim()}>{pending ? "저장 중…" : "부적합 처리"}</Button></div></Dialog>;
}
