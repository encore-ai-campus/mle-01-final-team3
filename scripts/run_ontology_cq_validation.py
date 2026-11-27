"""Execute separated Neo4j fixture and CQ Cypher files, then save query evidence."""
from __future__ import annotations

import csv
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from neo4j import GraphDatabase

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / ".env").exists())
DATA = ROOT / "data" / "ontology_validation"
QUERIES = ROOT / "queries" / "ontology_validation"
OUT = ROOT / "output" / "ontology_validation"
LAW_PATH = ROOT / "data" / "data_parsing" / "law" / "식품등의표시광고에관한법률_본문.json"


def read_cypher(name: str) -> str:
    return (QUERIES / name).read_text(encoding="utf-8")


def law_rows() -> tuple[dict, list[dict]]:
    law = json.loads(LAW_PATH.read_text(encoding="utf-8"))["법령"]
    mapping = json.loads((DATA / "law_violation_mapping.json").read_text(encoding="utf-8"))
    article = next(x for x in law["조문"]["조문단위"] if x.get("조문번호") == str(mapping["article"]) and "항" in x)
    paragraph = next(x for x in article["항"] if x.get("항번호") == "①")
    source_id = mapping["source_document_id"]
    source_path = mapping["source_path"]
    rows = []
    clauses = paragraph.get("호", [])
    for entry in mapping["items"]:
        index = entry["number"]
        if index < 1 or index > len(clauses):
            raise ValueError(f"Mapped law item is missing from source: {index}")
        clause = clauses[index - 1]
        text = clause.get("호내용", "").strip()
        rows.append({
            "provision": {"provision_id": f"LP-LAW-{mapping['article']}-{mapping['paragraph']}-{index}", "article": mapping["article"],
                          "paragraph": mapping["paragraph"], "item": index, "text": text,
                          "effective_from": law["기본정보"]["시행일자"], "data_status": "실제 법령 원문"},
            "violation": {"violation_code": entry["violation_code"], "name": entry["violation_name"],
                          "data_status": "법령 조문 의미를 요약한 분류"},
            "evidence": {"evidence_id": f"EV-LAW-8-1-{index}", "source_id": source_id,
                         "source_path": source_path, "locator": f"제{mapping['article']}조제{mapping['paragraph']}항제{index}호",
                         "source_span": f"조문 > 제{mapping['article']}조 > 제{mapping['paragraph']}항 > 제{index}호", "quote": text,
                         "review_status": "원문 JSON 대조", "assertion_type": "법령 규칙"},
        })
    meta = law["기본정보"]
    law_node = {"source_id": source_id, "title": meta["법령명_한글"], "document_type": "법률",
                "promulgation_no": f"법률 제{meta['공포번호']}호", "promulgated_at": meta["공포일자"],
                "effective_from": meta["시행일자"], "source_path": source_path, "data_status": "실제 법령 원문"}
    return {"source_id": source_id, "law": law_node, "rows": rows}, law


def encode_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return "" if value is None else str(value)


