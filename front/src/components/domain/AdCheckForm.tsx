import type { ChangeEvent, FormEvent } from "react";
import type { CheckInput, CheckProductType } from "../../types/domain";
import { Button } from "../ui/Button";

type CheckField = keyof CheckInput;
type CheckErrors = Partial<Record<CheckField, string>>;

interface AdCheckFormProps {
  value: CheckInput;
  errors: CheckErrors;
  pending: boolean;
  onChange: (field: CheckField, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSaveDraft: () => void;
}

export function AdCheckForm({ value, errors, pending, onChange, onSubmit, onSaveDraft }: AdCheckFormProps) {
  const update = (field: CheckField) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => onChange(field, event.target.value);

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
      <div className="check-form__actions">
        <Button type="button" variant="secondary" onClick={onSaveDraft} disabled={pending}>임시 저장</Button>
        <Button type="submit" disabled={pending}>{pending ? "검사 준비 중…" : "자동 검사 시작"}</Button>
      </div>
    </form>
  );
}
