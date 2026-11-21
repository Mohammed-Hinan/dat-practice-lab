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
    GATAttemptCreate,
    GATAttemptResult,
    GATLearningTopicRecord,
    GATMockTestCreate,
    GATMockTestRecord,
    GATOverviewResponse,
    GATQuestionCreate,
    GATQuestionRecord,
    GATVisualGKRecord,
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

                CREATE TABLE IF NOT EXISTS gat_questions (
                    id TEXT PRIMARY KEY,
                    exam TEXT NOT NULL,
                    programme TEXT NOT NULL DEFAULT 'Common',
                    section TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    difficulty TEXT NOT NULL DEFAULT 'Medium',
                    question_type TEXT NOT NULL DEFAULT 'multiple_choice',
                    source_type TEXT NOT NULL DEFAULT 'previous_year',
                    source_reference TEXT,
                    year INTEGER,
                    question_text TEXT NOT NULL,
                    image_url TEXT,
                    options TEXT NOT NULL DEFAULT '[]',
                    correct_answers TEXT NOT NULL DEFAULT '[]',
                    explanation TEXT NOT NULL DEFAULT '',
                    verified INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_gat_q_sec ON gat_questions(section);
                CREATE INDEX IF NOT EXISTS idx_gat_q_top ON gat_questions(topic);
                CREATE INDEX IF NOT EXISTS idx_gat_q_exam ON gat_questions(exam);

                CREATE TABLE IF NOT EXISTS gat_attempts (
                    id TEXT PRIMARY KEY,
                    question_id TEXT NOT NULL,
                    user_answers TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
                    mode TEXT NOT NULL DEFAULT 'practice',
                    test_id TEXT,
                    attempted_at TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES gat_questions(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_gat_att_q ON gat_attempts(question_id);

                CREATE TABLE IF NOT EXISTS gat_bookmarks (
                    question_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES gat_questions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS gat_learning_topics (
                    id TEXT PRIMARY KEY,
                    section TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    concept_markdown TEXT NOT NULL,
                    key_formulas_or_facts TEXT NOT NULL DEFAULT '[]',
                    worked_examples TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS gat_visual_gk (
                    id TEXT PRIMARY KEY,
                    subcategory TEXT NOT NULL,
                    title TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    description TEXT NOT NULL,
                    key_facts TEXT NOT NULL DEFAULT '[]',
                    related_quiz_question_id TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS gat_mock_tests (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    exam TEXT NOT NULL DEFAULT 'NIFT M.Des GAT',
                    time_limit_minutes INTEGER NOT NULL DEFAULT 60,
                    question_ids TEXT NOT NULL DEFAULT '[]',
                    user_responses TEXT NOT NULL DEFAULT '{}',
                    score REAL NOT NULL DEFAULT 0.0,
                    total_marks REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'not_started',
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL
                );
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
        self.seed_gat_data_if_empty()

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

    # ------------------------------------------------------------------
    # GAT (General Ability Test) Persistence & Learning Engine
    # ------------------------------------------------------------------

    def seed_gat_data_if_empty(self) -> None:
        try:
            with self.connect() as conn:
                count = conn.execute("SELECT COUNT(*) as c FROM gat_questions").fetchone()["c"]
                if count > 0:
                    return

            now = utc_now_iso()
            data_dir = Path(__file__).resolve().parents[1] / "data"

            # 1. Seed Questions from Roughworks
            q_file = data_dir / "gat_roughworks_questions.json"
            if q_file.exists():
                questions = json.loads(q_file.read_text(encoding="utf-8"))
                with self.connect() as conn:
                    for q in questions:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO gat_questions (
                                id, exam, programme, section, topic, difficulty,
                                question_type, source_type, source_reference, year,
                                question_text, image_url, options, correct_answers,
                                explanation, verified, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                q["id"],
                                q.get("exam", "UCEED"),
                                q.get("programme", "Common"),
                                q["section"],
                                q["topic"],
                                q.get("difficulty", "Medium"),
                                q.get("question_type", "multiple_choice"),
                                q.get("source_type", "previous_year"),
                                q.get("source_reference", "roughworks.in"),
                                q.get("year"),
                                q["question_text"],
                                q.get("image_url"),
                                json.dumps(q.get("options", [])),
                                json.dumps(q.get("correct_answers", [])),
                                q.get("explanation", ""),
                                1 if q.get("verified", True) else 0,
                                now,
                            ),
                        )

            # 2. Seed Learning Topics Curriculum
            t_file = data_dir / "gat_learning_topics.json"
            if t_file.exists():
                topics = json.loads(t_file.read_text(encoding="utf-8"))
                with self.connect() as conn:
                    for t in topics:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO gat_learning_topics (
                                id, section, topic, title, summary, concept_markdown,
                                key_formulas_or_facts, worked_examples, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                t["id"],
                                t["section"],
                                t["topic"],
                                t["topic"],
                                t.get("summary", ""),
                                t.get("concept_explanation", ""),
                                json.dumps(t.get("formulas_and_facts", [])),
                                json.dumps(t.get("worked_examples", [])),
                                now,
                            ),
                        )

            # 3. Seed Visual GK Boards
            v_file = data_dir / "gat_visual_gk.json"
            if v_file.exists():
                visuals = json.loads(v_file.read_text(encoding="utf-8"))
                with self.connect() as conn:
                    for v in visuals:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO gat_visual_gk (
                                id, subcategory, title, image_url, description,
                                key_facts, related_quiz_question_id, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                v["id"],
                                v.get("category", "art_heritage"),
                                v["name"],
                                v["image_url"],
                                v.get("brief", ""),
                                json.dumps(v.get("key_facts", [])),
                                (v.get("related_question_ids") or [None])[0],
                                now,
                            ),
                        )
        except Exception as e:
            # Safe failover: logging quiet to avoid blocking initialization
            pass

    def list_gat_questions(
        self,
        section: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        exam: Optional[str] = None,
        search: Optional[str] = None,
        bookmarked_only: bool = False,
        incorrect_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GATQuestionRecord]:
        clauses = ["1=1"]
        params: List[Any] = []

        if section:
            clauses.append("q.section = ?")
            params.append(section)
        if topic:
            clauses.append("q.topic = ?")
            params.append(topic)
        if difficulty:
            clauses.append("q.difficulty = ?")
            params.append(difficulty)
        if question_type:
            clauses.append("q.question_type = ?")
            params.append(question_type)
        if exam:
            clauses.append("q.exam = ?")
            params.append(exam)
        if search:
            clauses.append("(q.question_text LIKE ? OR q.topic LIKE ?)")
            term = f"%{search.strip()}%"
            params.extend([term, term])
        if bookmarked_only:
            clauses.append("b.question_id IS NOT NULL")
        if incorrect_only:
            clauses.append("latest_att.is_correct = 0")

        query = f"""
            SELECT 
                q.*,
                CASE WHEN b.question_id IS NOT NULL THEN 1 ELSE 0 END AS is_bookmarked,
                latest_att.is_correct AS latest_is_correct,
                latest_att.user_answers AS latest_user_answers
            FROM gat_questions q
            LEFT JOIN gat_bookmarks b ON q.id = b.question_id
            LEFT JOIN (
                SELECT a1.question_id, a1.is_correct, a1.user_answers
                FROM gat_attempts a1
                JOIN (
                    SELECT question_id, MAX(attempted_at) as max_time
                    FROM gat_attempts
                    GROUP BY question_id
                ) a2 ON a1.question_id = a2.question_id AND a1.attempted_at = a2.max_time
            ) latest_att ON q.id = latest_att.question_id
            WHERE {" AND ".join(clauses)}
            ORDER BY q.year DESC, q.id ASC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        records: List[GATQuestionRecord] = []
        for r in rows:
            attempt_status = None
            if r["latest_is_correct"] is not None:
                attempt_status = "correct" if r["latest_is_correct"] == 1 else "incorrect"

            user_prev = None
            if r["latest_user_answers"]:
                try:
                    user_prev = json.loads(r["latest_user_answers"])
                except Exception:
                    user_prev = []

            records.append(
                GATQuestionRecord(
                    id=r["id"],
                    exam=r["exam"],
                    programme=r["programme"],
                    section=r["section"],
                    topic=r["topic"],
                    difficulty=r["difficulty"],
                    question_type=r["question_type"],
                    source_type=r["source_type"],
                    source_reference=r["source_reference"],
                    year=r["year"],
                    question_text=r["question_text"],
                    image_url=r["image_url"],
                    options=json.loads(r["options"]),
                    correct_answers=json.loads(r["correct_answers"]),
                    explanation=r["explanation"],
                    verified=bool(r["verified"]),
                    created_at=r["created_at"],
                    is_bookmarked=bool(r["is_bookmarked"]),
                    attempt_status=attempt_status,
                    user_previous_answer=user_prev,
                )
            )
        return records

    def get_gat_question(self, question_id: str) -> Optional[GATQuestionRecord]:
        items = self.list_gat_questions(search=None, limit=1)
        query = """
            SELECT 
                q.*,
                CASE WHEN b.question_id IS NOT NULL THEN 1 ELSE 0 END AS is_bookmarked,
                latest_att.is_correct AS latest_is_correct,
                latest_att.user_answers AS latest_user_answers
            FROM gat_questions q
            LEFT JOIN gat_bookmarks b ON q.id = b.question_id
            LEFT JOIN (
                SELECT a1.question_id, a1.is_correct, a1.user_answers
                FROM gat_attempts a1
                JOIN (
                    SELECT question_id, MAX(attempted_at) as max_time
                    FROM gat_attempts
                    GROUP BY question_id
                ) a2 ON a1.question_id = a2.question_id AND a1.attempted_at = a2.max_time
            ) latest_att ON q.id = latest_att.question_id
            WHERE q.id = ?
            LIMIT 1
        """
        with self.connect() as conn:
            r = conn.execute(query, (question_id,)).fetchone()
            if not r:
                return None

        attempt_status = None
        if r["latest_is_correct"] is not None:
            attempt_status = "correct" if r["latest_is_correct"] == 1 else "incorrect"

        user_prev = None
        if r["latest_user_answers"]:
            try:
                user_prev = json.loads(r["latest_user_answers"])
            except Exception:
                user_prev = []

        return GATQuestionRecord(
            id=r["id"],
            exam=r["exam"],
            programme=r["programme"],
            section=r["section"],
            topic=r["topic"],
            difficulty=r["difficulty"],
            question_type=r["question_type"],
            source_type=r["source_type"],
            source_reference=r["source_reference"],
            year=r["year"],
            question_text=r["question_text"],
            image_url=r["image_url"],
            options=json.loads(r["options"]),
            correct_answers=json.loads(r["correct_answers"]),
            explanation=r["explanation"],
            verified=bool(r["verified"]),
            created_at=r["created_at"],
            is_bookmarked=bool(r["is_bookmarked"]),
            attempt_status=attempt_status,
            user_previous_answer=user_prev,
        )

    def record_gat_attempt(self, attempt: GATAttemptCreate) -> GATAttemptResult:
        with self.connect() as conn:
            q_row = conn.execute(
                "SELECT correct_answers, explanation, question_type FROM gat_questions WHERE id = ?",
                (attempt.question_id,),
            ).fetchone()
            if not q_row:
                raise ValueError(f"GAT question not found: {attempt.question_id}")

            correct_answers = json.loads(q_row["correct_answers"])
            q_type = q_row["question_type"]
            explanation = q_row["explanation"]

            # Evaluation logic by question type
            user_clean = [ans.strip().upper() for ans in attempt.user_answers if ans.strip()]
            correct_clean = [ans.strip().upper() for ans in correct_answers]

            is_correct = False
            if q_type == "numerical":
                if user_clean and correct_clean:
                    try:
                        u_val = float(user_clean[0])
                        c_val = float(correct_clean[0])
                        is_correct = abs(u_val - c_val) < 0.01
                    except ValueError:
                        is_correct = user_clean[0] == correct_clean[0]
            elif q_type == "multiple_select":
                is_correct = set(user_clean) == set(correct_clean) and len(user_clean) > 0
            else:
                # single multiple choice
                is_correct = sorted(user_clean) == sorted(correct_clean) and len(user_clean) > 0

            att_id = str(uuid.uuid4())
            now = utc_now_iso()
            conn.execute(
                """
                INSERT INTO gat_attempts (
                    id, question_id, user_answers, is_correct, time_spent_seconds, mode, test_id, attempted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    att_id,
                    attempt.question_id,
                    json.dumps(attempt.user_answers),
                    1 if is_correct else 0,
                    attempt.time_spent_seconds,
                    attempt.mode,
                    attempt.test_id,
                    now,
                ),
            )

        return GATAttemptResult(
            is_correct=is_correct,
            correct_answers=correct_answers,
            explanation=explanation,
            time_spent_seconds=attempt.time_spent_seconds,
        )

    def toggle_gat_bookmark(self, question_id: str, is_bookmarked: bool) -> bool:
        with self.connect() as conn:
            if is_bookmarked:
                conn.execute(
                    "INSERT OR IGNORE INTO gat_bookmarks (question_id, created_at) VALUES (?, ?)",
                    (question_id, utc_now_iso()),
                )
            else:
                conn.execute("DELETE FROM gat_bookmarks WHERE question_id = ?", (question_id,))
        return is_bookmarked

    def get_gat_overview(self) -> GATOverviewResponse:
        with self.connect() as conn:
            total_q = conn.execute("SELECT COUNT(*) as c FROM gat_questions").fetchone()["c"]
            b_count = conn.execute("SELECT COUNT(*) as c FROM gat_bookmarks").fetchone()["c"]

            # Distinct questions attempted
            att_stats = conn.execute(
                """
                SELECT 
                    COUNT(DISTINCT question_id) as attempted,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as total_correct_attempts,
                    COUNT(*) as total_attempts
                FROM gat_attempts
                """
            ).fetchone()
            total_attempted = att_stats["attempted"] or 0
            total_attempts = att_stats["total_attempts"] or 0
            total_correct = att_stats["total_correct_attempts"] or 0
            accuracy = round((total_correct / total_attempts * 100), 1) if total_attempts > 0 else 0.0

            # Count latest incorrect questions
            inc_row = conn.execute(
                """
                SELECT COUNT(*) as inc_count
                FROM (
                    SELECT a1.question_id, a1.is_correct
                    FROM gat_attempts a1
                    JOIN (
                        SELECT question_id, MAX(attempted_at) as max_time
                        FROM gat_attempts
                        GROUP BY question_id
                    ) a2 ON a1.question_id = a2.question_id AND a1.attempted_at = a2.max_time
                    WHERE a1.is_correct = 0
                )
                """
            ).fetchone()
            incorrect_count = inc_row["inc_count"] or 0

            # Section-wise breakdown
            sections = [
                ("quantitative_ability", "Quantitative Ability", "Arithmetic, Ratios, Speed & Geometry"),
                ("analytical_reasoning", "Analytical & Logical Reasoning", "Spatial, Syllogisms & Patterns"),
                ("english", "English & Verbal Ability", "Vocabulary, Comprehension & Rearrangement"),
                ("gk_awareness", "GK & Design Awareness", "Crafts, Architecture, Heritage & History"),
            ]
            sections_progress = []
            for sec_key, sec_title, sec_desc in sections:
                sec_total = conn.execute(
                    "SELECT COUNT(*) as c FROM gat_questions WHERE section = ?", (sec_key,)
                ).fetchone()["c"]
                sec_att = conn.execute(
                    """
                    SELECT 
                        COUNT(DISTINCT a.question_id) as att_count,
                        SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as cor_count,
                        COUNT(a.id) as total_runs
                    FROM gat_attempts a
                    JOIN gat_questions q ON a.question_id = q.id
                    WHERE q.section = ?
                    """,
                    (sec_key,),
                ).fetchone()
                att_c = sec_att["att_count"] or 0
                cor_c = sec_att["cor_count"] or 0
                runs_c = sec_att["total_runs"] or 0
                sec_acc = round((cor_c / runs_c * 100), 1) if runs_c > 0 else 0.0
                sections_progress.append(
                    {
                        "section": sec_key,
                        "title": sec_title,
                        "description": sec_desc,
                        "total_questions": sec_total,
                        "attempted_questions": att_c,
                        "accuracy_percentage": sec_acc,
                    }
                )

            # Weak topics: topics where latest attempts had lowest accuracy
            weak_rows = conn.execute(
                """
                SELECT 
                    q.topic,
                    q.section,
                    COUNT(a.id) as attempts,
                    SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM gat_attempts a
                JOIN gat_questions q ON a.question_id = q.id
                GROUP BY q.topic, q.section
                HAVING attempts >= 1 AND (CAST(correct as REAL) / attempts) < 0.7
                ORDER BY (CAST(correct as REAL) / attempts) ASC
                LIMIT 5
                """
            ).fetchall()
            weak_topics = [
                {
                    "topic": r["topic"],
                    "section": r["section"],
                    "accuracy": round((r["correct"] / r["attempts"]) * 100, 1),
                    "attempts": r["attempts"],
                }
                for r in weak_rows
            ]

            # Recent activity
            recent_rows = conn.execute(
                """
                SELECT 
                    a.id, a.question_id, a.is_correct, a.time_spent_seconds, a.attempted_at,
                    q.question_text, q.section, q.topic
                FROM gat_attempts a
                JOIN gat_questions q ON a.question_id = q.id
                ORDER BY a.attempted_at DESC
                LIMIT 6
                """
            ).fetchall()
            recent_activity = [
                {
                    "id": r["id"],
                    "question_id": r["question_id"],
                    "is_correct": bool(r["is_correct"]),
                    "time_spent_seconds": r["time_spent_seconds"],
                    "attempted_at": r["attempted_at"],
                    "question_text": r["question_text"][:80] + "..." if len(r["question_text"]) > 80 else r["question_text"],
                    "section": r["section"],
                    "topic": r["topic"],
                }
                for r in recent_rows
            ]

        recommended_practice = {
            "title": "High-Yield Design GAT Sprint",
            "description": "5 focused practice questions spanning Quant, Spatial & Design Awareness",
            "section": "quantitative_ability",
            "target_questions": 5,
        }

        return GATOverviewResponse(
            total_questions=total_q,
            total_attempted=total_attempted,
            total_correct=total_correct,
            accuracy_percentage=accuracy,
            bookmarked_count=b_count,
            incorrect_count=incorrect_count,
            sections_progress=sections_progress,
            weak_topics=weak_topics,
            recent_activity=recent_activity,
            recommended_practice=recommended_practice,
        )

    def list_gat_learning_topics(self, section: Optional[str] = None) -> List[GATLearningTopicRecord]:
        query = "SELECT * FROM gat_learning_topics"
        params: List[Any] = []
        if section:
            query += " WHERE section = ?"
            params.append(section)
        query += " ORDER BY section, topic ASC"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        records: List[GATLearningTopicRecord] = []
        for r in rows:
            with self.connect() as conn:
                q_stats = conn.execute(
                    """
                    SELECT 
                        COUNT(q.id) as total_q,
                        COUNT(DISTINCT a.question_id) as att_q,
                        SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as cor_att,
                        COUNT(a.id) as total_att
                    FROM gat_questions q
                    LEFT JOIN gat_attempts a ON q.id = a.question_id
                    WHERE q.section = ? AND (q.topic = ? OR q.topic LIKE ?)
                    """,
                    (r["section"], r["topic"], f"%{r['topic']}%"),
                ).fetchone()

            tot_q = q_stats["total_q"] or 0
            att_q = q_stats["att_q"] or 0
            cor_att = q_stats["cor_att"] or 0
            tot_att = q_stats["total_att"] or 0
            mastery = round((cor_att / tot_att * 100), 1) if tot_att > 0 else 0.0

            records.append(
                GATLearningTopicRecord(
                    id=r["id"],
                    section=r["section"],
                    topic=r["topic"],
                    title=r["title"],
                    summary=r["summary"],
                    concept_markdown=r["concept_markdown"],
                    key_formulas_or_facts=json.loads(r["key_formulas_or_facts"]),
                    worked_examples=json.loads(r["worked_examples"]),
                    total_questions=tot_q,
                    attempted_questions=att_q,
                    mastery_percentage=mastery,
                )
            )
        return records

    def list_gat_visual_gk(self, subcategory: Optional[str] = None) -> List[GATVisualGKRecord]:
        query = "SELECT * FROM gat_visual_gk"
        params: List[Any] = []
        if subcategory and subcategory != "all":
            query += " WHERE subcategory = ?"
            params.append(subcategory)
        query += " ORDER BY created_at ASC"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            GATVisualGKRecord(
                id=r["id"],
                subcategory=r["subcategory"],
                title=r["title"],
                image_url=r["image_url"],
                description=r["description"],
                key_facts=json.loads(r["key_facts"]),
                related_quiz_question_id=r["related_quiz_question_id"],
            )
            for r in rows
        ]

    def create_gat_mock_test(self, payload: GATMockTestCreate) -> GATMockTestRecord:
        with self.connect() as conn:
            clauses = ["1=1"]
            params: List[Any] = []
            if payload.section_filter:
                clauses.append("section = ?")
                params.append(payload.section_filter)

            q_rows = conn.execute(
                f"SELECT id FROM gat_questions WHERE {' AND '.join(clauses)} ORDER BY RANDOM() LIMIT ?",
                (*params, payload.num_questions),
            ).fetchall()
            q_ids = [r["id"] for r in q_rows]

            test_id = str(uuid.uuid4())
            now = utc_now_iso()
            total_marks = float(len(q_ids))

            conn.execute(
                """
                INSERT INTO gat_mock_tests (
                    id, title, exam, time_limit_minutes, question_ids, user_responses,
                    score, total_marks, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    test_id,
                    payload.title,
                    payload.exam,
                    payload.time_limit_minutes,
                    json.dumps(q_ids),
                    json.dumps({}),
                    0.0,
                    total_marks,
                    "not_started",
                    now,
                ),
            )

        return self.get_gat_mock_test(test_id)  # type: ignore

    def get_gat_mock_test(self, test_id: str) -> Optional[GATMockTestRecord]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM gat_mock_tests WHERE id = ?", (test_id,)).fetchone()
            if not row:
                return None

        q_ids = json.loads(row["question_ids"])
        questions = [self.get_gat_question(qid) for qid in q_ids]
        questions_clean = [q for q in questions if q is not None]

        return GATMockTestRecord(
            id=row["id"],
            title=row["title"],
            exam=row["exam"],
            time_limit_minutes=row["time_limit_minutes"],
            question_ids=q_ids,
            user_responses=json.loads(row["user_responses"]),
            score=row["score"],
            total_marks=row["total_marks"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
            questions=questions_clean,
        )

    def submit_gat_mock_test(self, test_id: str, responses: Dict[str, List[str]]) -> GATMockTestRecord:
        test = self.get_gat_mock_test(test_id)
        if not test:
            raise ValueError(f"Mock test not found: {test_id}")

        score = 0.0
        now = utc_now_iso()

        # Grade each question: +1 for correct, -0.25 for incorrect MCQ/MSQ, 0 for unattempted
        for q in (test.questions or []):
            user_ans = responses.get(q.id, [])
            if not user_ans:
                continue

            att = self.record_gat_attempt(
                GATAttemptCreate(
                    question_id=q.id,
                    user_answers=user_ans,
                    time_spent_seconds=0,
                    mode="exam",
                    test_id=test_id,
                )
            )
            if att.is_correct:
                score += 1.0
            else:
                if q.question_type == "numerical":
                    score += 0.0  # NAT generally has zero negative marking
                else:
                    score = max(0.0, score - 0.25)

        with self.connect() as conn:
            conn.execute(
                """
                UPDATE gat_mock_tests
                SET user_responses = ?, score = ?, status = 'completed', completed_at = ?
                WHERE id = ?
                """,
                (json.dumps(responses), score, now, test_id),
            )

        return self.get_gat_mock_test(test_id)  # type: ignore

    def list_gat_mock_tests(self) -> List[GATMockTestRecord]:
        with self.connect() as conn:
            rows = conn.execute("SELECT id FROM gat_mock_tests ORDER BY created_at DESC LIMIT 20").fetchall()
        tests = []
        for r in rows:
            t = self.get_gat_mock_test(r["id"])
            if t:
                tests.append(t)
        return tests

