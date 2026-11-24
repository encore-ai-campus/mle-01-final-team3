import type { InputHTMLAttributes } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function TextField({ label, error, id, ...props }: TextFieldProps) {
  const inputId = id ?? `field-${label}`;
  return <label className="field"><span>{label}</span><input id={inputId} aria-invalid={Boolean(error)} aria-describedby={error ? `${inputId}-error` : undefined} {...props} />{error ? <small id={`${inputId}-error`} className="field__error">{error}</small> : null}</label>;
}
