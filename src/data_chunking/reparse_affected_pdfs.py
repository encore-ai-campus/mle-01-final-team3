"""Correct the two registered parsed PDFs using their original page layout."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
LAW_ID = "bb51bc2a5017baec"
GUIDE_ID = "f32c7bd98edadb61"
FOOTER = re.compile(r"^법제처\s+\d+\s+국가법령정보센터$")


def registry_paths():
    with (ROOT / "data" / "document_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {row["document_id"]: ROOT / row["source_path"] for row in csv.DictReader(handle)}


def corrected_law(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    removed = []
    for page in data["pages"]:
        kept = []
        for line in page["lines"]:
            if FOOTER.fullmatch(str(line).strip()):
                removed.append((page["page_number"], line))
            else:
                kept.append(line)
        page["lines"] = kept
        page["text"] = "\n".join(kept)
        page["character_count"] = len("".join(kept))
    already_corrected = data["document"].get("correction_note") == \
        "Removed repeating law.go.kr page footers after original PDF review"
    if not ((len(removed) == 4 and {page for page, _ in removed} == {1, 2, 3, 4}) or
            (not removed and already_corrected)):
        raise ValueError(f"Unexpected law footer pattern: {removed}")
    data["document"]["correction_note"] = "Removed repeating law.go.kr page footers after original PDF review"
    return data, {"footer_lines_removed": len(removed)}


def table_columns(page):
    vertical = [line for line in page.lines
                if abs(line["x0"] - line["x1"]) < 1]
    left = [line for line in vertical if 190 <= line["x0"] <= 215]
    right = [line for line in vertical if 330 <= line["x0"] <= 350]
    if not left or not right:
        return None
    if sum(line["height"] for line in left) < 0.3 * page.height or \
       sum(line["height"] for line in right) < 0.3 * page.height:
        return None
    first_x = sum(line["x0"] * line["height"] for line in left) / sum(line["height"] for line in left)
    second_x = sum(line["x0"] * line["height"] for line in right) / sum(line["height"] for line in right)
    top = min(line["top"] for line in [*left, *right])
    bottom = max(line["bottom"] for line in [*left, *right])
    if not (first_x < second_x and top < bottom):
        raise ValueError("Invalid column geometry")
    return first_x, second_x, top, bottom


def corrected_guide(path, pdf_path):
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = []
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) != len(data["pages"]):
            raise ValueError("Guide PDF and parsed JSON page counts differ")
        for source_page, pdf_page in zip(data["pages"], pdf.pages):
            page_no = source_page["page_number"]
            if page_no != pdf_page.page_number:
                raise ValueError(f"Page number mismatch: {page_no}")
            geometry = table_columns(pdf_page)
            if geometry is None:
                continue
            first_x, second_x, top, bottom = geometry
            boxes = [
                ("intro", (0, 0, pdf_page.width, top)),
                ("law", (0, top, first_x, bottom)),
                ("decree", (first_x, top, second_x, bottom)),
                ("rule", (second_x, top, pdf_page.width, bottom)),
            ]
            lines, segments = [], []
            for role, box in boxes:
                content = pdf_page.crop(box).extract_text(x_tolerance=2, y_tolerance=3) or ""
                section_lines = [line.strip() for line in content.splitlines() if line.strip()]
                if not section_lines:
                    continue
                first_line = len(lines) + 1
                lines.extend(section_lines)
                segments.append({"role": role, "first_line": first_line,
                                 "last_line": len(lines), "bbox": [round(x, 2) for x in box]})
            if not any(segment["role"] == "law" for segment in segments):
                raise ValueError(f"No text in law column on page {page_no}")
            source_page["lines"] = lines
            source_page["text"] = "\n".join(lines)
            source_page["character_count"] = len("".join(lines))
            source_page["column_segments"] = segments
            source_page["column_break_lines"] = [segment["first_line"] for segment in segments[1:]]
            changed.append(page_no)
    if len(changed) != 54 or 104 not in changed:
        raise ValueError(f"Unexpected three-column page set: {changed}")
    data["document"]["correction_note"] = "Three-column legal tables extracted left-to-right by original PDF coordinates"
    return data, {"three_column_pages_reparsed": len(changed), "page_numbers": changed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--law-pdf", required=True, type=Path)
    parser.add_argument("--guide-pdf", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    paths = registry_paths()
    with pdfplumber.open(args.law_pdf) as pdf:
        if len(pdf.pages) != 4:
            raise ValueError("Law PDF must have four pages")
        if not all("국가법령정보센터" in (page.extract_text() or "") for page in pdf.pages):
            raise ValueError("Law PDF footer could not be confirmed on every page")
    law, law_stats = corrected_law(paths[LAW_ID])
    guide, guide_stats = corrected_guide(paths[GUIDE_ID], args.guide_pdf)
    for data, path in ((law, paths[LAW_ID]), (guide, paths[GUIDE_ID])):
        encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if not args.dry_run:
            staged = path.with_suffix(path.suffix + ".reparsing")
            staged.write_bytes(encoded)
            os.replace(staged, path)
        print(json.dumps({"path": str(path), "bytes": len(encoded),
                          "sha256": hashlib.sha256(encoded).hexdigest(),
                          "dry_run": args.dry_run}, ensure_ascii=False))
    print(json.dumps({"law": law_stats, "guide": guide_stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
