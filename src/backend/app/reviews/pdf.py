"""[PDF 저장]. 설계서 5장 '알림·마이페이지·PDF' (M-20·LG-16).

GET /reviews/{reviewId}/report.pdf                 마케팅: 그 검토 건의 최신 보고서 (팀 공유라 다른 작성자 것도 가능)
GET /legal-submissions/{submissionId}/report.pdf   법무: 요청 시점에 고정된 보고서 (팀 전원 가능)

한글은 reportlab 내장 CID 글꼴(HYGothic-Medium)로 쓴다. 글꼴 파일을 따로 두지 않는다.
파일 이름은 Content-Disposition에 담는다 (CORS expose_headers에 들어 있어 프론트가 읽을 수 있다).
"""

from io import BytesIO
from urllib.parse import quote
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session as DbSession

from app.core.deps import Lawyer, Marketer, get_db
from app.core.errors import ApiError
from app.core.times import to_kst
from app.models import LegalSubmission, Report, Review, User
from app.reviews.state import current_report, get_review_or_404, latest_legal

router = APIRouter()

FONT = "HYGothic-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))

CATEGORY = {"HEALTH_FUNCTIONAL_FOOD": "건강기능식품", "GENERAL_FOOD": "일반식품", "CHILDREN_PREFERRED_FOOD": "어린이기호식품"}
CHANNEL = {"DETAIL_PAGE": "상세페이지", "SNS": "SNS", "BANNER": "배너"}
DECISION = {"SUITABLE": "적합", "UNSUITABLE": "부적합"}
LEGAL_STATUS = {"PENDING": "검토 대기", "IN_REVIEW": "검토 중", "OPINION_SENT": "검토 의견 전송"}

_BASE = ParagraphStyle("base", fontName=FONT, fontSize=10, leading=15, wordWrap="CJK")
H1 = ParagraphStyle("h1", parent=_BASE, fontSize=16, leading=22, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=_BASE, fontSize=12, leading=18, spaceBefore=10, spaceAfter=4)
BODY = _BASE
SMALL = ParagraphStyle("small", parent=_BASE, fontSize=9, leading=13, textColor="#444444")


def _p(text: str | None, style: ParagraphStyle = BODY) -> Paragraph:
    """사용자·AI가 쓴 글은 태그로 해석되지 않게 escape하고, 줄바꿈은 그대로 둔다."""
    return Paragraph(escape(text or "-").replace("\n", "<br/>"), style)


def _when(dt) -> str:
    return to_kst(dt).strftime("%Y-%m-%d %H:%M") if dt else "-"


def _info_table(rows: list[tuple[str, str]]) -> Table:
    table = Table([[_p(k, SMALL), _p(v)] for k, v in rows], colWidths=[32 * mm, None])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, "#DDDDDD"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))  # fmt: skip
    return table


def build_pdf(review: Review, report: Report, author: User | None, legal: LegalSubmission | None) -> bytes:
    """보고서 1개를 PDF로. legal은 이 보고서로 한 법무 요청(없으면 None)."""
    story = [
        _p(f"{review.title} 검토 보고서", H1),
        _p(f"{report.version}차 심의 · v{report.version} · AI 판정 {DECISION.get(report.decision, report.decision)}", SMALL),
        Spacer(1, 4 * mm),
        _info_table([
            ("제품 분류", CATEGORY.get(review.product_category, review.product_category)),
            ("게시 채널", CHANNEL.get(review.channel, review.channel)),
            ("주요 원료", ", ".join(review.main_ingredients or []) or "-"),
            ("작성자", author.name if author else "-"),
            ("검토 요청", _when(review.created_at)),
            ("보고서 작성", _when(report.created_at)),
        ]),  # fmt: skip
        _p("검토한 광고 문구", H2),
        _p(report.reviewed_text),
        _p("검토 요약", H2),
        _p(report.summary),
        _p("문장별 판정", H2),
    ]
    for i, f in enumerate(report.findings, 1):
        head = f"{i}. [{DECISION.get(f.get('decision'), f.get('decision'))}] {f.get('text', '')}"
        story.append(_p(head))
        lines = [("판단 근거", f.get("rationale"))]
        if f.get("violationCode"):
            lines.append(("위반 유형", f"별표 1 {f['violationCode']}"))
        for s in f.get("sources") or []:
            src = f"{s.get('title', '')} {s.get('reference', '')}"
            if s.get("noticeNo"):
                src += f" (고시 {s['noticeNo']}, 시행 {s.get('effectiveDate') or '-'})"
            if s.get("lawText"):
                src += f"\n{s['lawText']}"
            lines.append(("근거", src))
        for c in f.get("referenceCases") or []:
            lines.append(("참고 사례", f"{c.get('title', '')}: {c.get('summary', '')}"))
        if f.get("alternativeText"):
            lines.append(("대안 문구 예시", f["alternativeText"]))
        story += [_info_table(lines), Spacer(1, 3 * mm)]
    story += [_p("개선 의견", H2), _p(report.improvement_note)]
    if legal is not None:
        story += [
            _p("법무 검토", H2),
            _info_table([
                ("처리 상태", LEGAL_STATUS.get(legal.status, legal.status)),
                ("요청 시각", _when(legal.sent_at)),
                ("의견 전송", _when(legal.decided_at)),
                ("검토 의견", legal.reason or "-"),
            ]),  # fmt: skip
        ]

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"{review.title} 검토 보고서",
    )  # fmt: skip
    doc.build(story)
    return buf.getvalue()


def pdf_response(content: bytes, filename: str) -> Response:
    # 한글 파일 이름은 RFC 5987 형식(filename*)으로, 옛 브라우저용 filename은 영문으로
    disposition = f"attachment; filename=\"report.pdf\"; filename*=UTF-8''{quote(filename)}"
    return Response(content, media_type="application/pdf", headers={"Content-Disposition": disposition})


@router.get(
    "/reviews/{reviewId}/report.pdf",
    summary="[PDF 저장] 마케팅 (M-20)",
    description="그 검토 건의 최신 보고서를 PDF로. 팀 공유라 다른 작성자 것도 받을 수 있다. 보고서가 아직 없으면 404",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def review_pdf(reviewId: str, user: Marketer, db: DbSession = Depends(get_db)):
    review = get_review_or_404(db, reviewId)
    report = current_report(db, review.id)
    if report is None:
        raise ApiError(404, "NOT_FOUND", "아직 보고서가 없습니다.")
    legal = latest_legal(db, review.id)
    legal = legal if legal is not None and legal.report_run_id == report.run_id else None
    author = db.get(User, review.author_id) if review.author_id else None
    content = build_pdf(review, report, author, legal)
    return pdf_response(content, f"{review.title} 검토 보고서 v{report.version}.pdf")


@router.get(
    "/legal-submissions/{submissionId}/report.pdf",
    summary="[PDF 저장] 법무 (LG-16)",
    description="요청 시점에 고정된 보고서와 법무 상태·검토 의견을 PDF로. 법무팀 전원 가능",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def submission_pdf(submissionId: str, user: Lawyer, db: DbSession = Depends(get_db)):
    sub = db.get(LegalSubmission, submissionId)
    if sub is None:
        raise ApiError(404, "NOT_FOUND", "보고서를 찾을 수 없습니다.")
    review = db.get(Review, sub.review_id)
    report = db.get(Report, sub.report_run_id)
    author = db.get(User, sub.sender_id) if sub.sender_id else None
    content = build_pdf(review, report, author, sub)
    return pdf_response(content, f"{review.title} 검토 보고서 v{report.version}.pdf")
