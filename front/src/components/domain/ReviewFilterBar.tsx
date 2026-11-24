import type { ReviewQuery } from "../../types/api";
import { Select } from "../ui/Select";
import { TextField } from "../ui/TextField";

interface ReviewFilterBarProps { value: ReviewQuery; onChange: (value: ReviewQuery) => void; }
export function ReviewFilterBar({ value, onChange }: ReviewFilterBarProps) {
  return <div className="filter-bar"><TextField label="검색" value={value.search ?? ""} placeholder="광고명·작성자 검색" onChange={(event) => onChange({ ...value, search: event.target.value || undefined })} /><Select label="처리 상태" value={value.processingStatus ?? ""} onChange={(event) => onChange({ ...value, processingStatus: event.target.value || undefined })} options={[{ value: "", label: "전체 상태" }, { value: "first-review-completed", label: "1차 검토 완료" }, { value: "second-review-completed", label: "2차 검토 완료" }, { value: "legal-review", label: "법무팀 검토" }, { value: "completed", label: "검토 완료" }, { value: "waiting", label: "검토 대기" }, { value: "in-progress", label: "검토 중" }]} /><Select label="AI 판정" value={value.aiJudgment ?? ""} onChange={(event) => onChange({ ...value, aiJudgment: event.target.value || undefined })} options={[{ value: "", label: "전체 판정" }, { value: "pending", label: "판정 대기" }, { value: "hold", label: "판단 보류" }, { value: "approved", label: "적합" }, { value: "rejected", label: "부적합" }]} /><TextField label="담당자" value={value.assignee ?? ""} placeholder="담당자" onChange={(event) => onChange({ ...value, assignee: event.target.value || undefined })} /></div>;
}
