"""Historical Question Bank import parsers (bulk text, CSV, JSON) and export helpers."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Dict, List, Optional

from .historical_analyser import classify_question_text
from .schemas import BulkParseResponse, HistoricalQuestionRecord, ParsedQuestionDraft
from .taxonomy import CATEGORIES, PROGRAMME_TAGS


def _parse_optional_int(val: Any, min_val: int, max_val: int) -> Optional[int]:
    if val is None:
        return None
    text = str(val).strip()
    if not text or text.lower() in {"unknown", "n/a", "na", "none", "-", "null"}:
        return None
    m = re.search(r"\d+", text)
    if not m:
        return None
    num = int(m.group(0))
    if min_val <= num <= max_val:
        return num
    return None


def _parse_list_field(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    text = str(val).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r"[;|,]", text) if part.strip()]


def _match_category(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    lookup = {c.lower(): c for c in CATEGORIES}
    return lookup.get(raw.strip().lower())


def _normalize_programmes(items: List[str]) -> List[str]:
    lookup = {p.lower(): p for p in PROGRAMME_TAGS}
    out: List[str] = []
    for item in items:
        matched = lookup.get(item.strip().lower())
        if matched and matched not in out:
            out.append(matched)
    return out


def _build_draft(
    prompt_text: str,
    title: Optional[str] = None,
    year: Optional[int] = None,
    raw_category: Optional[str] = None,
    programme_tags: Optional[List[str]] = None,
    archetypes: Optional[List[str]] = None,
    competencies: Optional[List[str]] = None,
    themes: Optional[List[str]] = None,
    marks: Optional[int] = None,
    time_minutes: Optional[int] = None,
    source: Optional[str] = None,
    notes: Optional[str] = None,
) -> ParsedQuestionDraft:
    explicit_cat = _match_category(raw_category)
    cls = classify_question_text(prompt_text, explicit_category=explicit_cat)

    progs = _normalize_programmes(programme_tags or [])
    if not progs:
        progs = cls["programme_tags"]

    clean_title = title.strip() if title and title.strip() else prompt_text.strip().splitlines()[0][:88]

    return ParsedQuestionDraft(
        title=clean_title,
        prompt_text=prompt_text.strip(),
        year=year,
        category=cls["category"],
        programme_tags=progs,
        archetypes=archetypes if archetypes else cls["archetypes"],
        competencies=competencies if competencies else cls["competencies"],
        themes=themes if themes else cls["themes"],
        marks=marks,
        time_minutes=time_minutes,
        source=source.strip() if source and source.strip() else None,
        notes=notes.strip() if notes and notes.strip() else None,
        auto_assigned_category=cls["auto_assigned_category"],
        confidence_note=cls["confidence_note"],
    )


def parse_bulk_text(content: str, default_source: Optional[str] = None) -> BulkParseResponse:
    """Split multi-prompt plain text (separated by blank lines or '---' or numbered blocks)."""
    drafts: List[ParsedQuestionDraft] = []
    errors: List[str] = []

    raw_blocks = re.split(r"\n\s*---\s*\n|\n{2,}", content.strip())
    for idx, block in enumerate(raw_blocks, start=1):
        text = block.strip()
        if not text:
            continue
        # Remove leading numbering like "1. " or "Q1:"
        text = re.sub(r"^(?:Q?\d+[\.\):]\s*)", "", text, flags=re.IGNORECASE).strip()
        if len(text) < 10:
            errors.append(f"Block {idx} skipped: too short (minimum 10 characters).")
            continue

        # Extract optional inline metadata tags like [2023], [Category: Storyboard], [Marks: 20], [Time: 30]
        year = None
        ym = re.search(r"\[(?:year\s*:\s*)?(19\d{2}|20[0-2]\d)\]", text, flags=re.IGNORECASE)
        if ym:
            year = int(ym.group(1))
            text = text.replace(ym.group(0), "").strip()

        raw_cat = None
        cm = re.search(r"\[category\s*:\s*([^\]]+)\]", text, flags=re.IGNORECASE)
        if cm:
            raw_cat = cm.group(1).strip()
            text = text.replace(cm.group(0), "").strip()

        marks = None
        mm = re.search(r"\[marks\s*:\s*(\d+)\]", text, flags=re.IGNORECASE)
        if mm:
            marks = _parse_optional_int(mm.group(1), 1, 200)
            text = text.replace(mm.group(0), "").strip()

        time_min = None
        tm = re.search(r"\[time\s*:\s*(\d+)\s*(?:min|mins|minutes)?\]", text, flags=re.IGNORECASE)
        if tm:
            time_min = _parse_optional_int(tm.group(1), 5, 240)
            text = text.replace(tm.group(0), "").strip()

        drafts.append(
            _build_draft(
                prompt_text=text,
                year=year,
                raw_category=raw_cat,
                marks=marks,
                time_minutes=time_min,
                source=default_source,
            )
        )

    return BulkParseResponse(drafts=drafts, errors=errors)


def parse_csv_import(content: str, default_source: Optional[str] = None) -> BulkParseResponse:
    drafts: List[ParsedQuestionDraft] = []
    errors: List[str] = []

    reader = csv.DictReader(io.StringIO(content.strip()))
    if not reader.fieldnames:
        return BulkParseResponse(drafts=[], errors=["CSV header row is missing."])

    for row_num, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items() if k}
        prompt = (
            row.get("prompt_text")
            or row.get("question")
            or row.get("prompt")
            or row.get("text")
            or ""
        )
        if len(prompt) < 10:
            errors.append(f"Row {row_num} skipped: missing or too-short 'prompt_text' / 'question' column.")
            continue

        drafts.append(
            _build_draft(
                prompt_text=prompt,
                title=row.get("title") or None,
                year=_parse_optional_int(row.get("year"), 1980, 2030),
                raw_category=row.get("category") or None,
                programme_tags=_parse_list_field(row.get("programme_tags") or row.get("programmes") or row.get("programme")),
                archetypes=_parse_list_field(row.get("archetypes")),
                competencies=_parse_list_field(row.get("competencies")),
                themes=_parse_list_field(row.get("themes")),
                marks=_parse_optional_int(row.get("marks"), 1, 200),
                time_minutes=_parse_optional_int(row.get("time_minutes") or row.get("time"), 5, 240),
                source=row.get("source") or default_source,
                notes=row.get("notes") or None,
            )
        )

    return BulkParseResponse(drafts=drafts, errors=errors)


def parse_json_import(content: str, default_source: Optional[str] = None) -> BulkParseResponse:
    drafts: List[ParsedQuestionDraft] = []
    errors: List[str] = []

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return BulkParseResponse(drafts=[], errors=[f"Invalid JSON syntax: {exc}"])

    if isinstance(parsed, dict):
        items = parsed.get("questions") or parsed.get("items") or [parsed]
    elif isinstance(parsed, list):
        items = parsed
    else:
        return BulkParseResponse(drafts=[], errors=["JSON must be an array of question objects or {\"questions\": [...] }."])

    for idx, obj in enumerate(items, start=1):
        if not isinstance(obj, dict):
            errors.append(f"Entry {idx} skipped: expected a JSON object.")
            continue
        prompt = str(obj.get("prompt_text") or obj.get("question") or obj.get("prompt") or "").strip()
        if len(prompt) < 10:
            errors.append(f"Entry {idx} skipped: missing or too-short 'prompt_text' / 'question'.")
            continue

        drafts.append(
            _build_draft(
                prompt_text=prompt,
                title=obj.get("title"),
                year=_parse_optional_int(obj.get("year"), 1980, 2030),
                raw_category=obj.get("category"),
                programme_tags=_parse_list_field(obj.get("programme_tags") or obj.get("programmes") or obj.get("programme")),
                archetypes=_parse_list_field(obj.get("archetypes")),
                competencies=_parse_list_field(obj.get("competencies")),
                themes=_parse_list_field(obj.get("themes")),
                marks=_parse_optional_int(obj.get("marks"), 1, 200),
                time_minutes=_parse_optional_int(obj.get("time_minutes") or obj.get("time"), 5, 240),
                source=obj.get("source") or default_source,
                notes=obj.get("notes"),
            )
        )

    return BulkParseResponse(drafts=drafts, errors=errors)


def export_historical_to_csv(records: List[HistoricalQuestionRecord]) -> str:
    buf = io.StringIO()
    fieldnames = [
        "title",
        "prompt_text",
        "year",
        "category",
        "programme_tags",
        "archetypes",
        "competencies",
        "marks",
        "time_minutes",
        "source",
        "notes",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow(
            {
                "title": r.title or "",
                "prompt_text": r.prompt_text,
                "year": "" if r.year is None else r.year,
                "category": r.category,
                "programme_tags": "; ".join(r.programme_tags),
                "archetypes": "; ".join(r.archetypes),
                "competencies": "; ".join(r.competencies),
                "marks": "" if r.marks is None else r.marks,
                "time_minutes": "" if r.time_minutes is None else r.time_minutes,
                "source": r.source or "",
                "notes": r.notes or "",
            }
        )
    return buf.getvalue()
