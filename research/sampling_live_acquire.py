#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

YEAR_FROM = 2000
YEAR_TO = 2025
VAM_SEARCH = "https://api.vam.ac.uk/v2/objects/search"
CC_EXPORT = "https://collections.craftscouncil.org.uk/csvexport?type=object"
VAM_CERAMICS_CATEGORY_ID = "THES48982"
VAM_CERAMICS_COLLECTION_ID = "THES48594"
MATERIAL_TERMS = ["ceramic", "porcelain", "bone china", "stoneware", "earthenware", "clay", "terracotta"]
CERAMIC_RE = re.compile(r"\b(ceramic|porcelain|bone\s+china|stoneware|earthenware|clay|terracotta)\b", re.I)
YEAR_RE = re.compile(r"(?<!\d)(1\d{3}|20\d{2}|2100)(?!\d)")

OUT = Path("sampling_run")
RAW_VAM = OUT / "raw" / "vam_search"
RAW_CC = OUT / "raw" / "crafts_council"
RAW_VAM.mkdir(parents=True, exist_ok=True)
RAW_CC.mkdir(parents=True, exist_ok=True)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get(session: requests.Session, url: str, *, params: dict[str, Any] | None = None, timeout: int = 60, retries: int = 5) -> requests.Response:
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, params=params, timeout=timeout, headers={"User-Agent": "ShangYu-PhD-sampling-audit/0.2"})
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(min(16, 2 ** attempt))
    raise RuntimeError(f"GET failed after {retries} attempts: {url}: {last!r}")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def vam_queries() -> list[tuple[str, dict[str, Any]]]:
    common = {"year_made_from": YEAR_FROM, "year_made_to": YEAR_TO, "page_size": 100}
    out = [
        ("category_ceramics", {**common, "id_category": VAM_CERAMICS_CATEGORY_ID}),
        ("ceramics_collection", {**common, "id_collection": VAM_CERAMICS_COLLECTION_ID}),
    ]
    out.extend((f"material_{t.replace(' ', '_')}", {**common, "q_material_technique": t}) for t in MATERIAL_TERMS)
    return out


def acquire_vam(session: requests.Session) -> dict[str, Any]:
    candidates: dict[str, dict[str, Any]] = {}
    sources: dict[str, set[str]] = defaultdict(set)
    qlog: list[dict[str, Any]] = []
    query_summary: list[dict[str, Any]] = []

    for label, base in vam_queries():
        page = 1
        pages = 1
        seen_this_query: set[str] = set()
        first_info: dict[str, Any] = {}
        while page <= pages:
            params = {**base, "page": page}
            r = get(session, VAM_SEARCH, params=params)
            data = r.json()
            info = data.get("info") or {}
            if page == 1:
                first_info = info
            pages = int(info.get("pages") or 1)
            records = data.get("records") or []
            raw_path = RAW_VAM / f"{label}_p{page:04d}.json"
            raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            qlog.append({
                "label": label,
                "page": page,
                "url": r.url,
                "record_count_reported": info.get("record_count", ""),
                "record_count_exact": info.get("record_count_exact", ""),
                "pages_reported": pages,
                "records_on_page": len(records),
                "captured_utc": now(),
                "raw_path": str(raw_path),
            })
            for rec in records:
                sn = str(rec.get("systemNumber") or "").strip()
                if not sn:
                    continue
                candidates.setdefault(sn, rec)
                sources[sn].add(label)
                seen_this_query.add(sn)
            page += 1
            time.sleep(0.08)
        query_summary.append({
            "label": label,
            "record_count_reported": first_info.get("record_count", ""),
            "record_count_exact": first_info.get("record_count_exact", ""),
            "pages": first_info.get("pages", ""),
            "unique_system_numbers_retrieved": len(seen_this_query),
        })

    summary_rows: list[dict[str, Any]] = []
    pattern_counts: Counter[str] = Counter()
    for sn in sorted(candidates):
        rec = candidates[sn]
        pm = rec.get("_primaryMaker") or {}
        labels = sorted(sources[sn])
        pattern = "; ".join(labels)
        pattern_counts[pattern] += 1
        summary_rows.append({
            "systemNumber": sn,
            "source_query": pattern,
            "source_query_count": len(labels),
            "accessionNumber": rec.get("accessionNumber", ""),
            "objectType": rec.get("objectType", ""),
            "_primaryTitle": rec.get("_primaryTitle", ""),
            "_primaryPlace": rec.get("_primaryPlace", ""),
            "_primaryMaker__name": pm.get("name", "") if isinstance(pm, dict) else "",
            "_primaryMaker__association": pm.get("association", "") if isinstance(pm, dict) else "",
            "_primaryDate": rec.get("_primaryDate", ""),
        })

    write_csv(OUT / "vam_query_log.csv", qlog, ["label", "page", "url", "record_count_reported", "record_count_exact", "pages_reported", "records_on_page", "captured_utc", "raw_path"])
    write_csv(OUT / "vam_query_summary.csv", query_summary, ["label", "record_count_reported", "record_count_exact", "pages", "unique_system_numbers_retrieved"])
    write_csv(OUT / "vam_candidate_union_search_summary.csv", summary_rows, ["systemNumber", "source_query", "source_query_count", "accessionNumber", "objectType", "_primaryTitle", "_primaryPlace", "_primaryMaker__name", "_primaryMaker__association", "_primaryDate"])
    pattern_rows = [{"source_pattern": k, "count": v} for k, v in pattern_counts.most_common()]
    write_csv(OUT / "vam_source_overlap_patterns.csv", pattern_rows, ["source_pattern", "count"])
    return {
        "ok": True,
        "candidate_union_count": len(candidates),
        "query_routes": len(query_summary),
        "query_pages_saved": len(qlog),
        "query_summary": query_summary,
        "top_source_overlap_patterns": pattern_rows[:20],
    }


