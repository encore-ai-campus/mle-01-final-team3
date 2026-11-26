import type { ReactNode } from "react";
import { Card } from "../ui/Card";

export function SummaryCard({ label, value, tone = "neutral", icon }: { label: string; value: number; tone?: "neutral" | "info" | "success" | "warning"; icon?: ReactNode }) {
  return <Card className={`summary-card summary-card--${tone}`}><div className="summary-card__label">{icon}<span>{label}</span></div><strong>{value}</strong></Card>;
}
