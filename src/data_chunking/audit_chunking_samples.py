"""Select representative chunks and compare them with parsed source data."""

import collections
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "data_chunking" / "structured_chunks.jsonl"
REPORT = ROOT / "docs" / "chunking_samples_50.md"
QUOTAS = {"article": 8, "paragraph": 8, "item": 8, "subitem": 4,
          "appendix": 4, "table": 2, "guide_ocr": 4, "guide_txt": 2,
          "case": 6, "record": 2, "record_food": 2}


def normalized(value):
    return re.sub(r"\s+", "", value)


def leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from leaves(item)


def compare(row, source):
    text = normalized(row["text"])
    if not text:
        return "FAIL", "empty chunk text"
    if isinstance(source, dict) and "pages" in source:
        pages = source["pages"]
        start = row.get("source_page")
        selected = [page for page in pages if start is None or page.get("page_number", 0) >= start]
        merged = "\n".join("\n".join(str(line) for line in page.get("lines", [])
                                     if not str(line).startswith("<img")) for page in selected)
        first = next((page for page in pages if page.get("page_number") == start), None)
        first_text = "\n".join(str(line) for line in first.get("lines", [])) if first else ""
        if text in normalized(merged) and text[:30] in normalized(first_text):
            return "PASS", "full text in OCR lines; start page matched"
        return "REVIEW", "OCR text or start page did not match exactly"
    if row["chunk_type"] in ("record", "case"):
        try:
            obj = json.loads(row["text"])
            if row.get("record_type") == "raw_material" and isinstance(source, dict):
                return ("PASS", "record object matches source JSONL line") if obj == source else (
                    "REVIEW", "record object differs from source JSONL line")
            arr = source if isinstance(source, list) else next(
                (value for value in source.values() if isinstance(value, list)), [])
            return ("PASS", "record object matches parsed source") if obj in arr else (
                "REVIEW", "record object not found in parsed source")
        except (ValueError, TypeError):
            pass
    if row["chunk_type"] in ("appendix", "table") and isinstance(source, dict):
        root = source.get("법령", source.get("AdmRulService", {}))
        annex = root.get("별표", {}).get("별표단위", [])
        units = annex if isinstance(annex, list) else [annex]
        for unit in units:
            if not isinstance(unit, dict):
                continue
            title = normalized(str(unit.get("별표제목", "")))
            content = normalized("\n".join(leaves(unit.get("별표내용", []))))
            if text == title + content or text == content:
                return "PASS", "full text matches annex title and content in source order"
            if row.get("table_role") == "row" and text in content:
                return "PASS", "table row matches consecutive annex source lines"
    if any(text == normalized(value) for value in leaves(source)):
        return "PASS", "full text matches one source field"
    if text in normalized("\n".join(leaves(source))):
        return "PASS", "full text matches consecutive source fields"
    return "REVIEW", "full text not found as one continuous source span"


def main():
    by_type = collections.defaultdict(lambda: collections.defaultdict(list))
    with CHUNKS.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if "record_type" in row and not row["source_path"].endswith("food_raw_material.jsonl"):
                break
            kind = row["chunk_type"]
            if kind == "guide":
                kind = "guide_txt" if row["source_path"].endswith(".txt") else "guide_ocr"
            elif kind == "record" and row["source_path"].endswith("food_raw_material.jsonl"):
                kind = "record_food"
            if kind in QUOTAS:
                by_type[kind][row["source_path"]].append(row)
    rng = random.Random(20261126)
    picked = []
    for kind, quota in QUOTAS.items():
        groups = list(by_type[kind].values())
        rng.shuffle(groups)
        chosen = []
        for group in groups:
            chosen.append(rng.choice(group))
            if len(chosen) == quota:
                break
        if len(chosen) < quota:
            remaining = [row for group in groups for row in group
                         if row["chunk_id"] not in {x["chunk_id"] for x in chosen}]
            chosen.extend(rng.sample(remaining, min(quota - len(chosen), len(remaining))))
        picked.extend(chosen)
    sources = {}
    results = []
    for row in picked:
        path = ROOT / row["source_path"]
        if path not in sources:
            if path.suffix == ".txt":
                sources[path] = path.read_text(encoding="utf-8").splitlines()
            elif path.suffix == ".jsonl":
                sources[path] = None
            else:
                sources[path] = json.loads(path.read_text(encoding="utf-8"))
        source_value = sources[path]
        if path.suffix == ".txt":
            match = re.match(r"^page \d+, lines (\d+)-(\d+)$", row["source_span"])
            source_value = "\n".join(source_value[int(match.group(1))-1:int(match.group(2))])
        elif path.suffix == ".jsonl":
            with path.open(encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    if number == row["source_record_number"]:
                        source_value = json.loads(line)
                        break
        status, reason = compare(row, source_value)
        results.append((row, status, reason))
    totals = collections.Counter(status for _, status, _ in results)
    lines = ["# 대표 청크 50건 원문 대조", "",
             "파싱 원본 JSON/TXT의 청크 문구와 위치를 비교했다. 두 PDF의 레이아웃 수정 결과는 별도 검증 문서에서 확인한다.", "",
             f"- PASS: {totals['PASS']}건",
             f"- REVIEW: {totals['REVIEW']}건",
             f"- FAIL: {totals['FAIL']}건", ""]
    for number, (row, status, reason) in enumerate(results, 1):
        excerpt = row["text"][:220].replace("\n", " ")
        lines.extend([f"## {number}. {row['chunk_type']} — {status}", "",
                      f"- chunk_id: `{row['chunk_id']}`",
                      f"- source_path: `{row['source_path']}`",
                      f"- source_page: `{row.get('source_page')}` / source_span: `{row.get('source_span')}`",
                      f"- 판정 근거: {reason}", f"> {excerpt}", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(dict(totals))


if __name__ == "__main__":
    main()
