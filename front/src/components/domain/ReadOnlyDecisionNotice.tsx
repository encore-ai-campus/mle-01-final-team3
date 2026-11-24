export function ReadOnlyDecisionNotice({ reason }: { reason: string }) { return <div className="read-only-notice" role="status"><strong>읽기 전용 보고서</strong><p>{reason}</p></div>; }