def execute() -> dict:
    cfg = {**dotenv_values(ROOT / ".env"), **os.environ}
    required = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
    missing = [key for key in required if not cfg.get(key)]
    if missing:
        raise SystemExit(f"Neo4j 환경변수 누락: {', '.join(missing)}")
    fixture = json.loads((DATA / "sample_fixture.json").read_text(encoding="utf-8"))
    legal_params, law = law_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    driver = GraphDatabase.driver(cfg["NEO4J_URI"], auth=(cfg["NEO4J_USER"], cfg["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            version = session.run(read_cypher("server_version.cypher")).single(strict=True)["version"]
            before = session.run(read_cypher("count_nodes.cypher")).single(strict=True)["node_count"]
            session.run(read_cypher("seed_legal.cypher"), legal_params).consume()
            sample_params = {"fixture_id": fixture["fixture_id"], "nodes": fixture["nodes"]}
            session.run(read_cypher("seed_fixture_migrate.cypher"), sample_params).consume()
            session.run(read_cypher("seed_fixture_nodes.cypher"), sample_params).consume()
            session.run(read_cypher("seed_fixture_cleanup.cypher"), {"fixture_id": fixture["fixture_id"]}).consume()
            node_by_key = {row["key"]: row for row in fixture["nodes"]}
            for legal_row in legal_params["rows"]:
                violation = legal_row["violation"]
                node_by_key[violation["violation_code"]] = {
                    "key": violation["violation_code"], "label": "ViolationType",
                    "id_key": "violation_code", "id": violation["violation_code"],
                }
            rels = []
            for rel in fixture["relationships"]:
                start, end = node_by_key[rel["from"]], node_by_key[rel["to"]]
                rels.append({"from": {"label": start["label"], "id_key": start["id_key"], "id": start["id"]},
                             "to": {"label": end["label"], "id_key": end["id_key"], "id": end["id"]},
                             "type": rel["type"], "properties": rel.get("properties", {})})
            session.run(read_cypher("seed_fixture_relationships.cypher"), {"relationships": rels}).consume()
            cq_meta = list(csv.DictReader((QUERIES / "cq_questions.csv").open(encoding="utf-8-sig", newline="")))
            results = []
            multihop_rows = [dict(record) for record in session.run(read_cypher("multihop_product_risk_law.cypher"))]
            for item in cq_meta:
                rows = [dict(record) for record in session.run(read_cypher(f"{item['cq_id'].lower().replace('-', '_')}.cypher"))]
                results.append({"cq_id": item["cq_id"], "question": item["question"], "row_count": len(rows),
                                "status": "PASS" if rows else "NO_DATA", "rows": rows,
                                "cypher": read_cypher(f"{item['cq_id'].lower().replace('-', '_')}.cypher").strip()})
            after_nodes = session.run(read_cypher("count_nodes.cypher")).single(strict=True)["node_count"]
            after_rels = session.run(read_cypher("count_relationships.cypher")).single(strict=True)["relationship_count"]
    finally:
        driver.close()
    report = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(), "neo4j_version": version,
        "nodes_before": before, "nodes_after": after_nodes, "relationships_after": after_rels,
        "fixture_id": fixture["fixture_id"], "fixture_warning": fixture["warning"],
        "source_document_id": legal_params["source_id"], "source_path": legal_params["law"]["source_path"],
        "source_title": legal_params["law"]["title"], "source_promulgation_no": legal_params["law"]["promulgation_no"],
        "source_effective_from": legal_params["law"]["effective_from"], "law_s_p_o_count": len(legal_params["rows"]),
        "cqs": results, "multihop_query": read_cypher("multihop_product_risk_law.cypher").strip(),
        "multihop_rows": multihop_rows,
        "limitations": [fixture["warning"],
                        "법령 S-P-O 5개는 저장소 법령 JSON의 제8조제1항제1호~제5호 원문이며, 현재 법령 여부를 별도 검증한 결과는 아닙니다.",
                        "가상 광고 표현의 위험 유형 연결은 테스트 추론이며 실제 위법 판단이 아닙니다.",
                        "어린이 기호식품 플래그는 테스트 값이며 실제 제품·법령 적용 검증이 아닙니다."],
    }
    (OUT / "cq_execution_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    with (OUT / "cq_execution_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cq_id", "question", "status", "row_count", "data_status"])
        writer.writeheader()
        for item in results:
            statuses = sorted({encode_value(row.get("데이터구분")) for row in item["rows"] if row.get("데이터구분")})
            writer.writerow({"cq_id": item["cq_id"], "question": item["question"], "status": item["status"], "row_count": item["row_count"], "data_status": "; ".join(statuses)})
    legal_rows = next(x["rows"] for x in results if x["cq_id"] == "CQ-07")
    with (OUT / "law_spo_triples.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(legal_rows[0]) if legal_rows else [])
        writer.writeheader(); writer.writerows(legal_rows)
    render_html(report, OUT / "cq_execution_report.html")
    render_graph(report, OUT / "ontology_cq_graph.svg")
    print(json.dumps({"neo4j_version": version, "nodes_before": before, "nodes_after": after_nodes,
                      "relationships_after": after_rels,
                      "cqs": [{"id": x["cq_id"], "status": x["status"], "rows": x["row_count"]} for x in results],
                      "output": str(OUT)}, ensure_ascii=False, indent=2))
    return report


def render_html(report: dict, target: Path) -> None:
    cards = []
    for item in report["cqs"]:
        headers = list(item["rows"][0]) if item["rows"] else []
        table = "<p>조회 결과 0행</p>" if not headers else "<table><thead><tr>" + "".join(f"<th>{html.escape(str(h))}</th>" for h in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{html.escape(encode_value(row.get(h)))}</td>" for h in headers) + "</tr>" for row in item["rows"]) + "</tbody></table>"
        cards.append(f"<section><h2>{html.escape(item['cq_id'])} · {html.escape(item['question'])}</h2><p>상태: {item['status']} · 반환 행: {item['row_count']}</p><details><summary>실행한 Cypher</summary><pre>{html.escape(item['cypher'])}</pre></details>{table}</section>")
    legal = next(x for x in report["cqs"] if x["cq_id"] == "CQ-07")
    headers = list(legal["rows"][0]) if legal["rows"] else []
    law_table = "<table><thead><tr>" + "".join(f"<th>{html.escape(str(h))}</th>" for h in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{html.escape(encode_value(row.get(h)))}</td>" for h in headers) + "</tr>" for row in legal["rows"]) + "</tbody></table>"
    limits = "".join(f"<li>{html.escape(x)}</li>" for x in report["limitations"])
    multi_headers = list(report["multihop_rows"][0]) if report["multihop_rows"] else []
    multi_table = "<p>조회 결과 0행</p>" if not multi_headers else "<table><thead><tr>" + "".join(f"<th>{html.escape(str(h))}</th>" for h in multi_headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{html.escape(encode_value(row.get(h)))}</td>" for h in multi_headers) + "</tr>" for row in report["multihop_rows"]) + "</tbody></table>"
    doc = f"""<!doctype html><html lang='ko'><meta charset='utf-8'><title>온톨로지 CQ 실행 검증</title>
    <style>body{{font:15px/1.55 'Malgun Gothic',sans-serif;color:#1d2939;margin:32px auto;max-width:1200px;padding:0 20px;background:#f7f9fc}}h1{{color:#163a5f}}section{{background:white;border:1px solid #d0d5dd;border-radius:10px;padding:18px;margin:18px 0}}table{{border-collapse:collapse;width:100%;margin-top:12px;background:white}}th,td{{border:1px solid #d0d5dd;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}th{{background:#eef4fa}}pre{{white-space:pre-wrap;background:#101828;color:#e6edf3;padding:14px;border-radius:8px;overflow:auto}}.notice{{background:#fff8e6;padding:14px;border-left:4px solid #e5a000}}img{{max-width:100%;height:auto}}</style>
    <h1>Neo4j 온톨로지 실행 결과</h1><p>Neo4j {html.escape(report['neo4j_version'])} · {html.escape(report['run_at_utc'])} · 노드 {report['nodes_after']} · 관계 {report['relationships_after']} · 법령 S-P-O {report['law_s_p_o_count']}개</p>
    <p class='notice'>{html.escape(report['fixture_warning'])}<br>법령 원문: {html.escape(report['source_title'])}, {html.escape(report['source_promulgation_no'])}, 시행일 {html.escape(report['source_effective_from'])}, 문서 ID {html.escape(report['source_document_id'])}</p>
    <h2>멀티홉 Cypher 실행 결과</h2><details><summary>실행한 Cypher</summary><pre>{html.escape(report['multihop_query'])}</pre></details>{multi_table}
    <h2>실행 그래프 개요</h2><img src='ontology_cq_graph.svg' alt='온톨로지 실행 그래프'><h2>실제 법령 S-P-O</h2>{law_table}<h2>CQ 실행 결과</h2>{''.join(cards)}<h2>해석 범위</h2><ul>{limits}</ul></html>"""
    target.write_text(doc, encoding="utf-8")


def render_graph(report: dict, target: Path) -> None:
    positions = {"광고(가상)":(110,130),"광고 표현(가상)":(340,130),"위반 유형":(600,130),"AI 판정(가상)":(860,130),"후속 업무(가상)":(1110,130),"제품(가상)":(110,340),"원재료(가상)":(340,340),"기능성 인정(가상)":(600,340),"허용 문구(가상)":(860,340),"법령 조항(실제)":(480,570),"Evidence(원문)":(760,570),"법령 문서(실제)":(1050,570)}
    edges = [("광고(가상)","광고 표현(가상)","HAS_CLAIM"),("광고 표현(가상)","위반 유형","INDICATES_RISK_OF"),("AI 판정(가상)","광고 표현(가상)","ANALYZES"),("AI 판정(가상)","후속 업무(가상)","GENERATES_TASK"),("제품(가상)","원재료(가상)","CONTAINS"),("원재료(가상)","기능성 인정(가상)","HAS_CLAIM"),("기능성 인정(가상)","허용 문구(가상)","ALLOWS"),("법령 조항(실제)","위반 유형","PROHIBITS"),("Evidence(원문)","법령 조항(실제)","EVIDENCE_FROM"),("법령 조항(실제)","법령 문서(실제)","PART_OF")]
    elements=["<svg xmlns='http://www.w3.org/2000/svg' width='1240' height='720' viewBox='0 0 1240 720'><defs><marker id='arrow' markerWidth='10' markerHeight='8' refX='8' refY='4' orient='auto'><path d='M0,0 L10,4 L0,8 z' fill='#667085'/></marker></defs><rect width='100%' height='100%' fill='white'/>","<text x='620' y='42' text-anchor='middle' font-size='24' font-family='sans-serif' font-weight='bold' fill='#163a5f'>Neo4j 실행 그래프 · CQ 경로 및 법령 S-P-O</text>"]
    for a,b,label in edges:
        x1,y1=positions[a]; x2,y2=positions[b]; dx=x2-x1; dy=y2-y1; length=max((dx*dx+dy*dy)**.5,1); sx=x1+dx/length*82; sy=y1+dy/length*30; ex=x2-dx/length*84; ey=y2-dy/length*30
        elements.append(f"<line x1='{sx}' y1='{sy}' x2='{ex}' y2='{ey}' stroke='#667085' stroke-width='2' marker-end='url(#arrow)'/><text x='{(sx+ex)/2}' y='{(sy+ey)/2-8}' text-anchor='middle' font-size='11' font-family='sans-serif' fill='#344054'>{html.escape(label)}</text>")
    for label,(x,y) in positions.items():
        color='#e8f5ed' if '실제' in label else '#fff4db'; elements.append(f"<rect x='{x-82}' y='{y-30}' width='164' height='60' rx='12' fill='{color}' stroke='#475467' stroke-width='2'/><text x='{x}' y='{y+6}' text-anchor='middle' font-size='13' font-family='sans-serif' font-weight='bold' fill='#1d2939'>{html.escape(label)}</text>")
    elements.append(f"<text x='32' y='670' font-size='13' font-family='sans-serif' fill='#475467'>Neo4j {html.escape(report['neo4j_version'])} · {report['nodes_after']} nodes · {report['relationships_after']} relationships · CQ 10개 실행</text><text x='1208' y='670' text-anchor='end' font-size='13' font-family='sans-serif' fill='#475467'>초록: 법령 원문 · 노랑: 가상 테스트</text></svg>")
    target.write_text("\n".join(elements), encoding="utf-8")


if __name__ == "__main__":
    execute()
