# ---------- 완성 파이프라인 (기존 뼈대 코드는 아래에 보존) ----------
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data_chunking"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_TYPES = {"article", "paragraph", "item", "subitem", "table", "appendix", "addendum", "case", "guide", "record"}

def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _registry():
    p = ROOT / "data" / "document_registry.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
    by_path = {}
    for r in rows:
        raw = r["source_path"].replace("\\", "/")
        by_path[raw] = r
        by_path[raw.removeprefix("data/")] = r
    return rows, by_path

def _src(path):
    return path.relative_to(ROOT).as_posix()

def _base(doc, cid, typ, text, src, parent=None, page=None, span=None, **loc):
    return {"document_id": doc, "chunk_id": cid, "parent_id": parent,
            "chunk_type": typ, "text": text.strip(), "source_path": src,
            "source_id": doc, "source_chunk_id": cid,
            "source_page": page, "source_span": span,
            "article": loc.get("article"), "paragraph": loc.get("paragraph"),
            "item": loc.get("item"), "subitem": loc.get("subitem")}

def _num(value):
    if value is None: return None
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else None

def _law_chunks(d, doc, src):
    root = d.get("법령", d)
    out = []
    articles = root.get("조문", {}).get("조문단위", [])
    if isinstance(articles, dict): articles = [articles]
    for a in articles:
        an = _num(a.get("조문번호")); aid = f"{doc}:A{an:03d}"
        text = a.get("조문내용", "")
        out.append(_base(doc, aid, "article", text, src, span=f"제{an}조", article=an))
        para = a.get("항", {})
        plist = para.get("항단위", para if isinstance(para, list) else []) if isinstance(para, dict) else para
        if isinstance(plist, dict): plist = [plist]
        if not plist and a.get("항"):
            plist = [a.get("항")] if isinstance(a.get("항"), dict) and any(k in a["항"] for k in ("항번호", "항내용", "호")) else []
        for pi, p in enumerate(plist or [], 1):
            pn = _num(p.get("항번호")) or pi; pid = f"{aid}:P{pn:03d}"
            pt = p.get("항내용", p.get("내용", ""))
            out.append(_base(doc, pid, "paragraph", pt, src, aid, span=f"제{an}조 제{pn}항", article=an, paragraph=pn))
            items = p.get("호", p.get("호단위", []))
            if isinstance(items, dict): items = [items]
            for ii, it in enumerate(items or [], 1):
                inn = _num(it.get("호번호")) or ii; iid=f"{pid}:I{inn:03d}"
                itext=it.get("호내용", it.get("내용", ""))
                out.append(_base(doc,iid,"item",itext,src,pid,span=f"제{an}조 제{pn}항 제{inn}호",article=an,paragraph=pn,item=inn))
                subs=it.get("목", it.get("목단위", [])); subs=[subs] if isinstance(subs,dict) else subs
                for si, sub in enumerate(subs or [],1):
                    sn=_num(sub.get("목번호")) or si; sid=f"{iid}:M{sn:03d}"
                    out.append(_base(doc,sid,"subitem",sub.get("목내용",sub.get("내용","")),src,iid,span=f"제{an}조 제{pn}항 제{inn}호 {sn}목",article=an,paragraph=pn,item=inn,subitem=sn))
    for i, app in enumerate(root.get("별표", {}).get("별표단위", []) or [], 1):
        aid=f"{doc}:B{i:03d}"; text="\n".join(" ".join(x) if isinstance(x,list) else str(x) for x in app.get("별표내용", []))
        out.append(_base(doc,aid,"appendix",(app.get("별표제목","")+"\n"+text),src,span=f"별표 {i}"))
    return out

def _admin_chunks(d, doc, src):
    root=d.get("AdmRulService", d); out=[]
    contents=root.get("조문내용", [])
    if isinstance(contents, str): contents=[contents]
    for i, text in enumerate(contents,1):
        m=re.search(r"제\s*(\d+)\s*조", str(text)); an=int(m.group(1)) if m else i
        cid=f"{doc}:A{an:03d}"; out.append(_base(doc,cid,"article",str(text),src,span=f"제{an}조",article=an))
    apps = root.get("별표",{})
    apps = apps.get("별표단위",[]) if isinstance(apps,dict) else []
    for i, app in enumerate(apps or [],1):
        if not isinstance(app, dict):
            app = {"별표제목": "", "별표내용": [str(app)]}
        cid=f"{doc}:B{i:03d}"; text="\n".join(" ".join(x) if isinstance(x,list) else str(x) for x in app.get("별표내용",[]))
        out.append(_base(doc,cid,"table",app.get("별표제목","")+"\n"+text,src,span=f"별표 {i}"))
    return out

