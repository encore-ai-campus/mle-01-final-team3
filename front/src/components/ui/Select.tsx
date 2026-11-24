import type { SelectHTMLAttributes } from "react";

interface SelectOption { value: string; label: string; }
interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: SelectOption[];
}

export function Select({ label, options, id, ...props }: SelectProps) {
  const selectId = id ?? `select-${label}`;
  return <label className="field"><span>{label}</span><select id={selectId} {...props}>{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>;
}
