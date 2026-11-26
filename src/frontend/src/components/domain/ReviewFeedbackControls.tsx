import { useState } from "react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

type Feedback = "correct" | "incorrect";

export function ReviewFeedbackControls() {
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  return <Card className="review-feedback"><div><h2>AI 판정 피드백</h2><p>AI 근거가 실제 문구와 맞는지 표시해 주세요.</p></div><div className="review-feedback__actions"><Button variant={feedback === "correct" ? "primary" : "secondary"} onClick={() => setFeedback("correct")}>맞음</Button><Button variant={feedback === "incorrect" ? "danger" : "secondary"} onClick={() => setFeedback("incorrect")}>다름</Button></div>{feedback ? <p className="review-feedback__status" role="status">{feedback === "correct" ? "맞음" : "다름"}으로 선택했습니다. 피드백 저장 API 연결 후 서버에 반영됩니다.</p> : <p className="field__hint">현재는 화면 선택만 제공되며 저장 API는 연결되지 않았습니다.</p>}</Card>;
}