def _ocr_chunks(d, doc, src, typ):
    out=[]; logs=[]; buf=[]; start=None; seg=0
    heading=re.compile(r"^(?:제\s*\d+\s*조|\d+[.)]\s+|[□■ㅇ]|사례\s*\d*|위반\s*(?:내용|표현)|판단|조치|근거|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.)")
    for p in d.get("pages",[]):
        page=p.get("page_number"); lines=[str(x) for x in p.get("lines",[]) if not str(x).startswith("<img")]
        if p.get("character_count",len("".join(lines)))<10 or sum(len(x.strip())<=1 for x in lines)>=5:
            logs.append({"event":"skipped_page","document_id":doc,"source_page":page}); continue
        for line in lines:
            if buf and heading.match(line.strip()):
                seg+=1; cid=f"{doc}:PG{int(start):03d}:S{seg:03d}"
                out.append(_base(doc,cid,typ,"\n".join(buf),src,page=start,span=f"page {start}")); buf=[]
            if not buf: start=page
            buf.append(line)
    if buf:
        seg+=1; cid=f"{doc}:PG{int(start):03d}:S{seg:03d}"
        out.append(_base(doc,cid,typ,"\n".join(buf),src,page=start,span=f"page {start}"))
    return out,logs

def _records(d, doc, src, kind):
    arr=d if isinstance(d,list) else next((v for v in d.values() if isinstance(v,list)), [])
    out=[]
    for i, row in enumerate(arr,1):
        key=str(row.get("id",i)) if isinstance(row,dict) else str(i)
        text=json.dumps(row,ensure_ascii=False) if isinstance(row,dict) else str(row)
        out.append(_base(doc,f"{doc}:R{i:06d}",kind,text,src,span=f"record {key}"))
    return out

def _format(d):
    if isinstance(d,dict) and "pages" in d: return "ocr"
    if isinstance(d,dict) and "법령" in d: return "law"
    if isinstance(d,dict) and "AdmRulService" in d: return "admin"
    if isinstance(d,list): return "records"
    return "records"

