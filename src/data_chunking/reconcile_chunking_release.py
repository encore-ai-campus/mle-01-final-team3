"""Reconcile a chunking JSONL release against the registry and source structure.

Reads and writes JSONL incrementally so catalog records do not fill memory.
"""

import argparse
import collections
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sqlite3

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "data" / "data_chunking"
POSITION = re.compile(r"^(.*:A\d+):P(\d+)$")
OCR_HEADING = re.compile(r"^(?:제\s*\d+\s*조|\d+[.)]\s+|[□■ㅇ]|사례\s*\d*|위반\s*(?:내용|표현)|판단|조치|근거|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.)")
ARTICLE_HEADING = re.compile(r"^제\s*(\d+)\s*조(?:의\d+)?\s*\(")
TXT_PAGE = re.compile(r"^--- page (\d+) ---$")
TXT_HEADING = re.compile(r"^\s*(?:[□■]|원료\s*개요|기능성\s*(?:내용|원료명)|일일\s*섭취량|섭취\s*시\s*주의사항|참고\s*내용|기본\s*정보|인정\s*정보|\d+[.)]\s*)")


def dump(row):
    return json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"


def rebuild_ocr(doc_id, source_path, case_document):
    """Keep every nonempty OCR page and emit traceable heading/length segments."""
    source = json.loads((REPO / source_path).read_text(encoding="utf-8"))
    rows, blank_pages = [], []
    serial = 0
    for page in source["pages"]:
        page_no = page["page_number"]
        lines = [(i + 1, str(line)) for i, line in enumerate(page.get("lines", []))
                 if not str(line).startswith("<img") and str(line).strip()]
        if len("".join(line for _, line in lines).strip()) < 10:
            blank_pages.append(page_no)
            continue
        segments = []
        current = []
        length = 0
        column_breaks = set(page.get("column_break_lines", []))
        for line_no, line in lines:
            is_heading = (ARTICLE_HEADING.match(line.strip()) if column_breaks
                          else OCR_HEADING.match(line.strip()))
            boundary = current and (line_no in column_breaks or
                                    is_heading or length + len(line) > 1500)
            if boundary:
                segments.append(current)
                current, length = [], 0
            current.append((line_no, line))
            length += len(line) + 1
        if current:
            segments.append(current)
        for segment in segments:
            serial += 1
            first_line, last_line = segment[0][0], segment[-1][0]
            text = "\n".join(line for _, line in segment)
            article = (ARTICLE_HEADING.match(text) if column_breaks
                       else re.match(r"^제\s*(\d+)\s*조", text))
            kind = "case" if case_document else ("article" if article else "guide")
            chunk_id = f"{doc_id}:PG{page_no:03d}:S{serial:04d}"
            rows.append({"document_id": doc_id, "chunk_id": chunk_id,
                         "parent_id": None, "chunk_type": kind, "text": text,
                         "source_path": source_path, "source_id": doc_id,
                         "source_chunk_id": chunk_id, "source_page": page_no,
                         "source_span": f"page {page_no}, lines {first_line}-{last_line}",
                         "article": int(article.group(1)) if article else None,
                         "paragraph": None, "item": None, "subitem": None})
    return rows, blank_pages


def chunk_txt_report(doc_id, source_path):
    """Split parsed raw-material reports at source headings and page lines."""
    lines = (REPO / source_path).read_text(encoding="utf-8").splitlines()
    rows, current, page_no, serial = [], [], 1, 0

    def flush():
        nonlocal current, serial
        if not current:
            return
        serial += 1
        chunk_id = f"{doc_id}:PG{page_no:03d}:S{serial:04d}"
        rows.append({"document_id": doc_id, "chunk_id": chunk_id,
                     "parent_id": None, "chunk_type": "guide",
                     "text": "\n".join(text for _, text in current),
                     "source_path": source_path, "source_id": doc_id,
                     "source_chunk_id": chunk_id, "source_page": page_no,
                     "source_span": f"page {page_no}, lines {current[0][0]}-{current[-1][0]}",
                     "article": None, "paragraph": None, "item": None, "subitem": None})
        current = []

    for line_no, line in enumerate(lines, 1):
        match = TXT_PAGE.match(line)
        if match:
            flush()
            page_no = int(match.group(1))
            continue
        if not line.strip():
            continue
        if current and (TXT_HEADING.match(line) or
                        sum(len(text) + 1 for _, text in current) + len(line) > 1500):
            flush()
        current.append((line_no, line))
    flush()
    return rows


