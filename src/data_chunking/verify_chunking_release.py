"""Verify OCR source coverage and catalog record ranges in a release."""

import collections
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "data_chunking" / "structured_chunks.jsonl"
SPAN = re.compile(r"^page (\d+), lines (\d+)-(\d+)$")


def main():
    ocr = collections.defaultdict(list)
    txt = collections.defaultdict(list)
    tables = collections.defaultdict(list)
    catalogs = collections.defaultdict(lambda: {"count": 0, "min": None, "max": 0})
    kinds = collections.Counter()
    with CHUNKS.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            kinds[row["chunk_type"]] += 1
            if row.get("source_page") is not None:
                (txt if row["source_path"].endswith(".txt") else ocr)[row["source_path"]].append(row)
            if "source_record_number" in row:
                item = catalogs[row["document_id"]]
                n = row["source_record_number"]
                item["count"] += 1
                item["min"] = n if item["min"] is None else min(item["min"], n)
                item["max"] = max(item["max"], n)
            if row["chunk_type"] == "table":
                tables[row["parent_id"] or row["chunk_id"]].append(row)
    problems = []
    page_stats = collections.Counter()
    for source_path, rows in ocr.items():
        source = json.loads((ROOT / source_path).read_text(encoding="utf-8"))
        pages = {page["page_number"]: page for page in source["pages"]}
        covered = collections.defaultdict(list)
        for row in rows:
            match = SPAN.match(row.get("source_span") or "")
            if not match:
                problems.append((row["chunk_id"], "bad source_span"))
                continue
            page_no, first, last = map(int, match.groups())
            if row["source_page"] != page_no or page_no not in pages:
                problems.append((row["chunk_id"], "bad source_page"))
                continue
            lines = pages[page_no]["lines"]
            selected = [(i, str(lines[i - 1])) for i in range(first, last + 1)
                        if str(lines[i - 1]).strip() and not str(lines[i - 1]).startswith("<img")]
            if row["text"] != "\n".join(text for _, text in selected):
                problems.append((row["chunk_id"], "text/source line mismatch"))
            segments = pages[page_no].get("column_segments", [])
            if segments and not any(first >= segment["first_line"] and
                                    last <= segment["last_line"] for segment in segments):
                problems.append((row["chunk_id"], "crosses legal-table columns"))
            if row["document_id"] == "bb51bc2a5017baec" and "국가법령정보센터" in row["text"]:
                problems.append((row["chunk_id"], "PDF footer remains in article text"))
            covered[page_no].extend(i for i, _ in selected)
        for page_no, page in pages.items():
            expected = [i for i, line in enumerate(page["lines"], 1)
                        if str(line).strip() and not str(line).startswith("<img")]
            if len("".join(str(page["lines"][i - 1]) for i in expected).strip()) < 10:
                page_stats["blank"] += 1
                continue
            page_stats["included"] += 1
            if sorted(covered[page_no]) != expected:
                problems.append((source_path, f"page {page_no} line coverage mismatch"))
    for doc, item in catalogs.items():
        if item["min"] != 1 or item["count"] != item["max"]:
            problems.append((doc, f"catalog range {item}"))
    for source_path, rows in txt.items():
        lines = (ROOT / source_path).read_text(encoding="utf-8").splitlines()
        expected = [(i, line) for i, line in enumerate(lines, 1)
                    if line.strip() and not re.match(r"^--- page \d+ ---$", line)]
        actual = []
        for row in rows:
            match = SPAN.match(row.get("source_span") or "")
            if not match:
                problems.append((row["chunk_id"], "bad TXT source_span"))
                continue
            page_no, first, last = map(int, match.groups())
            selected = [(i, lines[i - 1]) for i in range(first, last + 1)
                        if lines[i - 1].strip() and not re.match(r"^--- page \d+ ---$", lines[i - 1])]
            if page_no != row["source_page"] or row["text"] != "\n".join(line for _, line in selected):
                problems.append((row["chunk_id"], "TXT text/source line mismatch"))
            actual.extend(selected)
        if expected != actual:
            problems.append((source_path, "TXT line coverage mismatch"))
    for parent_id, rows in tables.items():
        parent = next((row for row in rows if row["chunk_id"] == parent_id), None)
        if not parent:
            problems.append((parent_id, "missing table parent"))
            continue
        source = json.loads((ROOT / parent["source_path"]).read_text(encoding="utf-8"))
        units = source["AdmRulService"]["별표"]["별표단위"]
        units = units if isinstance(units, list) else [units]
        number = int(parent_id.rsplit(":B", 1)[1])
        unit = units[number - 1]
        expected = [str(line) for group in unit["별표내용"]
                    for line in (group if isinstance(group, list) else [group])
                    if str(line).strip()]
        children = sorted((row for row in rows if row["chunk_id"] != parent_id),
                          key=lambda row: row["chunk_id"])
        actual = [line for row in children for line in row["text"].splitlines()]
        if expected != actual:
            problems.append((parent_id, "table source row coverage mismatch"))
    result = {"ocr_documents": len(ocr), "ocr_pages": dict(page_stats),
              "txt_documents": len(txt), "txt_chunks": sum(len(rows) for rows in txt.values()),
              "table_parents": len(tables),
              "catalog_ranges": dict(catalogs), "chunk_types": dict(kinds),
              "problem_count": len(problems), "problems": problems[:30]}
    print(json.dumps(result, ensure_ascii=False))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
