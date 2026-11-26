"""Compare the two corrected parsed sources with their original PDFs."""

import argparse
import csv
import json
from pathlib import Path
import re

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--law-pdf", required=True, type=Path)
    parser.add_argument("--guide-pdf", required=True, type=Path)
    args = parser.parse_args()
    with (ROOT / "data" / "document_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        registry = {row["document_id"]: row["source_path"] for row in csv.DictReader(handle)}
    law = json.loads((ROOT / registry["bb51bc2a5017baec"]).read_text(encoding="utf-8"))
    guide = json.loads((ROOT / registry["f32c7bd98edadb61"]).read_text(encoding="utf-8"))
    problems = []
    with pdfplumber.open(args.law_pdf) as pdf:
        if len(pdf.pages) != len(law["pages"]) or len(pdf.pages) != 4:
            problems.append("law page count mismatch")
        for page in law["pages"]:
            if any(re.search(r"법제처\s+\d+\s+국가법령정보센터", str(line)) for line in page["lines"]):
                problems.append(f"law footer remains on page {page['page_number']}")
    ratios = []
    with pdfplumber.open(args.guide_pdf) as pdf:
        if len(pdf.pages) != len(guide["pages"]) or len(pdf.pages) != 133:
            problems.append("guide page count mismatch")
        for source_page, pdf_page in zip(guide["pages"], pdf.pages):
            segments = source_page.get("column_segments", [])
            if not segments:
                continue
            reconstructed = []
            for segment in segments:
                cropped = pdf_page.crop(segment["bbox"])
                lines = [line.strip() for line in (cropped.extract_text(x_tolerance=2, y_tolerance=3) or "").splitlines()
                         if line.strip()]
                original = source_page["lines"][segment["first_line"]-1:segment["last_line"]]
                if lines != original:
                    problems.append(f"page {source_page['page_number']} {segment['role']} differs from PDF")
                reconstructed.extend(lines)
            if reconstructed != source_page["lines"]:
                problems.append(f"page {source_page['page_number']} segment coverage mismatch")
            pdf_chars = len(re.sub(r"\s+", "", pdf_page.extract_text() or ""))
            parsed_chars = len(re.sub(r"\s+", "", source_page["text"]))
            ratios.append((source_page["page_number"], parsed_chars / pdf_chars if pdf_chars else 0))
    if len(ratios) != 54 or min(value for _, value in ratios) < 0.97:
        problems.append("three-column page coverage below expected threshold")
    page104 = guide["pages"][103]
    roles = [segment["role"] for segment in page104["column_segments"]]
    if roles != ["law", "decree", "rule"]:
        problems.append("page 104 column order incorrect")
    result = {"law_footer_pages_clean": 4, "guide_column_pages": len(ratios),
              "minimum_pdf_text_retention": round(min(value for _, value in ratios), 4),
              "page_104_roles": roles, "problem_count": len(problems),
              "problems": problems[:20]}
    print(json.dumps(result, ensure_ascii=False))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
