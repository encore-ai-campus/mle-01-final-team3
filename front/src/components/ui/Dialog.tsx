import { useLayoutEffect, useRef, type ReactNode } from "react";

interface DialogProps {
  open: boolean;
  title: string;
  description?: string;
  children: ReactNode;
  onClose: () => void;
}

export function Dialog({ open, title, description, children, onClose }: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    if (!open) return;
    returnFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const firstFocusable = dialogRef.current?.querySelector<HTMLElement>(".dialog__body button, .dialog__body [href], .dialog__body input, .dialog__body select, .dialog__body textarea, .dialog__body [tabindex]:not([tabindex='-1']), button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
    firstFocusable?.focus();
    return () => returnFocusRef.current?.focus();
  }, [open]);

  if (!open) return null;

  return (
    <div className="dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div
        ref={dialogRef}
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby={description ? "dialog-description" : undefined}
        onKeyDown={(event) => { if (event.key === "Escape") onClose(); }}
      >
        <div className="dialog__header">
          <div>
            <h2 id="dialog-title">{title}</h2>
            {description ? <p id="dialog-description">{description}</p> : null}
          </div>
          <button type="button" className="icon-button" aria-label="닫기" onClick={onClose}>×</button>
        </div>
        <div className="dialog__body">{children}</div>
      </div>
    </div>
  );
}
