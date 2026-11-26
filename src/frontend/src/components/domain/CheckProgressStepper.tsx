import type { CheckProgressStep } from "../../types/domain";
import { Badge } from "../ui/Badge";

const labels = { completed: "완료", "in-progress": "진행 중", skipped: "건너뜀", waiting: "대기" } as const;
const tones = { completed: "success", "in-progress": "info", skipped: "neutral", waiting: "neutral" } as const;

export function CheckProgressStepper({ steps, currentStep }: { steps: CheckProgressStep[]; currentStep: string }) {
  return <ol className="progress-stepper">{steps.map((step) => <li className={`progress-step progress-step--${step.status}`} key={step.id} aria-current={step.id === currentStep ? "step" : undefined}><div><Badge tone={tones[step.status]}>{labels[step.status]}</Badge><strong>{step.label}</strong><small>{step.owner}</small></div><p>{step.detail}</p></li>)}</ol>;
}