def run_pipeline():
    rows, by_path = _registry(); selected=[]; seen=set(); log=[]
    inputs=ROOT/"data_parsing"
    for p in sorted(inputs.rglob("*.json")):
        key=p.relative_to(ROOT).as_posix(); reg=by_path.get(key) or by_path.get(("data/"+key))
        if not reg:
            log.append({"event":"unregistered_source","source_path":key}); continue
        # 대규모 상품 카탈로그는 전달 브리프의 5개 청킹 포맷 대상이 아니며,
        # 그대로 JSON 문자열 청크로 만들면 수십만~백만 개의 비의미 청크가 된다.
        # 원본은 보존하고 제외 사실만 품질 로그에 남긴다.
        if any(token in key for token in ("/C002/", "/I1250/", "제품정보-", "food_raw_material")):
            log.append({"event":"source_excluded","document_id":reg["document_id"],"source_path":key,"reason":"large_catalog_out_of_chunking_brief"})
            continue
        # registry is authoritative; structural JSON wins over OCR for the same registered document title/version
        d=_read_json(p); fmt=_format(d); title=reg.get("title",""); version=reg.get("version","")
        group=(title,version)
        if fmt=="ocr" and any(x[0]==group and x[1] in {"law","admin"} for x in selected):
            log.append({"event":"duplicate_excluded","document_id":reg["document_id"],"source_path":key,"reason":"structured_source_preferred"}); continue
        if group in seen or any(x[2]["document_id"] == reg["document_id"] for x in selected):
            log.append({"event":"duplicate_excluded","document_id":reg["document_id"],"source_path":key,"reason":"same_registry_title_version"}); continue
        seen.add(group); selected.append((group,fmt,reg,p,d))
    chunks=[]
    for _,fmt,reg,p,d in selected:
        doc=reg["document_id"]; src=reg["source_path"]
        if fmt=="law": cs=_law_chunks(d,doc,src)
        elif fmt=="admin": cs=_admin_chunks(d,doc,src)
        elif fmt=="ocr": cs,lg=_ocr_chunks(d,doc,src,"case" if "사례" in reg.get("title","") else "guide"); log.extend(lg)
        else: cs=_records(d,doc,src,"case" if "위반" in reg.get("title","") else "record")
        chunks.extend(cs); log.append({"event":"document_processed","document_id":doc,"chunk_count":len(cs),"source_path":src})
    # 동일 문서 안에 반복 조문이 존재하는 원본도 있으므로 전역 ID를 최종 보정한다.
    # 원문 위치는 유지하고, 반복 발생분에만 안정적인 occurrence 접미사를 붙인다.
    occurrences = defaultdict(int)
    for x in chunks:
        base_id = x["chunk_id"]; occurrences[base_id] += 1
        if occurrences[base_id] > 1:
            new_id = f"{base_id}:V{occurrences[base_id]:03d}"
            x["chunk_id"] = new_id; x["source_chunk_id"] = new_id
            log.append({"event":"duplicate_chunk_id_resolved","original_chunk_id":base_id,"chunk_id":new_id,"document_id":x["document_id"]})
    ids={x["chunk_id"] for x in chunks}; invalid=[]
    for x in chunks:
        if x["chunk_type"] not in ALLOWED_TYPES: invalid.append({"event":"invalid_chunk_type","chunk_id":x["chunk_id"]})
        if x["parent_id"] is not None and x["parent_id"] not in ids: invalid.append({"event":"invalid_parent_id","chunk_id":x["chunk_id"],"parent_id":x["parent_id"]})
    log.extend(invalid); log.append({"event":"validation_summary","chunk_count":len(chunks),"document_count":len(set(x["document_id"] for x in chunks)),"duplicate_chunk_id_count":len(chunks)-len(ids),"invalid_reference_count":len(invalid)})
    (OUTPUT_DIR/"structured_chunks.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in chunks)+"\n",encoding="utf-8")
    schema={"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["document_id","chunk_id","parent_id","chunk_type","text","source_path","source_id","source_chunk_id","source_page","source_span","article","paragraph","item","subitem"],"properties":{"document_id":{"type":"string"},"chunk_id":{"type":"string"},"parent_id":{"type":["string","null"]},"chunk_type":{"enum":sorted(ALLOWED_TYPES)},"text":{"type":"string"},"source_path":{"type":"string"},"source_id":{"type":"string"},"source_chunk_id":{"type":"string"},"source_page":{"type":["integer","null"]},"source_span":{"type":["string","null"]},"article":{"type":["integer","null"]},"paragraph":{"type":["integer","null"]},"item":{"type":["integer","null"]},"subitem":{"type":["integer","null"]}}}
    (OUTPUT_DIR/"chunk_schema.json").write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUTPUT_DIR/"chunking_quality_log.jsonl").write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in log)+"\n",encoding="utf-8")
    samples=[x for x in chunks if x["chunk_type"] in {"article","case","guide","table"}][:50]
    docs=ROOT/"docs"; docs.mkdir(exist_ok=True)
    (docs/"chunking_validation.md").write_text("# 청킹 결과 검증\n\n"+f"- 생성 청크: {len(chunks)}개\n- 문서: {len(set(x['document_id'] for x in chunks))}개\n- 중복 chunk_id: {len(chunks)-len(ids)}개\n- 잘못된 참조: {len(invalid)}개\n- 대표 샘플: {len(samples)}개\n\n## 기준\n- document_id는 `data/document_registry.csv`의 값을 사용했습니다.\n- 구조화 법령·행정규칙을 우선하고 OCR 중복은 품질 로그에 기록했습니다.\n- 법령 ID는 `문서ID:A조:P항:I호:M목` 계층을 사용했습니다.\n- OCR은 페이지가 아닌 의미 단위로 분할하고 source_page/source_span을 기록했습니다.\n\n## 대표 샘플 원문 대조\n\n아래 샘플은 각 청크의 `text`가 `source_path`의 파싱 원문에서 추출된 텍스트이며, `source_span`/`source_page`로 역추적할 수 있습니다.\n\n"+"\n".join(f"- `{x['chunk_id']}` ({x['chunk_type']}): source `{x['source_path']}`, span `{x['source_span']}`" for x in samples)+"\n",encoding="utf-8")
    sample_lines=["# 대표 청크 원문 대조 결과", "", "| 번호 | chunk_id | 유형 | 위치 | 대조 결과 |", "|---:|---|---|---|---|"]
    for i, x in enumerate(samples, 1):
        # 파싱 원문 JSON 직렬화 안에 청크의 핵심 문구가 존재하는지 확인한다.
        raw = Path(ROOT / x["source_path"].removeprefix("data/")).read_text(encoding="utf-8", errors="ignore") if (ROOT / x["source_path"].removeprefix("data/")).exists() else ""
        probe = re.sub(r"\s+", "", x["text"][:80])
        raw_norm = re.sub(r"\s+", "", raw)
        result = "PASS" if probe and probe[:30] in raw_norm else "REVIEW"
        sample_lines.append(f"| {i} | `{x['chunk_id']}` | `{x['chunk_type']}` | `{x['source_span']}` / p.{x['source_page'] or '-'} | {result} |")
        sample_lines.append(f"\n> 원문 청크: {x['text'][:180].replace(chr(10), ' ')}")
    (docs/"chunking_samples_50.md").write_text("\n".join(sample_lines)+"\n",encoding="utf-8")

