import { useState, type FormEvent } from "react";
import type { ReviewDetail, ReviewStatus, ReviewUpdateInput } from "../../types/domain";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface ReviewEditFormProps {
  detail: ReviewDetail;
  pending: boolean;
  onSave: (input: ReviewUpdateInput) => void;
  onCancel: () => void;
}

const statusLabels: Record<ReviewStatus, string> = { waiting: "검토 대기", "in-progress": "검토 중", completed: "검토 완료", "first-review-completed": "1차 검토 완료", "second-review-completed": "2차 검토 완료", "legal-review": "법무팀 검토", "marketing-completed-approved": "[마케팅]검토 완료(적합)", "marketing-completed-rejected": "[마케팅]검토 완료(부적합)", "legal-pending": "[법무]검토 대기", "legal-in-progress": "[법무]검토 중", "legal-completed-approved": "[법무]검토 완료(적합)", "legal-completed-rejected": "[법무]검토 완료(부적합)", "legal-completed-needs-revision": "[법무]검토 완료(보완 필요)", "legal-completed-continuable": "[법무]검토 완료(진행 가능)", "marketing-cancelled": "[마케팅]심의 취소" };

export function ReviewEditForm({ detail, pending, onSave, onCancel }: ReviewEditFormProps) {
  const [value, setValue] = useState<ReviewUpdateInput>({ title: detail.title, category: detail.category, copy: detail.copy });
  const update = (field: keyof ReviewUpdateInput, next: string) => setValue((current) => ({ ...current, [field]: next }));
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); onSave(value); };

  return <Card><div className="section-heading"><div><h2>검토 보고서 수정</h2><p>광고명, 분류, 상세내용만 수정할 수 있습니다.</p></div></div><form className="review-edit-form" onSubmit={submit}><label className="field"><span>광고명</span><input value={value.title} onChange={(event) => update("title", event.target.value)} required /></label><label className="field"><span>작성자</span><input value={detail.author} readOnly /></label><label className="field"><span>분류</span><input value={value.category} onChange={(event) => update("category", event.target.value)} required /></label><label className="field"><span>상태</span><input value={statusLabels[detail.status]} readOnly /></label><label className="field"><span>전송일</span><input value={detail.sentAt} readOnly /></label><label className="field"><span>상세내용</span><textarea value={value.copy} onChange={(event) => update("copy", event.target.value)} rows={6} required /></label><div className="dialog-actions"><Button type="button" variant="secondary" onClick={onCancel} disabled={pending}>취소</Button><Button type="submit" disabled={pending}>{pending ? "저장 중…" : "저장"}</Button></div></form></Card>;
}
