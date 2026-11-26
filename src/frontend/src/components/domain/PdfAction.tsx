import { Button } from "../ui/Button";

export function PdfAction({ pdfUrl }: { pdfUrl: string | null }) { return pdfUrl ? <a className="button button--secondary" href={pdfUrl} target="_blank" rel="noreferrer">PDF 저장</a> : <Button variant="secondary" disabled title="검증된 PDF 기능이 연결되지 않았습니다.">PDF 저장 불가</Button>; }
