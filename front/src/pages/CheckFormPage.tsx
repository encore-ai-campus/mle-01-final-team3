import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { CheckDataProvider } from "../types/api";
import type { CheckInput, DataState, CheckStartResult, CheckDraftResult } from "../types/domain";
import { PageHeader } from "../components/layout/PageHeader";
import { AdCheckForm } from "../components/domain/AdCheckForm";
import { Card } from "../components/ui/Card";

const initialInput: CheckInput = { title: "", productType: "health-functional-food", ingredient: "", channel: "상세페이지", copy: "" };

export function CheckFormPage({ provider }: { provider: CheckDataProvider }) {
  const navigate = useNavigate();
  const [value, setValue] = useState<CheckInput>(initialInput);
  const [errors, setErrors] = useState<Partial<Record<keyof CheckInput, string>>>({});
  const [mutation, setMutation] = useState<DataState<CheckStartResult | CheckDraftResult> | null>(null);
  const pending = mutation?.status === "loading";
  const update = (field: keyof CheckInput, nextValue: string) => setValue((current) => ({ ...current, [field]: field === "productType" ? nextValue as CheckInput["productType"] : nextValue }));
  const validate = () => {
    const nextErrors: Partial<Record<keyof CheckInput, string>> = {};
    if (!value.title.trim()) nextErrors.title = "광고명을 입력해 주세요.";
    if (!value.copy.trim()) nextErrors.copy = "광고 문구를 입력해 주세요.";
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };
  const start = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); if (!validate()) return; setMutation({ status: "loading" }); void provider.startCheck(value).then((result) => { setMutation(result); if (result.status === "ready") navigate(`/checks/${result.data.checkId}`); }); };
  const saveDraft = () => { setMutation({ status: "loading" }); void provider.saveDraft(value).then(setMutation); };

  return <div className="page-stack"><PageHeader eyebrow="MARKETING" title="광고 문구 검사" description="문구를 넣으면 AI가 법령 위반 의심 부분을 찾아줘요. 결과는 사전 점검용입니다." actions={<Link className="button button--secondary" to="/">홈으로</Link>} /><div className="check-layout"><Card><AdCheckForm value={value} errors={errors} pending={Boolean(pending)} onChange={update} onSubmit={start} onSaveDraft={saveDraft} />{mutation?.status === "not-configured" ? <div className="inline-error" role="alert">{mutation.message}</div> : null}{mutation?.status === "error" ? <div className="inline-error" role="alert">{mutation.error.message}</div> : null}{mutation?.status === "ready" && "draftId" in mutation.data ? <div className="success-banner" role="status">임시 저장 요청이 완료되었습니다.</div> : null}</Card><aside className="check-guide"><Card><h2>검사는 이렇게 진행돼요</h2><ol><li><strong>문장 나누기</strong><span>문구를 문장 단위로 나눠요.</span></li><li><strong>조항 찾기</strong><span>제품 유형에 맞는 조항과 원료 허가 문구를 찾아요.</span></li><li><strong>사례 찾기</strong><span>비슷한 적발 사례를 찾아요.</span></li><li><strong>판정·검증</strong><span>위반 의심·애매·안전을 구분하고 근거를 확인해요.</span></li><li><strong>대안 제안</strong><span>허가 범위 안에서 고친 문구를 만들어요.</span></li></ol></Card></aside></div></div>;
}
