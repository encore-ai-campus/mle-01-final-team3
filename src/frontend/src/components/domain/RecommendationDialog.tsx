import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";

interface RecommendationDialogProps {
  open: boolean;
  recommendation: string;
  pending?: boolean;
  onRequestCheck: () => void;
  onClose: () => void;
}

export function RecommendationDialog({ open, recommendation, pending = false, onRequestCheck, onClose }: RecommendationDialogProps) {
  return (
    <Dialog
      open={open}
      title="AI 추천 광고 문구"
      description="추천 문구를 확인한 뒤 광고 문구 검사를 다시 요청할 수 있습니다."
      onClose={onClose}
    >
      <div className="recommendation-dialog__copy">
        <span className="page-header__eyebrow">추천 광고 문구</span>
        <p>{recommendation}</p>
      </div>
      <div className="workflow-actions">
        <Button onClick={onRequestCheck} disabled={pending}>광고 문구 검사 요청</Button>
        <Button variant="secondary" onClick={onClose} disabled={pending}>닫기</Button>
      </div>
    </Dialog>
  );
}
