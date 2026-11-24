import { useState, type ChangeEvent, type FormEvent } from "react";
import type { CheckInput, CheckProductType } from "../../types/domain";
import { Button } from "../ui/Button";

type CheckField = Exclude<keyof CheckInput, "attachments">;
type CheckErrors = Partial<Record<CheckField, string>>;

interface AdCheckFormProps {
  value: CheckInput;
  errors: CheckErrors;
  pending: boolean;
  onChange: (field: CheckField, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSaveDraft: () => void;
  files: File[];
  onFilesChange: (files: File[]) => void;
}

const allowedExtensions = ["pdf", "txt", "doc", "docx", "xls", "xlsx"];

export function AdCheckForm({ value, errors, pending, onChange, onSubmit, onSaveDraft, files, onFilesChange }: AdCheckFormProps) {
  const [fileError, setFileError] = useState<string | null>(null);
  const update = (field: CheckField) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => onChange(field, event.target.value);
  const updateFiles = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files ?? []);
    const invalid = selected.find((file) => !allowedExtensions.includes(file.name.split(".").pop()?.toLowerCase() ?? ""));
    if (invalid) { setFileError(`${invalid.name}은(는) 첨부할 수 없는 형식입니다.`); return; }
    setFileError(null);
    onFilesChange([...files, ...selected]);
    event.target.value = "";
  };
  const removeFile = (file: File) => onFilesChange(files.filter((item) => item !== file));

  return (
    <form className="check-form" onSubmit={onSubmit} noValidate>
      {Object.values(errors).length > 0 ? <div className="inline-error" role="alert"><ul>{Object.values(errors).map((message) => <li key={message}>{message}</li>)}</ul></div> : null}
      <label className="field">
        <span>광고명</span>
        <input value={value.title} onChange={update("title")} aria-invalid={Boolean(errors.title)} aria-describedby={errors.title ? "check-title-error" : undefined} />
        {errors.title ? <small id="check-title-error" className="field__error">{errors.title}</small> : null}
      </label>
      <fieldset className="check-form__fieldset">
        <legend>제품 유형</legend>
        <div className="check-form__options">
          {(["general-food", "health-functional-food"] as CheckProductType[]).map((productType) => (
            <label className={`choice-card ${value.productType === productType ? "choice-card--selected" : ""}`} key={productType}>
              <input type="radio" name="productType" value={productType} checked={value.productType === productType} onChange={update("productType")} />
              <span>{productType === "general-food" ? "일반식품" : "건강기능식품"}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <label className="field">
        <span>주요 원료</span>
        <input value={value.ingredient} onChange={update("ingredient")} placeholder="원료명을 입력하세요" />
      </label>
      <label className="field">
        <span>게시 채널</span>
        <select value={value.channel} onChange={update("channel")}>
          <option value="상세페이지">상세페이지</option>
          <option value="SNS">SNS</option>
          <option value="배너">배너</option>
        </select>
      </label>
      <label className="field">
        <span>광고 문구</span>
        <textarea value={value.copy} onChange={update("copy")} rows={8} maxLength={2000} aria-invalid={Boolean(errors.copy)} aria-describedby={errors.copy ? "check-copy-error" : undefined} />
        <small className="field__hint">{value.copy.length}/2,000자</small>
        {errors.copy ? <small id="check-copy-error" className="field__error">{errors.copy}</small> : null}
      </label>
      <div className="field">
        <span>첨부 파일</span>
        <input type="file" multiple accept=".pdf,.txt,.doc,.docx,.xls,.xlsx" onChange={updateFiles} aria-label="첨부 파일" aria-describedby="check-attachments-hint" />
        <small id="check-attachments-hint" className="field__hint">PDF, TXT, DOC, DOCX, XLS, XLSX 파일을 첨부할 수 있습니다.</small>
        {fileError ? <small className="field__error" role="alert">{fileError}</small> : null}
        {files.length > 0 ? <ul className="attachment-list">{files.map((file) => <li key={`${file.name}-${file.lastModified}`}><span>{file.name}</span><button type="button" className="button button--ghost button--compact" onClick={() => removeFile(file)} aria-label={`${file.name} 삭제`}>삭제</button></li>)}</ul> : null}
      </div>
      <div className="check-form__actions">
        <Button type="button" variant="secondary" onClick={onSaveDraft} disabled={pending}>임시 저장</Button>
        <Button type="submit" disabled={pending}>{pending ? "검사 준비 중…" : "자동 검사 시작"}</Button>
      </div>
    </form>
  );
}