def cc_date_screen(text: str) -> tuple[str, str, str, str]:
    years = [int(m.group(1)) for m in YEAR_RE.finditer(text or "")]
    if not years:
        return "", "", "unknown", "manual_review_no_year"
    lo, hi = min(years), max(years)
    overlap = lo <= YEAR_TO and hi >= YEAR_FROM
    if len(set(years)) == 1:
        decision = "likely_include" if overlap else "likely_exclude"
    else:
        decision = "manual_review_overlap" if overlap else "likely_exclude"
    return str(lo), str(hi), str(overlap).lower(), decision


def acquire_cc(session: requests.Session) -> dict[str, Any]:
    r = get(session, CC_EXPORT, timeout=120, retries=6)
    raw = r.content
    raw_path = RAW_CC / "all_objects.csv"
    raw_path.write_bytes(raw)
    text_head = raw[:1000].decode("utf-8", errors="replace")
    if "Collection" not in text_head or "Object number" not in text_head:
        raise RuntimeError(f"Crafts Council export did not look like the expected CSV. Content-Type={r.headers.get('content-type')!r}; head={text_head[:250]!r}")

    total = primary = cat_core = expansion = 0
    rows: list[dict[str, Any]] = []
    with raw_path.open("r", newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            collection = (row.get("Collection") or "").strip()
            if collection.casefold() != "primary collection":
                continue
            primary += 1
            category = (row.get("Category") or "").strip()
            mattech = (row.get("Materials and techniques") or "").strip()
            category_hit = "ceramic" in category.casefold()
            material_hit = bool(CERAMIC_RE.search(mattech))
            if not (category_hit or material_hit):
                continue
            if category_hit:
                cat_core += 1
                source_class = "institutional_category_core"
            else:
                expansion += 1
                source_class = "analytic_material_expansion"
            date_text = (row.get("Date") or "").strip()
            earliest, latest, overlap, date_screen = cc_date_screen(date_text)
            rows.append({
                "object_number": (row.get("Object number") or "").strip(),
                "source_class": source_class,
                "collection": collection,
                "category": category,
                "production_person": (row.get("Production person") or "").strip(),
                "production_organisation": (row.get("Production organisation") or "").strip(),
                "title": (row.get("Title") or "").strip(),
                "made_in": (row.get("Made in") or "").strip(),
                "date_text": date_text,
                "date_earliest_screen": earliest,
                "date_latest_screen": latest,
                "date_overlap_2000_2025_screen": overlap,
                "date_screen_decision": date_screen,
                "description": (row.get("Description") or "").strip(),
                "content": (row.get("Content") or "").strip(),
                "materials_and_techniques": mattech,
                "address": (row.get("Address") or "").strip(),
            })

    write_csv(OUT / "crafts_council_candidate_union_all_dates.csv", rows, ["object_number", "source_class", "collection", "category", "production_person", "production_organisation", "title", "made_in", "date_text", "date_earliest_screen", "date_latest_screen", "date_overlap_2000_2025_screen", "date_screen_decision", "description", "content", "materials_and_techniques", "address"])
    window_rows = [x for x in rows if x["date_overlap_2000_2025_screen"] == "true"]
    write_csv(OUT / "crafts_council_candidate_window_screen.csv", window_rows, ["object_number", "source_class", "collection", "category", "production_person", "production_organisation", "title", "made_in", "date_text", "date_earliest_screen", "date_latest_screen", "date_overlap_2000_2025_screen", "date_screen_decision", "description", "content", "materials_and_techniques", "address"])
    return {
        "ok": True,
        "source_url": r.url,
        "http_content_type": r.headers.get("content-type", ""),
        "rows_total": total,
        "primary_collection_rows": primary,
        "category_ceramics_candidates_all_dates": cat_core,
        "material_expansion_candidates_all_dates": expansion,
        "candidate_union_all_dates": len(rows),
        "candidate_window_screen_count": len(window_rows),
        "window_category_core_count": sum(x["source_class"] == "institutional_category_core" for x in window_rows),
        "window_material_expansion_count": sum(x["source_class"] == "analytic_material_expansion" for x in window_rows),
    }


def main() -> None:
    session = requests.Session()
    manifest: dict[str, Any] = {
        "started_utc": now(),
        "year_window": [YEAR_FROM, YEAR_TO],
        "status": {},
        "method_note": "Search hits and date screens are candidate-frame evidence only; final eligibility requires record-level/manual adjudication.",
    }
    for name, fn in [("vam", acquire_vam), ("crafts_council", acquire_cc)]:
        try:
            manifest["status"][name] = fn(session)
        except Exception as exc:
            manifest["status"][name] = {"ok": False, "error": repr(exc)}
    manifest["finished_utc"] = now()
    (OUT / "acquisition_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
