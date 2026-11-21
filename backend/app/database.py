"""SQLite database initialization and persistence operations for DAT Practice Lab."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .schemas import (
    AppSettings,
    ExamPaperRecord,
    HistoricalQuestionCreate,
    HistoricalQuestionRecord,
    HistoricalQuestionUpdate,
    PracticeAttemptCreate,
    PracticeAttemptRecord,
    PracticeAttemptUpdate,
    StoredGeneratedQuestion,
    VisualLearningCreate,
    VisualLearningRecord,
    WeakAreaCreate,
    WeakAreaRecord,
)


def _get_env_gemini_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    for p in [Path(__file__).resolve().parents[1] / ".env", Path(__file__).resolve().parents[2] / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _default_db_path() -> Path:
    env_path = os.environ.get("DAT_LAB_DB_PATH")
    if env_path:
        return Path(env_path)
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    for root in [repo_root, backend_root]:
        candidate = root / "data" / "dat_practice_lab.db"
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate

    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "dat_practice_lab.db"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Thin, synchronous SQLite repository with strict schema management."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else _default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS historical_questions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    prompt_text TEXT NOT NULL,
                    year INTEGER,
                    category TEXT NOT NULL,
                    programme_tags TEXT NOT NULL DEFAULT '[]',
                    archetypes TEXT NOT NULL DEFAULT '[]',
                    competencies TEXT NOT NULL DEFAULT '[]',
                    themes TEXT NOT NULL DEFAULT '[]',
                    marks INTEGER,
                    time_minutes INTEGER,
                    source TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS exam_papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    num_questions INTEGER NOT NULL,
                    total_time_minutes INTEGER NOT NULL,
                    difficulty TEXT NOT NULL,
                    paper_strategy TEXT NOT NULL,
                    historical_relevance TEXT NOT NULL,
                    programme_focus TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'not_started',
                    elapsed_seconds INTEGER NOT NULL DEFAULT 0,
                    warnings TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS generated_questions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    programme_tags TEXT NOT NULL,
                    archetypes TEXT NOT NULL,
                    competencies TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    time_minutes INTEGER NOT NULL,
                    total_marks INTEGER NOT NULL,
                    scenario TEXT NOT NULL,
                    subquestions TEXT NOT NULL,
                    constraints TEXT NOT NULL,
                    sketching_requirements TEXT NOT NULL,
                    visual_sketch_prompt TEXT NOT NULL DEFAULT '',
                    visual_negative_prompt TEXT NOT NULL DEFAULT '',
                    evaluation_rubric TEXT NOT NULL,
                    practice_priority INTEGER NOT NULL,
                    priority_reason TEXT NOT NULL,
                    prediction_confidence TEXT NOT NULL,
                    historical_pattern_references TEXT NOT NULL,
                    suggested_time_split TEXT NOT NULL,
                    generation_mode TEXT NOT NULL,
                    exam_paper_id TEXT,
                    question_order INTEGER NOT NULL DEFAULT 1,
                    is_saved INTEGER NOT NULL DEFAULT 0,
                    model_used TEXT NOT NULL DEFAULT '',
                    provider_used TEXT NOT NULL DEFAULT '',
                    practice_priority_score REAL NOT NULL DEFAULT 0.0,
                    historical_evidence TEXT NOT NULL DEFAULT '[]',
                    model_interpretation TEXT NOT NULL DEFAULT '',
                    low_confidence_warning TEXT,
                    raw_llm_response TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (exam_paper_id) REFERENCES exam_papers(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS practice_attempts (
                    id TEXT PRIMARY KEY,
                    question_id TEXT,
                    question_title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    programme_tags TEXT NOT NULL DEFAULT '[]',
                    exam_paper_id TEXT,
                    time_allocated_minutes INTEGER NOT NULL DEFAULT 30,
                    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
                    self_difficulty TEXT,
                    status TEXT NOT NULL DEFAULT 'completed',
                    notes TEXT NOT NULL DEFAULT '',
                    rubric_revealed INTEGER NOT NULL DEFAULT 0,
                    attempted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS weak_areas (
                    id TEXT PRIMARY KEY,
                    area_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS visual_learning_memory (
                    id TEXT PRIMARY KEY,
                    question_id TEXT,
                    question_title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    archetype TEXT NOT NULL DEFAULT '',
                    older_prompt TEXT NOT NULL DEFAULT '',
                    older_image_url TEXT NOT NULL DEFAULT '',
                    uploaded_image_url TEXT NOT NULL DEFAULT '',
                    new_image_url TEXT NOT NULL DEFAULT '',
                    what_changed TEXT NOT NULL,
                    why_changed TEXT NOT NULL,
                    actionable_guidelines TEXT NOT NULL,
                    negative_guidelines TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_visual_learning_cat ON visual_learning_memory(category);
                """
            )
            # Safe additive migration for existing SQLite databases
            cols = {
                r["name"] for r in conn.execute("PRAGMA table_info(generated_questions)").fetchall()
            }
            if "visual_sketch_prompt" not in cols:
                conn.execute(
                    "ALTER TABLE generated_questions ADD COLUMN visual_sketch_prompt TEXT NOT NULL DEFAULT ''"
                )
            if "visual_negative_prompt" not in cols:
                conn.execute(
                    "ALTER TABLE generated_questions ADD COLUMN visual_negative_prompt TEXT NOT NULL DEFAULT ''"
                )

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_settings(self) -> AppSettings:
        with self.connect() as conn:
            row = conn.execute("SELECT payload FROM settings WHERE id = 1").fetchone()
            if not row:
                default = AppSettings()
                self.save_settings(default)
                return default
            data = json.loads(row["payload"])
            st = AppSettings.model_validate(data)
            env_gemini_key = _get_env_gemini_key()
            if env_gemini_key and not st.gemini_api_key:
                st.gemini_api_key = env_gemini_key
            st.has_gemini_key = bool(st.gemini_api_key)
            st.has_groq_key = bool(st.groq_api_key)
            st.has_custom_key = bool(st.custom_api_key)
            st.has_openai_key = bool(st.openai_api_key)
            return st

    def save_settings(self, settings: AppSettings) -> AppSettings:
        now = utc_now_iso()
        # Retrieve existing settings to preserve secret keys if incoming keys are masked or omitted
        try:
            existing = self.get_settings()
        except Exception:
            existing = None

        if existing:
            secret_fields = ["gemini_api_key", "groq_api_key", "custom_api_key", "openai_api_key"]
            for field in secret_fields:
                incoming_val = getattr(settings, field, "") or ""
                existing_val = getattr(existing, field, "") or ""
                # If incoming is masked ("••••...") or blank while existing has a key, preserve existing
                if incoming_val.startswith("••••") or (not incoming_val and existing_val):
                    setattr(settings, field, existing_val)

            # Preserve working model & token safety if incoming is blank or dangerously low
            if not settings.model and existing.model:
                settings.model = existing.model
            if settings.max_tokens < 1500 and existing.max_tokens >= 1500:
                settings.max_tokens = existing.max_tokens

        settings.has_gemini_key = bool(settings.gemini_api_key)
        settings.has_groq_key = bool(settings.groq_api_key)
        settings.has_custom_key = bool(settings.custom_api_key)
        settings.has_openai_key = bool(settings.openai_api_key)

        payload = settings.model_dump_json()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (id, payload, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET payload = excluded.payload, updated_at = excluded.updated_at
                """,
                (payload, now),
            )
        return settings

    # ------------------------------------------------------------------
    # Historical Questions
    # ------------------------------------------------------------------

    def _row_to_historical(self, row: sqlite3.Row) -> HistoricalQuestionRecord:
        return HistoricalQuestionRecord(
            id=row["id"],
            title=row["title"],
            prompt_text=row["prompt_text"],
            year=row["year"],
            category=row["category"],
            programme_tags=json.loads(row["programme_tags"] or "[]"),
            archetypes=json.loads(row["archetypes"] or "[]"),
            competencies=json.loads(row["competencies"] or "[]"),
            themes=json.loads(row["themes"] or "[]"),
            marks=row["marks"],
            time_minutes=row["time_minutes"],
            source=row["source"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_historical_questions(
        self,
        category: Optional[str] = None,
        programme: Optional[str] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[HistoricalQuestionRecord]:
        clauses: List[str] = []
        params: List[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if year is not None:
            clauses.append("year = ?")
            params.append(year)
        if search:
            clauses.append("(LOWER(prompt_text) LIKE ? OR LOWER(COALESCE(title,'')) LIKE ? OR LOWER(COALESCE(source,'')) LIKE ?)")
            term = f"%{search.lower()}%"
            params.extend([term, term, term])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM historical_questions {where} ORDER BY COALESCE(year, 0) DESC, created_at DESC",
                params,
            ).fetchall()
        records = [self._row_to_historical(r) for r in rows]
        if programme:
            records = [r for r in records if programme in r.programme_tags]
        return records

    def create_historical_question(self, item: HistoricalQuestionCreate) -> HistoricalQuestionRecord:
        qid = str(uuid.uuid4())
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO historical_questions (
                    id, title, prompt_text, year, category, programme_tags,
                    archetypes, competencies, themes, marks, time_minutes,
                    source, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    qid,
                    item.title,
                    item.prompt_text.strip(),
                    item.year,
                    item.category,
                    json.dumps(item.programme_tags),
                    json.dumps(item.archetypes),
                    json.dumps(item.competencies),
                    json.dumps(item.themes),
                    item.marks,
                    item.time_minutes,
                    item.source,
                    item.notes,
                    now,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM historical_questions WHERE id = ?", (qid,)).fetchone()
        return self._row_to_historical(row)

    def update_historical_question(
        self, qid: str, patch: HistoricalQuestionUpdate
    ) -> Optional[HistoricalQuestionRecord]:
        with self.connect() as conn:
            existing = conn.execute("SELECT * FROM historical_questions WHERE id = ?", (qid,)).fetchone()
            if not existing:
                return None
            rec = self._row_to_historical(existing)
            update_data = patch.model_dump(exclude_unset=True)
            merged = rec.model_copy(update=update_data)
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE historical_questions
                SET title=?, prompt_text=?, year=?, category=?, programme_tags=?,
                    archetypes=?, competencies=?, themes=?, marks=?, time_minutes=?,
                    source=?, notes=?, updated_at=?
                WHERE id=?
                """,
                (
                    merged.title,
                    merged.prompt_text.strip(),
                    merged.year,
                    merged.category,
                    json.dumps(merged.programme_tags),
                    json.dumps(merged.archetypes),
                    json.dumps(merged.competencies),
                    json.dumps(merged.themes),
                    merged.marks,
                    merged.time_minutes,
                    merged.source,
                    merged.notes,
                    now,
                    qid,
                ),
            )
            row = conn.execute("SELECT * FROM historical_questions WHERE id = ?", (qid,)).fetchone()
        return self._row_to_historical(row)

    def delete_historical_question(self, qid: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM historical_questions WHERE id = ?", (qid,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Generated Questions
    # ------------------------------------------------------------------

    def _row_to_generated(self, row: sqlite3.Row) -> StoredGeneratedQuestion:
        return StoredGeneratedQuestion(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            programme_tags=json.loads(row["programme_tags"]),
            archetypes=json.loads(row["archetypes"]),
            competencies=json.loads(row["competencies"]),
            difficulty=row["difficulty"],
            time_minutes=row["time_minutes"],
            total_marks=row["total_marks"],
            scenario=row["scenario"],
            subquestions=json.loads(row["subquestions"]),
            constraints=json.loads(row["constraints"]),
            sketching_requirements=json.loads(row["sketching_requirements"]),
            visual_sketch_prompt=row["visual_sketch_prompt"] if "visual_sketch_prompt" in row.keys() else "",
            visual_negative_prompt=row["visual_negative_prompt"] if "visual_negative_prompt" in row.keys() else "",
            evaluation_rubric=json.loads(row["evaluation_rubric"]),
            practice_priority=row["practice_priority"],
            priority_reason=row["priority_reason"],
            prediction_confidence=row["prediction_confidence"],
            historical_pattern_references=json.loads(row["historical_pattern_references"]),
            suggested_time_split=json.loads(row["suggested_time_split"]),
            generation_mode=row["generation_mode"],
            exam_paper_id=row["exam_paper_id"],
            question_order=row["question_order"],
            is_saved=bool(row["is_saved"]),
            model_used=row["model_used"],
            provider_used=row["provider_used"],
            practice_priority_score=row["practice_priority_score"],
            historical_evidence=json.loads(row["historical_evidence"] or "[]"),
            model_interpretation=row["model_interpretation"] or "",
            low_confidence_warning=row["low_confidence_warning"],
            raw_llm_response=row["raw_llm_response"],
            created_at=row["created_at"],
        )

    def save_generated_question(self, q: StoredGeneratedQuestion) -> StoredGeneratedQuestion:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO generated_questions (
                    id, title, category, programme_tags, archetypes, competencies,
                    difficulty, time_minutes, total_marks, scenario, subquestions,
                    constraints, sketching_requirements, visual_sketch_prompt, visual_negative_prompt,
                    evaluation_rubric, practice_priority, priority_reason, prediction_confidence,
                    historical_pattern_references, suggested_time_split,
                    generation_mode, exam_paper_id, question_order, is_saved,
                    model_used, provider_used, practice_priority_score,
                    historical_evidence, model_interpretation, low_confidence_warning,
                    raw_llm_response, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    q.id,
                    q.title,
                    q.category,
                    json.dumps(q.programme_tags),
                    json.dumps(q.archetypes),
                    json.dumps(q.competencies),
                    q.difficulty,
                    q.time_minutes,
                    q.total_marks,
                    q.scenario,
                    json.dumps([sq.model_dump() for sq in q.subquestions]),
                    json.dumps(q.constraints),
                    json.dumps(q.sketching_requirements),
                    q.visual_sketch_prompt,
                    q.visual_negative_prompt,
                    json.dumps([r.model_dump() for r in q.evaluation_rubric]),
                    q.practice_priority,
                    q.priority_reason,
                    q.prediction_confidence,
                    json.dumps(q.historical_pattern_references),
                    json.dumps([t.model_dump() for t in q.suggested_time_split]),
                    q.generation_mode,
                    q.exam_paper_id,
                    q.question_order,
                    1 if q.is_saved else 0,
                    q.model_used,
                    q.provider_used,
                    q.practice_priority_score,
                    json.dumps(q.historical_evidence),
                    q.model_interpretation,
                    q.low_confidence_warning,
                    q.raw_llm_response,
                    q.created_at,
                ),
            )
        return q

    def list_generated_questions(
        self,
        saved_only: bool = False,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[StoredGeneratedQuestion]:
        clauses: List[str] = []
        params: List[Any] = []
        if saved_only:
            clauses.append("is_saved = 1")
        if category:
            clauses.append("category = ?")
            params.append(category)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM generated_questions {where} ORDER BY created_at DESC LIMIT ?",
                params,
            ).fetchall()
        return [self._row_to_generated(r) for r in rows]

    def get_generated_question(self, qid: str) -> Optional[StoredGeneratedQuestion]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM generated_questions WHERE id = ?", (qid,)).fetchone()
        return self._row_to_generated(row) if row else None

    def set_question_saved(self, qid: str, saved: bool) -> Optional[StoredGeneratedQuestion]:
        with self.connect() as conn:
            conn.execute(
                "UPDATE generated_questions SET is_saved = ? WHERE id = ?",
                (1 if saved else 0, qid),
            )
            row = conn.execute("SELECT * FROM generated_questions WHERE id = ?", (qid,)).fetchone()
        return self._row_to_generated(row) if row else None

    def delete_generated_question(self, qid: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM generated_questions WHERE id = ?", (qid,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Exam Papers
    # ------------------------------------------------------------------

    def create_exam_paper(self, paper: ExamPaperRecord) -> ExamPaperRecord:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO exam_papers (
                    id, title, num_questions, total_time_minutes, difficulty,
                    paper_strategy, historical_relevance, programme_focus,
                    status, elapsed_seconds, warnings, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper.id,
                    paper.title,
                    paper.num_questions,
                    paper.total_time_minutes,
                    paper.difficulty,
                    paper.paper_strategy,
                    paper.historical_relevance,
                    json.dumps(paper.programme_focus),
                    paper.status,
                    paper.elapsed_seconds,
                    json.dumps(paper.warnings),
                    paper.created_at,
                ),
            )
        return paper

    def list_exam_papers(self, limit: int = 30) -> List[ExamPaperRecord]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM exam_papers ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            papers: List[ExamPaperRecord] = []
            for r in rows:
                q_rows = conn.execute(
                    "SELECT * FROM generated_questions WHERE exam_paper_id = ? ORDER BY question_order ASC",
                    (r["id"],),
                ).fetchall()
                papers.append(
                    ExamPaperRecord(
                        id=r["id"],
                        title=r["title"],
                        num_questions=r["num_questions"],
                        total_time_minutes=r["total_time_minutes"],
                        difficulty=r["difficulty"],
                        paper_strategy=r["paper_strategy"],
                        historical_relevance=r["historical_relevance"],
                        programme_focus=json.loads(r["programme_focus"] or "[]"),
                        status=r["status"],
                        elapsed_seconds=r["elapsed_seconds"],
                        warnings=json.loads(r["warnings"] or "[]"),
                        created_at=r["created_at"],
                        questions=[self._row_to_generated(qr) for qr in q_rows],
                    )
                )
        return papers

    def get_exam_paper(self, paper_id: str) -> Optional[ExamPaperRecord]:
        with self.connect() as conn:
            r = conn.execute("SELECT * FROM exam_papers WHERE id = ?", (paper_id,)).fetchone()
            if not r:
                return None
            q_rows = conn.execute(
                "SELECT * FROM generated_questions WHERE exam_paper_id = ? ORDER BY question_order ASC",
                (paper_id,),
            ).fetchall()
        return ExamPaperRecord(
            id=r["id"],
            title=r["title"],
            num_questions=r["num_questions"],
            total_time_minutes=r["total_time_minutes"],
            difficulty=r["difficulty"],
            paper_strategy=r["paper_strategy"],
            historical_relevance=r["historical_relevance"],
            programme_focus=json.loads(r["programme_focus"] or "[]"),
            status=r["status"],
            elapsed_seconds=r["elapsed_seconds"],
            warnings=json.loads(r["warnings"] or "[]"),
            created_at=r["created_at"],
            questions=[self._row_to_generated(qr) for qr in q_rows],
        )

    def update_exam_paper_state(
        self,
        paper_id: str,
        status: Optional[str] = None,
        elapsed_seconds: Optional[int] = None,
    ) -> Optional[ExamPaperRecord]:
        with self.connect() as conn:
            r = conn.execute("SELECT * FROM exam_papers WHERE id = ?", (paper_id,)).fetchone()
            if not r:
                return None
            new_status = status if status is not None else r["status"]
            new_elapsed = elapsed_seconds if elapsed_seconds is not None else r["elapsed_seconds"]
            conn.execute(
                "UPDATE exam_papers SET status = ?, elapsed_seconds = ? WHERE id = ?",
                (new_status, new_elapsed, paper_id),
            )
        return self.get_exam_paper(paper_id)

    def delete_exam_paper(self, paper_id: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM exam_papers WHERE id = ?", (paper_id,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Practice Attempts
    # ------------------------------------------------------------------

    def _row_to_attempt(self, row: sqlite3.Row) -> PracticeAttemptRecord:
        return PracticeAttemptRecord(
            id=row["id"],
            question_id=row["question_id"],
            question_title=row["question_title"],
            category=row["category"],
            programme_tags=json.loads(row["programme_tags"] or "[]"),
            exam_paper_id=row["exam_paper_id"],
            time_allocated_minutes=row["time_allocated_minutes"],
            time_spent_seconds=row["time_spent_seconds"],
            self_difficulty=row["self_difficulty"],
            status=row["status"],
            notes=row["notes"] or "",
            rubric_revealed=bool(row["rubric_revealed"]),
            attempted_at=row["attempted_at"],
        )

    def create_practice_attempt(self, item: PracticeAttemptCreate) -> PracticeAttemptRecord:
        aid = str(uuid.uuid4())
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO practice_attempts (
                    id, question_id, question_title, category, programme_tags,
                    exam_paper_id, time_allocated_minutes, time_spent_seconds,
                    self_difficulty, status, notes, rubric_revealed, attempted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    item.question_id,
                    item.question_title,
                    item.category,
                    json.dumps(item.programme_tags),
                    item.exam_paper_id,
                    item.time_allocated_minutes,
                    item.time_spent_seconds,
                    item.self_difficulty,
                    item.status,
                    item.notes,
                    1 if item.rubric_revealed else 0,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM practice_attempts WHERE id = ?", (aid,)).fetchone()
        return self._row_to_attempt(row)

    def list_practice_attempts(
        self, category: Optional[str] = None, status: Optional[str] = None, limit: int = 200
    ) -> List[PracticeAttemptRecord]:
        clauses: List[str] = []
        params: List[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM practice_attempts {where} ORDER BY attempted_at DESC LIMIT ?",
                params,
            ).fetchall()
        return [self._row_to_attempt(r) for r in rows]

    def update_practice_attempt(
        self, aid: str, patch: PracticeAttemptUpdate
    ) -> Optional[PracticeAttemptRecord]:
        with self.connect() as conn:
            existing = conn.execute("SELECT * FROM practice_attempts WHERE id = ?", (aid,)).fetchone()
            if not existing:
                return None
            rec = self._row_to_attempt(existing)
            merged = rec.model_copy(update=patch.model_dump(exclude_unset=True))
            conn.execute(
                """
                UPDATE practice_attempts
                SET time_spent_seconds=?, self_difficulty=?, status=?, notes=?, rubric_revealed=?
                WHERE id=?
                """,
                (
                    merged.time_spent_seconds,
                    merged.self_difficulty,
                    merged.status,
                    merged.notes,
                    1 if merged.rubric_revealed else 0,
                    aid,
                ),
            )
            row = conn.execute("SELECT * FROM practice_attempts WHERE id = ?", (aid,)).fetchone()
        return self._row_to_attempt(row)

    def delete_practice_attempt(self, aid: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM practice_attempts WHERE id = ?", (aid,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Weak Areas (Manual Student Flags)
    # ------------------------------------------------------------------

    def list_weak_areas(self) -> List[WeakAreaRecord]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM weak_areas ORDER BY created_at DESC").fetchall()
        return [
            WeakAreaRecord(
                id=r["id"],
                area_type=r["area_type"],
                name=r["name"],
                severity=r["severity"],
                notes=r["notes"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def create_weak_area(self, item: WeakAreaCreate) -> WeakAreaRecord:
        wid = str(uuid.uuid4())
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO weak_areas (id, area_type, name, severity, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (wid, item.area_type, item.name, item.severity, item.notes, now),
            )
            row = conn.execute("SELECT * FROM weak_areas WHERE id = ?", (wid,)).fetchone()
        return WeakAreaRecord(
            id=row["id"],
            area_type=row["area_type"],
            name=row["name"],
            severity=row["severity"],
            notes=row["notes"],
            created_at=row["created_at"],
        )

    def delete_weak_area(self, wid: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM weak_areas WHERE id = ?", (wid,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Visual Learning Memory (Continuous Student Exemplar Adaptation)
    # ------------------------------------------------------------------

    def save_visual_learning(self, item: VisualLearningCreate) -> VisualLearningRecord:
        lid = str(uuid.uuid4())
        now = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO visual_learning_memory (
                    id, question_id, question_title, category, archetype,
                    older_prompt, older_image_url, uploaded_image_url, new_image_url,
                    what_changed, why_changed, actionable_guidelines, negative_guidelines, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lid,
                    item.question_id,
                    item.question_title,
                    item.category,
                    item.archetype,
                    item.older_prompt,
                    item.older_image_url,
                    item.uploaded_image_url,
                    item.new_image_url,
                    item.what_changed,
                    item.why_changed,
                    item.actionable_guidelines,
                    item.negative_guidelines,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM visual_learning_memory WHERE id = ?", (lid,)).fetchone()
        return VisualLearningRecord(
            id=row["id"],
            question_id=row["question_id"],
            question_title=row["question_title"],
            category=row["category"],
            archetype=row["archetype"],
            older_prompt=row["older_prompt"],
            older_image_url=row["older_image_url"],
            uploaded_image_url=row["uploaded_image_url"],
            new_image_url=row["new_image_url"],
            what_changed=row["what_changed"],
            why_changed=row["why_changed"],
            actionable_guidelines=row["actionable_guidelines"],
            negative_guidelines=row["negative_guidelines"],
            created_at=row["created_at"],
        )

    def list_visual_learning(
        self, category: Optional[str] = None, limit: int = 50
    ) -> List[VisualLearningRecord]:
        with self.connect() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM visual_learning_memory WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                    (category, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM visual_learning_memory ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [
            VisualLearningRecord(
                id=r["id"],
                question_id=r["question_id"],
                question_title=r["question_title"],
                category=r["category"],
                archetype=r["archetype"],
                older_prompt=r["older_prompt"],
                older_image_url=r["older_image_url"],
                uploaded_image_url=r["uploaded_image_url"],
                new_image_url=r["new_image_url"],
                what_changed=r["what_changed"],
                why_changed=r["why_changed"],
                actionable_guidelines=r["actionable_guidelines"],
                negative_guidelines=r["negative_guidelines"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def get_active_learned_rules_for_category(
        self, category: str, limit: int = 4
    ) -> List[VisualLearningRecord]:
        return self.list_visual_learning(category=category, limit=limit)

    def delete_visual_learning(self, record_id: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM visual_learning_memory WHERE id = ?", (record_id,))
            return cur.rowcount > 0