def chunk_additional_law(doc_id, source_path):
    """Map a registered law API source omitted by title-based deduplication."""
    root = json.loads((REPO / source_path).read_text(encoding="utf-8"))["법령"]
    rows, occurrences = [], collections.Counter()

    def add(base, kind, value, parent, span, article=None, paragraph=None, item=None, subitem=None):
        content = str(value or "").strip()
        if not content:
            return None
        occurrences[base] += 1
        chunk_id = base if occurrences[base] == 1 else f"{base}:V{occurrences[base]:03d}"
        rows.append({"document_id": doc_id, "chunk_id": chunk_id,
                     "parent_id": parent, "chunk_type": kind, "text": content,
                     "source_path": source_path, "source_id": doc_id,
                     "source_chunk_id": chunk_id, "source_page": None,
                     "source_span": span, "article": article, "paragraph": paragraph,
                     "item": item, "subitem": subitem})
        return chunk_id

    articles = root.get("조문", {}).get("조문단위", [])
    if isinstance(articles, dict):
        articles = [articles]
    for sequence, article_obj in enumerate(articles, 1):
        article_no = int(re.search(r"\d+", str(article_obj.get("조문번호", sequence))).group())
        article_text = article_obj.get("조문내용", "")
        if not re.match(r"^\s*제\s*\d+\s*조", str(article_text)):
            add(f"{doc_id}:H{sequence:03d}", "guide", article_text, None,
                f"조문단위 {sequence} / 조문키 {article_obj.get('조문키', '')}")
            continue
        article_id = add(f"{doc_id}:A{article_no:03d}", "article", article_text, None,
                         f"제{article_no}조 / 조문키 {article_obj.get('조문키', '')}", article=article_no)
        raw_para = article_obj.get("항", [])
        if isinstance(raw_para, list):
            paragraphs, direct_items = raw_para, []
        elif isinstance(raw_para, dict) and "호" in raw_para and "항번호" not in raw_para:
            paragraphs, direct_items = [], raw_para["호"]
        elif isinstance(raw_para, dict):
            paragraphs, direct_items = raw_para.get("항단위", [raw_para]), []
        else:
            paragraphs, direct_items = [], []
        if isinstance(paragraphs, dict):
            paragraphs = [paragraphs]
        groups = [(None, article_id, direct_items)] if direct_items else []
        for para_no, paragraph_obj in enumerate(paragraphs, 1):
            para_text = paragraph_obj.get("항내용") or paragraph_obj.get("항번호", "")
            para_id = add(f"{article_id}:P{para_no:03d}", "paragraph", para_text,
                          article_id, f"제{article_no}조 제{para_no}항",
                          article=article_no, paragraph=para_no)
            items = paragraph_obj.get("호", [])
            groups.append((para_no if para_id else None, para_id or article_id, items))
        for para_no, parent_id, items in groups:
            if isinstance(items, dict):
                items = [items]
            for item_no, item_obj in enumerate(items or [], 1):
                item_text = item_obj.get("호내용") or item_obj.get("호번호", "")
                span = f"제{article_no}조" + (f" 제{para_no}항" if para_no else "") + f" 제{item_no}호"
                item_id = add(f"{parent_id}:I{item_no:03d}", "item", item_text,
                              parent_id, span, article=article_no,
                              paragraph=para_no, item=item_no)
                subs = item_obj.get("목", [])
                if isinstance(subs, dict):
                    subs = [subs]
                for sub_no, sub_obj in enumerate(subs or [], 1):
                    add(f"{item_id}:M{sub_no:03d}", "subitem",
                        sub_obj.get("목내용") or sub_obj.get("목번호", ""), item_id,
                        f"{span} {sub_obj.get('목번호', sub_no)}",
                        article=article_no, paragraph=para_no, item=item_no,
                        subitem=sub_no)
    annexes = root.get("별표", {}).get("별표단위", [])
    if isinstance(annexes, dict):
        annexes = [annexes]
    for number, annex in enumerate(annexes or [], 1):
        content = "\n".join(str(line) for group in annex.get("별표내용", [])
                            for line in (group if isinstance(group, list) else [group]))
        add(f"{doc_id}:B{number:03d}", "appendix",
            str(annex.get("별표제목", "")) + "\n" + content,
            None, f"별표 {number}")
    return rows


