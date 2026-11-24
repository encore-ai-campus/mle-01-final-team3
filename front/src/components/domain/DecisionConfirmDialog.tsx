import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";

export function DecisionConfirmDialog({ open, onClose, onConfirm, pending }: { open: boolean; onClose: () => void; onConfirm: () => void; pending: boolean }) { return <Dialog open={open} title="적합 처리" description="이 보고서를 적합으로 처리하시겠습니까?" onClose={onClose}><div className="dialog-actions"><Button variant="secondary" onClick={onClose} disabled={pending}>취소</Button><Button onClick={onConfirm} disabled={pending}>{pending ? "저장 중…" : "확인"}</Button></div></Dialog>; }
