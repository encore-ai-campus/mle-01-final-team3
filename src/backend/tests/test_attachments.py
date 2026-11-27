"""첨부 파일: 올리기, 검토 요청에 붙이기, Agent 서명 URL로 내려받기."""

from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import API

PDF = b"%PDF-1.4 test"


def upload(c, name="근거자료.pdf", data=PDF):
    return c.post(f"{API}/attachments", files={"file": (name, data)}, data={"purpose": "AD_COPY"})


def test_upload_and_attach_to_review(mkt, agent):
    r = upload(mkt)
    assert r.status_code == 201
    att = r.json()
    assert att["filename"] == "근거자료.pdf" and att["size"] == len(PDF)

    rv = mkt.post(f"{API}/reviews", json={"title": "첨부 광고", "productCategory": "GENERAL_FOOD", "text": "문구",
                                         "attachmentIds": [att["attachmentId"]]})  # fmt: skip
    assert rv.status_code == 202
    job_att = agent.last()["attachments"]
    assert [a["attachmentId"] for a in job_att] == [att["attachmentId"]] and job_att[0]["filename"] == "근거자료.pdf"

    # Agent가 서명 URL로 내려받는다 (로그인 없이)
    url = urlsplit(job_att[0]["url"])
    got = TestClient(app).get(f"{url.path}?{url.query}")
    assert got.status_code == 200 and got.content == PDF
    assert got.headers["content-type"] == "application/pdf"  # 저장은 "pdf", 내려받을 때 MIME

    bad = TestClient(app).get(url.path + "?" + url.query.replace("sig=", "sig=0"))
    assert bad.status_code == 401


def test_unsupported_type_415(mkt):
    r = upload(mkt, "image.png")
    assert r.status_code == 415 and r.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_filename_over_255_is_422(mkt):
    r = upload(mkt, "가" * 252 + ".pdf")  # 256자
    assert r.status_code == 422
    assert r.json()["error"]["fieldErrors"] == [{"field": "file", "code": "INVALID"}]
    assert upload(mkt, "가" * 251 + ".pdf").status_code == 201  # 255자


def test_file_over_10mb_413(mkt):
    r = upload(mkt, "big.pdf", b"0" * (10 * 1024 * 1024 + 1))
    assert r.status_code == 413 and r.json()["error"]["code"] == "ATTACHMENT_LIMIT_EXCEEDED"


def test_total_over_10mb_413(mkt):
    a = upload(mkt, "a.pdf", b"0" * (6 * 1024 * 1024)).json()["attachmentId"]
    b = upload(mkt, "b.pdf", b"0" * (6 * 1024 * 1024)).json()["attachmentId"]
    r = mkt.post(f"{API}/reviews", json={"title": "t", "productCategory": "GENERAL_FOOD", "text": "x",
                                        "attachmentIds": [a, b]})  # fmt: skip
    assert r.status_code == 413


def test_unknown_or_foreign_or_used_attachment_422(mkt, mkt_b):
    mine = upload(mkt).json()["attachmentId"]
    other = upload(mkt_b).json()["attachmentId"]
    body = {"title": "t", "productCategory": "GENERAL_FOOD", "text": "x"}
    r = mkt.post(f"{API}/reviews", json={**body, "attachmentIds": [mine, other, "att_none"]})
    assert r.status_code == 422
    assert [e["field"] for e in r.json()["error"]["fieldErrors"]] == ["attachmentIds[1]", "attachmentIds[2]"]

    assert mkt.post(f"{API}/reviews", json={**body, "attachmentIds": [mine]}).status_code == 202
    r = mkt.post(f"{API}/reviews", json={**body, "attachmentIds": [mine]})  # 이미 다른 검토 건에 붙음
    assert r.status_code == 422