def rebuild_admin_table(row):
    """Preserve the complete annex and expose its source rows as children."""
    source = json.loads((REPO / row["source_path"]).read_text(encoding="utf-8"))
    units = source["AdmRulService"]["별표"]["별표단위"]
    units = units if isinstance(units, list) else [units]
    number = int(row["chunk_id"].rsplit(":B", 1)[1])
    unit = units[number - 1]
    all_lines = [str(line) for group in unit["별표내용"]
                 for line in (group if isinstance(group, list) else [group])]
    raw_lines = [(number, line) for number, line in enumerate(all_lines, 1) if line.strip()]
    title = str(unit.get("별표제목", "")).strip()
    row["text"] = (title + "\n" if title else "") + "\n".join(text for _, text in raw_lines)
    row["table_role"] = "parent"
    if not isinstance(units, list) or unit.get("별표번호") == "0000":
        row["source_span"] = "별표 (원본 별표번호 0000)"
    children, group = [], []

    def flush():
        nonlocal group
        if not group:
            return
        child = row.copy()
        child_id = f"{row['chunk_id']}:R{len(children) + 1:03d}"
        child["chunk_id"] = child["source_chunk_id"] = child_id
        child["parent_id"] = row["chunk_id"]
        child["text"] = "\n".join(text for _, text in group)
        child["source_span"] = f"{row['source_span']} / 원본 줄 {group[0][0]}-{group[-1][0]}"
        child["table_role"] = "row"
        children.append(child)
        group = []

    for line_no, line in raw_lines:
        starts_section = re.match(r"^\s*(?:\d+\.|[가나다라마바사아자차카타파하]\.)", line)
        separator = line.lstrip().startswith(("├", "┠", "┝", "└", "┗", "╞", "╟"))
        if group and (starts_section or separator or
                      sum(len(text) + 1 for _, text in group) + len(line) > 1500):
            flush()
        group.append((line_no, line))
    flush()
    return row, children


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    registry_path = REPO / "data" / "document_registry.csv"
    with registry_path.open(encoding="utf-8-sig", newline="") as handle:
        registry = {row["document_id"]: row for row in csv.DictReader(handle)}

    source = args.input.resolve()
    first_rows = []
    with source.open("rb") as handle:
        while True:
            line = handle.readline()
            if not line:
                break
            row = json.loads(line)
            if "record_type" in row:
                break
            first_rows.append(row)
    original_first_count = len(first_rows)
    present = {row["chunk_id"] for row in first_rows}
    missing = {row["parent_id"] for row in first_rows
               if row.get("parent_id") and row["parent_id"] not in present}
    if any(not POSITION.match(value) for value in missing):
        raise ValueError("Unexpected missing parent ID form")

    # Each missing P001 is an invented paragraph in an article whose source
    # stores items directly under the article. Verify that structure first.
    by_source = collections.defaultdict(list)
    for parent in missing:
        match = POSITION.match(parent)
        article_no = int(match.group(1).rsplit(":A", 1)[1])
        doc_id = parent.split(":", 1)[0]
        by_source[registry[doc_id]["source_path"]].append((parent, article_no))
    for source_path, entries in by_source.items():
        original = json.loads((REPO / source_path).read_text(encoding="utf-8"))
        articles = original.get("법령", {}).get("조문", {}).get("조문단위", [])
        for parent, article_no in entries:
            candidates = [article for article in articles
                          if str(article.get("조문번호")) == str(article_no)]
            direct = any(isinstance(article.get("항"), dict)
                         and "호" in article["항"]
                         and not any(key in article["항"]
                                     for key in ("항번호", "항내용", "항단위"))
                         for article in candidates)
            if not direct:
                raise ValueError(f"Missing parent is not a direct-item article: {parent}")

    id_map = {}
    changed = []
    for row in first_rows:
        old_id = row["chunk_id"]
        for parent in missing:
            prefix = parent + ":I"
            if old_id.startswith(prefix):
                article_id, para = POSITION.match(parent).groups()
                new_id = old_id.replace(prefix, article_id + ":I", 1)
                id_map[old_id] = new_id
                row["chunk_id"] = new_id
                row["source_chunk_id"] = new_id
                row["paragraph"] = None
                if isinstance(row.get("source_span"), str):
                    row["source_span"] = row["source_span"].replace(
                        f" 제{int(para)}항", "", 1)
                changed.append((old_id, new_id))
                break
    if len({row["chunk_id"] for row in first_rows}) != len(first_rows):
        raise ValueError("ID collision after parent repair")
    for row in first_rows:
        parent = row.get("parent_id")
        if parent in missing:
            row["parent_id"] = POSITION.match(parent).group(1)
        elif parent in id_map:
            row["parent_id"] = id_map[parent]
    present = {row["chunk_id"] for row in first_rows}
    unresolved = [row["chunk_id"] for row in first_rows
                  if row.get("parent_id") and row["parent_id"] not in present]
    if unresolved:
        raise ValueError(f"Unresolved parents: {unresolved[:5]}")

    # The prior OCR pass skipped content-bearing pages and joined text across
    # those gaps. Rebuild all OCR documents directly from their parsed pages.
    ocr_docs = {}
    for row in first_rows:
        if row.get("source_page") is not None:
            ocr_docs.setdefault(row["document_id"], row["source_path"])
    ocr_rebuilt = {}
    blank_ocr_pages = {}
    for doc_id, source_path in ocr_docs.items():
        old_types = collections.Counter(row["chunk_type"] for row in first_rows
                                        if row["document_id"] == doc_id)
        rows, blanks = rebuild_ocr(doc_id, source_path, old_types["case"] > old_types["guide"])
        ocr_rebuilt[doc_id] = rows
        blank_ocr_pages[doc_id] = blanks
    included_ocr = set()
    corrected_rows = []
    bad_table_doc = "DOC_표시·광고의 공정화에 관한 법"
    table_content = None
    for row in first_rows:
        doc_id = row["document_id"]
        if doc_id in ocr_rebuilt:
            if doc_id not in included_ocr:
                corrected_rows.extend(ocr_rebuilt[doc_id])
                included_ocr.add(doc_id)
            continue
        if doc_id == bad_table_doc and row["chunk_id"].rsplit(":", 1)[-1].startswith("B"):
            if table_content is None:
                annex = json.loads((REPO / row["source_path"]).read_text(encoding="utf-8"))[
                    "AdmRulService"]["별표"]["별표단위"]
                content = annex["별표내용"]
                table_content = "\n".join(str(line) for group in content for line in group if str(line).strip())
                row["text"] = table_content
                row["source_span"] = "별표 (원본 별표번호 0000)"
                corrected_rows.append(row)
            continue
        corrected_rows.append(row)
    with_table_rows = []
    table_child_count = 0
    for row in corrected_rows:
        if row["chunk_type"] == "table":
            parent, children = rebuild_admin_table(row)
            with_table_rows.extend([parent, *children])
            table_child_count += len(children)
        else:
            with_table_rows.append(row)
    corrected_rows = with_table_rows
    for doc_id in ("7721de8f3c4fa1a9", "ccb21ee852a2ed89", "4875117b2d645c67"):
        source_path = registry[doc_id]["source_path"]
        rows, blanks = rebuild_ocr(doc_id, source_path, False)
        ocr_rebuilt[doc_id] = rows
        blank_ocr_pages[doc_id] = blanks
        corrected_rows.extend(rows)
    additional_law_doc = "df71ee26b065bf5b"
    additional_law_rows = chunk_additional_law(
        additional_law_doc, registry[additional_law_doc]["source_path"])
    corrected_rows.extend(additional_law_rows)
    first_rows = corrected_rows
    present = {row["chunk_id"] for row in first_rows}
    txt_documents = {}
    txt_rows = []
    for doc_id, entry in registry.items():
        if entry["source_path"].endswith(".txt"):
            rows = chunk_txt_report(doc_id, entry["source_path"])
            if not rows:
                raise ValueError(f"Empty TXT report: {doc_id}")
            txt_documents[doc_id] = len(rows)
            txt_rows.extend(rows)
    food_doc = "3e85ebc3edc60881"
    food_source_path = registry[food_doc]["source_path"]
    food_count = 0

    def food_rows():
        nonlocal food_count
        with (REPO / food_source_path).open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ValueError(f"Blank food raw material line {number}")
                original = json.loads(line)
                chunk_id = f"{food_doc}:R{number:07d}"
                food_count += 1
                yield {"document_id": food_doc, "chunk_id": chunk_id,
                       "parent_id": None, "chunk_type": "record",
                       "text": json.dumps(original, ensure_ascii=False, separators=(",", ":")),
                       "source_path": food_source_path, "source_id": food_doc,
                       "source_chunk_id": chunk_id, "source_page": None,
                       "source_span": f"record {number}", "article": None,
                       "paragraph": None, "item": None, "subitem": None,
                       "record_type": "raw_material", "original_fields": original,
                       "source_record_number": number,
                       "record_id_semantics": "source_row_ordinal_no_stable_source_id",
                       "link_status": "unconfirmed_no_source_link_fields"}

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    schema["properties"]["record_type"]["enum"] = [
        "product", "product_with_raw_materials", "raw_material", "raw_material_metadata"
    ]
    schema["properties"]["text"]["minLength"] = 1
    schema["properties"]["text"]["pattern"] = r"\S"
    schema["properties"]["record_id_semantics"] = {"type": "string"}
    schema["properties"]["table_role"] = {"enum": ["parent", "row"]}
    (output / "chunk_schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    required = set(schema["required"])
    allowed_types = set(schema["properties"]["chunk_type"]["enum"])
    allowed_records = set(schema["properties"]["record_type"]["enum"])

    temp_output = output / "structured_chunks.rebuilding.jsonl"
    index = output / "chunk_ids.rebuilding.sqlite"
    if index.exists():
        index.unlink()
    db = sqlite3.connect(index)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")
    db.execute("CREATE TABLE chunks (id TEXT PRIMARY KEY, doc TEXT NOT NULL, parent TEXT) WITHOUT ROWID")
    counts = collections.Counter()
    type_counts = collections.Counter()
    document_counts = collections.Counter()
    documents = set()
    sha = hashlib.sha256()
    with source.open("rb") as incoming, temp_output.open("wb") as outgoing:
        for _ in range(original_first_count):
            incoming.readline()
        def remaining():
            for line in incoming:
                if not line.strip():
                    raise ValueError("Blank catalog input line")
                yield json.loads(line)
        for line_no, row in enumerate(itertools.chain(first_rows, txt_rows, food_rows(), remaining()), 1):
            absent = required - row.keys()
            if absent:
                raise ValueError(f"Missing fields at line {line_no}: {absent}")
            if row["document_id"] not in registry:
                raise ValueError(f"Unknown document at line {line_no}")
            if row["source_path"] != registry[row["document_id"]]["source_path"]:
                raise ValueError(f"Wrong source path at line {line_no}")
            if row["source_id"] != row["document_id"] or row["source_chunk_id"] != row["chunk_id"]:
                raise ValueError(f"Wrong source references at line {line_no}")
            if row["chunk_type"] not in allowed_types or not isinstance(row["text"], str) or not row["text"].strip():
                raise ValueError(f"Invalid type or empty text at line {line_no}")
            if "record_type" in row and row["record_type"] not in allowed_records:
                raise ValueError(f"Invalid record type at line {line_no}")
            try:
                db.execute("INSERT INTO chunks VALUES (?,?,?)", (row["chunk_id"], row["document_id"], row["parent_id"]))
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"Duplicate chunk ID at line {line_no}: {row['chunk_id']}") from exc
            encoded = dump(row).encode("utf-8")
            outgoing.write(encoded)
            sha.update(encoded)
            counts["chunks"] += 1
            type_counts[row["chunk_type"]] += 1
            documents.add(row["document_id"])
            document_counts[row["document_id"]] += 1
            if line_no % 200000 == 0:
                db.commit()
                print(f"Processed {line_no:,} chunks", flush=True)
    db.commit()
    orphans = db.execute("SELECT COUNT(*) FROM chunks c LEFT JOIN chunks p ON p.id=c.parent "
                         "WHERE c.parent IS NOT NULL AND (p.id IS NULL OR p.doc<>c.doc)").fetchone()[0]
    db.close()
    index.unlink()
    if orphans:
        raise ValueError(f"Parent references still invalid: {orphans}")
    os.replace(temp_output, output / "structured_chunks.jsonl")

    source_events = [json.loads(line) for line in args.log.read_text(encoding="utf-8").splitlines() if line]
    events = [event for event in source_events
              if event.get("event") != "validation_summary"
              and event.get("event") not in ("skipped_page", "document_processed")
              and not (event.get("event") == "duplicate_chunk_id_resolved"
                       and id_map.get(event.get("chunk_id"), event.get("chunk_id")) not in present)
              and not (event.get("event") == "source_excluded"
                       and event.get("document_id") in documents)]
    events = [event for event in events
              if not (event.get("event") == "duplicate_excluded"
                      and event.get("document_id") in documents)]
    for event in events:
        if event.get("chunk_id") in id_map:
            event["chunk_id"] = id_map[event["chunk_id"]]
    logged = {event.get("document_id") for event in events if event.get("event") == "catalog_processed"}
    for doc_id in sorted(documents - logged):
        events.append({"event": "document_included", "document_id": doc_id,
                       "chunk_count": document_counts[doc_id],
                       "source_path": registry[doc_id]["source_path"]})
    for doc_id, pages in blank_ocr_pages.items():
        for page in pages:
            events.append({"event": "blank_ocr_page", "document_id": doc_id,
                           "source_page": page, "reason": "less_than_10_text_characters"})
    for doc_id, rows in ocr_rebuilt.items():
        events.append({"event": "ocr_rebuilt_from_parsed_pages", "document_id": doc_id,
                       "chunk_count": len(rows)})
    events.append({"event": "malformed_table_replaced", "document_id": bad_table_doc,
                   "old_chunk_count": 10, "new_chunk_count": 1})
    events.append({"event": "admin_table_rows_rebuilt", "parent_table_count": 3,
                   "child_row_count": table_child_count})
    events.append({"event": "catalog_generated_from_jsonl", "document_id": food_doc,
                   "chunk_count": food_count, "source_path": food_source_path})
    for doc_id, chunk_count in txt_documents.items():
        events.append({"event": "txt_report_chunked", "document_id": doc_id,
                       "chunk_count": chunk_count,
                       "source_path": registry[doc_id]["source_path"]})
    events.append({"event": "law_added_from_registered_source",
                   "document_id": additional_law_doc,
                   "chunk_count": len(additional_law_rows),
                   "source_path": registry[additional_law_doc]["source_path"]})
    for doc_id, correction, scope in (
        ("bb51bc2a5017baec", "repeated_page_footer_removed", 4),
        ("f32c7bd98edadb61", "three_column_pages_reparsed", 54),
    ):
        source_path = REPO / registry[doc_id]["source_path"]
        events.append({"event": "pdf_source_reparsed", "document_id": doc_id,
                       "correction": correction, "affected_page_count": scope,
                       "source_path": registry[doc_id]["source_path"],
                       "parsed_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest()})
    for doc_id in sorted(set(registry) - documents):
        source_path = registry[doc_id]["source_path"]
        events.append({"event": "registry_source_not_in_release", "document_id": doc_id,
                       "source_path": source_path,
                       "reason": "text_report_scope_unconfirmed" if source_path.endswith(".txt")
                       else "selection_or_duplicate_status_unconfirmed"})
    for old, new in changed:
        events.append({"event": "id_rewritten_from_source_structure", "old_chunk_id": old,
                       "chunk_id": new, "reason": "item_directly_under_article"})
    events.append({"event": "validation_summary", "chunk_count": counts["chunks"],
                   "document_count": len(documents), "duplicate_chunk_id_count": 0,
                   "invalid_reference_count": 0, "empty_text_count": 0,
                   "chunk_type_counts": dict(type_counts),
                   "id_rewritten_count": len(changed)})
    (output / "chunking_quality_log.jsonl").write_text(
        "".join(dump(event) for event in events), encoding="utf-8")
    manifest = {"dataset_name": "structured_chunks", "data_version": "2026-11-26-pdf-layout-repair",
                "schema_version": "2026-11-26-reconciled", "record_count": counts["chunks"],
                "document_count": len(documents),
                "file_size_bytes": (output / "structured_chunks.jsonl").stat().st_size,
                "sha256": sha.hexdigest(),
                "local_path": "data/data_chunking/structured_chunks.jsonl",
                "storage_uri": None,
                "reparsed_sources_sha256": {
                    doc_id: hashlib.sha256((REPO / registry[doc_id]["source_path"]).read_bytes()).hexdigest()
                    for doc_id in ("bb51bc2a5017baec", "f32c7bd98edadb61")},
                "source_file": source.name}
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"chunks": counts["chunks"], "documents": len(documents),
                      "rewritten_ids": len(changed), "orphans": orphans,
                      "sha256": sha.hexdigest()}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