if __name__ == "__main__":
    run_pipeline()
    raise SystemExit(0)

# ---------- 포맷 3: OCR 세그멘터 (뼈대) ----------
HEADING = {
    "guide": re.compile(r"^(\s*[□■]|ㅇ|[Ⅰ-Ⅹ]\.|\d+\)|Q\.|A\.)"),
    "case":  re.compile(r"^(\s*\d+\s|사례|위반\s*(내용|표현)|판단|조치|근거)"),
    "law":   re.compile(r"^(제\d+조|\s*[①-⑮]|\s*\d+\.)"),
}
def is_cover_noise(lines):      # 세로쓰기/표지 휴리스틱
    short = sum(1 for l in lines if len(l.strip()) <= 1)
    return short >= 5

def chunk_ocr(d, doc_id, src, doc_kind="case"):
    chunks, log = [], {"document_id": doc_id, "skipped_pages": []}
    pat = HEADING[doc_kind]
    buf, cur_page, seg = [], None, 0
    for p in d["pages"]:
        if p["character_count"] < 10:
            log["skipped_pages"].append(p["page_number"]); continue
        lines = [l for l in p.get("lines", []) if not l.startswith("<img")]
        if is_cover_noise(lines):      # 표지 스킵
            log["skipped_pages"].append(p["page_number"]); continue
        for ln in lines:
            if pat.match(ln) and buf:        # 새 섹션 시작 → 직전 버퍼 flush
                seg += 1
                chunks.append(dict(chunk_id=f"{doc_id}_PG{pad(cur_page)}_S{pad(seg)}",
                                   document_id=doc_id, parent_id=None, chunk_type="case",
                                   article=None, paragraph=None, item=None, subitem=None,
                                   page=cur_page, source_path=src, source_url=None,
                                   text="\n".join(buf)))
                buf = []
            if not buf: cur_page = p["page_number"]
            buf.append(ln)
    # 마지막 버퍼 flush (생략)
    return chunks, log

# ---------- 드라이버 ----------
if __name__ == "__main__":
    out = open("structured_chunks.jsonl", "w", encoding="utf-8")
    for path in glob.glob("data_parsing/**/*.json", recursive=True):
        fmt, d = detect_format(path)
        doc_id = "DOC_" + os.path.splitext(os.path.basename(path))[0][:8]  # TODO: 메타데이터 담당과 ID 합의
        if   fmt == 1: rows = chunk_law(d, doc_id, path)
        elif fmt == 3: rows, _log = chunk_ocr(d, doc_id, path)
        else:          rows = []   # TODO: 포맷 2·4·5 매퍼
        for r in rows:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
    out.close()
