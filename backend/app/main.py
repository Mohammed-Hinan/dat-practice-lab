"""FastAPI backend application for DAT Practice Lab."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from .database import Database
from .drawthings_service import DrawThingsService
from .historical_analyser import classify_question_text
from .llm_service import LLMService
from .ollama_provider import LLMProviderError
from .prediction_engine import compute_analytics_and_predictions
from .question_bank import (
    export_historical_to_csv,
    parse_bulk_text,
    parse_csv_import,
    parse_json_import,
)
from .question_generator import QuestionGenerator
from .schemas import (
    AnalyticsOverviewResponse,
    AppSettings,
    BulkImportCommitRequest,
    BulkParseRequest,
    BulkParseResponse,
    CraftSketchPromptRequest,
    CraftSketchPromptResponse,
    DrawThingsEssenceResponse,
    DrawThingsGenerateRequest,
    DrawThingsGenerateResponse,
    DrawThingsStatus,
    ExamPaperCreateRequest,
    ExamPaperRecord,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    HistoricalQuestionCreate,
    HistoricalQuestionRecord,
    HistoricalQuestionUpdate,
    LLMConnectionStatus,
    LLMTestRequest,
    PracticeAttemptCreate,
    PracticeAttemptRecord,
    PracticeAttemptUpdate,
    StoredGeneratedQuestion,
    VisualDeltaAnalysis,
    VisualLearningRecord,
    WeakAreaCreate,
    WeakAreaRecord,
)
from .taxonomy import (
    ARCHETYPES,
    CATEGORIES,
    CATEGORY_DEFINITIONS,
    DNERD_REFERENCE_METADATA,
    PREPARATION_PROFILES,
    PROGRAMME_TAGS,
    RECURRING_THEMES,
    STANDARD_COMPETENCIES,
)


def create_app(db_instance: Optional[Database] = None) -> FastAPI:
    app = FastAPI(
        title="DAT Practice Lab API",
        version="1.0.0",
        description="Local AI-powered NID M.Des DAT Prelims examination preparation backend.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    db = db_instance or Database()
    llm_service = LLMService()
    drawthings_service = DrawThingsService()
    generator = QuestionGenerator(db=db, llm_service=llm_service)

    app.state.db = db
    app.state.llm_service = llm_service
    app.state.drawthings_service = drawthings_service
    app.state.generator = generator

    # ------------------------------------------------------------------
    # Health & Taxonomy
    # ------------------------------------------------------------------

    @app.get("/api/health")
    def health() -> Dict[str, Any]:
        return {"status": "ok", "db_path": str(db.db_path)}

    @app.get("/api/taxonomy")
    def get_taxonomy() -> Dict[str, Any]:
        return {
            "categories": CATEGORIES,
            "category_definitions": CATEGORY_DEFINITIONS,
            "programme_tags": PROGRAMME_TAGS,
            "archetypes": ARCHETYPES,
            "preparation_profiles": list(PREPARATION_PROFILES.values()),
            "recurring_themes": RECURRING_THEMES,
            "competencies": STANDARD_COMPETENCIES,
            "dnerd_reference": DNERD_REFERENCE_METADATA,
        }

    # ------------------------------------------------------------------
    # Settings & Local LLM Connection
    # ------------------------------------------------------------------

    def _mask_sensitive_settings(settings: AppSettings) -> AppSettings:
        masked = settings.model_copy()
        masked.has_gemini_key = bool(settings.gemini_api_key)
        masked.has_groq_key = bool(settings.groq_api_key)
        masked.has_custom_key = bool(settings.custom_api_key)
        masked.has_openai_key = bool(settings.openai_api_key)
        if masked.gemini_api_key:
            masked.gemini_api_key = "••••••••"
        if masked.groq_api_key:
            masked.groq_api_key = "••••••••"
        if masked.custom_api_key:
            masked.custom_api_key = "••••••••"
        if masked.openai_api_key:
            masked.openai_api_key = "••••••••"
        return masked

    @app.get("/api/settings", response_model=AppSettings)
    def get_settings() -> AppSettings:
        return _mask_sensitive_settings(db.get_settings())

    @app.put("/api/settings", response_model=AppSettings)
    def update_settings(payload: AppSettings) -> AppSettings:
        saved = db.save_settings(payload)
        return _mask_sensitive_settings(saved)

    @app.get("/api/llm/status", response_model=LLMConnectionStatus)
    async def llm_status() -> LLMConnectionStatus:
        settings = db.get_settings()
        return await llm_service.test_connection(settings)

    @app.post("/api/llm/test", response_model=LLMConnectionStatus)
    async def test_llm_connection(req: LLMTestRequest) -> LLMConnectionStatus:
        settings = db.get_settings()
        api_key = req.api_key or ""
        # If the client sent a masked or empty key, fall back to the actual saved secret
        if api_key.startswith("••••") or not api_key:
            if req.provider == "gemini":
                api_key = settings.gemini_api_key
            elif req.provider == "groq":
                api_key = settings.groq_api_key
            elif req.provider == "custom_openai":
                api_key = settings.custom_api_key
        return await llm_service.test_connection(
            settings=settings,
            provider=req.provider,
            override_url=req.base_url,
            override_api_key=api_key,
            override_model=req.model,
        )

    # ------------------------------------------------------------------
    # Local Draw Things Sketch Reference Engine
    # ------------------------------------------------------------------

    @app.get("/api/drawthings/status", response_model=DrawThingsStatus)
    async def drawthings_status() -> DrawThingsStatus:
        settings = db.get_settings()
        return await drawthings_service.test_connection(settings)

    class DrawThingsTestBody(BaseModel):
        base_url: Optional[str] = None

    @app.post("/api/drawthings/test", response_model=DrawThingsStatus)
    async def test_drawthings(body: DrawThingsTestBody) -> DrawThingsStatus:
        settings = db.get_settings()
        return await drawthings_service.test_connection(settings, override_url=body.base_url)

    @app.get("/api/drawthings/essence", response_model=DrawThingsEssenceResponse)
    def get_drawthings_essence() -> DrawThingsEssenceResponse:
        return drawthings_service.get_essence_metadata()

    @app.post("/api/drawthings/craft-prompt", response_model=CraftSketchPromptResponse)
    async def craft_drawthings_prompt(
        req: CraftSketchPromptRequest,
    ) -> CraftSketchPromptResponse:
        settings = db.get_settings()
        return await drawthings_service.craft_visual_prompt(
            settings=settings,
            llm_service=llm_service,
            req=req,
            db=db,
        )

    @app.post("/api/drawthings/generate", response_model=DrawThingsGenerateResponse)
    async def generate_drawthings_sketch(
        req: DrawThingsGenerateRequest,
    ) -> DrawThingsGenerateResponse:
        settings = db.get_settings()
        try:
            return await drawthings_service.generate_reference_sketch(
                settings=settings,
                req=req,
                db=db,
                llm_service=llm_service,
            )
        except LLMProviderError as exc:
            import traceback
            print(f"GENERATION ERROR: {exc}", flush=True)
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/drawthings/learned-rules", response_model=List[VisualLearningRecord])
    def list_learned_rules(
        category: Optional[str] = None,
        limit: int = Query(default=30, ge=1, le=100),
    ) -> List[VisualLearningRecord]:
        return db.list_visual_learning(category=category, limit=limit)

    @app.delete("/api/drawthings/learned-rules/{rule_id}")
    def delete_learned_rule(rule_id: str) -> Dict[str, bool]:
        ok = db.delete_visual_learning(rule_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Learned rule not found.")
        return {"deleted": True}

    @app.get("/api/sketches/{filename}")
    def get_saved_sketch(filename: str):
        if "/" in filename or "\\" in filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid sketch filename.")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ("png", "jpg", "jpeg", "webp"):
            raise HTTPException(status_code=400, detail="Invalid sketch filename extension.")
        path = drawthings_service.sketches_dir / filename
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Sketch not found.")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        return FileResponse(path, media_type=media_type)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @app.get("/api/dashboard")
    def get_dashboard() -> Dict[str, Any]:
        settings = db.get_settings()
        historical = db.list_historical_questions()
        attempts = db.list_practice_attempts(limit=500)
        weak_areas = db.list_weak_areas()
        recent_questions = db.list_generated_questions(limit=8)
        saved_questions_count = len(db.list_generated_questions(saved_only=True, limit=500))
        exam_papers_count = len(db.list_exam_papers(limit=100))

        analytics = compute_analytics_and_predictions(
            historical_records=historical,
            attempts=attempts,
            weak_areas=weak_areas,
            settings=settings,
        )

        completed = [a for a in attempts if a.status == "completed"]
        skipped = [a for a in attempts if a.status == "skipped"]
        total_seconds = sum(a.time_spent_seconds for a in attempts)
        cat_attempts = Counter(a.category for a in completed)

        category_coverage = [
            {
                "category": cp.category,
                "attempted": cat_attempts.get(cp.category, 0),
                "historical_count": cp.historical_count,
                "priority_score": cp.practice_priority_score,
                "is_under_practised": cp.is_under_practised,
                "is_flagged_weak": cp.is_flagged_weak,
            }
            for cp in analytics.category_priorities
        ]
        # Order alphabetically/canonical for chart clarity
        cat_order = {c: i for i, c in enumerate(CATEGORIES)}
        category_coverage.sort(key=lambda x: cat_order.get(x["category"], 99))

        under_practised = [c for c in analytics.category_priorities if c.is_under_practised or c.is_flagged_weak]
        top_cat = analytics.category_priorities[0] if analytics.category_priorities else None
        top_theme = analytics.theme_priorities[0] if analytics.theme_priorities else None

        recommended_session = {
            "category": top_cat.category if top_cat else "Problem identification",
            "theme_id": top_theme.theme_id if top_theme else None,
            "theme_label": top_theme.label if top_theme else "Public Infrastructure & Everyday Problems",
            "suggested_mode": "balanced_random",
            "suggested_time_minutes": 20,
            "reason": (
                f"Prioritise '{top_cat.category}' ({top_cat.reason}) paired with theme "
                f"'{top_theme.label}' (priority {top_theme.practice_priority_score:.0f}/100)."
                if top_cat and top_theme
                else "Start a balanced 30-minute DAT Prelims session across all seven categories."
            ),
        }

        return {
            "stats": {
                "total_attempts": len(attempts),
                "completed_attempts": len(completed),
                "skipped_attempts": len(skipped),
                "total_practice_seconds": total_seconds,
                "saved_questions_count": saved_questions_count,
                "historical_questions_count": len(historical),
                "exam_papers_count": exam_papers_count,
                "categories_covered": sum(1 for c in CATEGORIES if cat_attempts.get(c, 0) > 0),
                "total_categories": len(CATEGORIES),
            },
            "category_coverage": category_coverage,
            "weak_and_under_practised": [c.model_dump() for c in under_practised[:4]],
            "manual_weak_areas": [w.model_dump() for w in weak_areas],
            "recent_questions": [q.model_dump() for q in recent_questions],
            "top_themes": [t.model_dump() for t in analytics.theme_priorities[:5]],
            "confidence_level": analytics.confidence_level,
            "low_confidence_warning": analytics.low_confidence_warning,
            "active_profiles": [
                PREPARATION_PROFILES[p] for p in analytics.active_profiles if p in PREPARATION_PROFILES
            ],
            "recommended_session": recommended_session,
        }

    # ------------------------------------------------------------------
    # Question Generation & Saved Questions
    # ------------------------------------------------------------------

    @app.post("/api/questions/generate", response_model=GenerateQuestionsResponse)
    async def generate_questions(req: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
        try:
            return await generator.generate_questions(req)
        except LLMProviderError as exc:
            import traceback
            print(f"GENERATION ERROR: {exc}", flush=True)
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/questions", response_model=List[StoredGeneratedQuestion])
    def list_generated_questions(
        saved_only: bool = False,
        category: Optional[str] = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> List[StoredGeneratedQuestion]:
        return db.list_generated_questions(saved_only=saved_only, category=category, limit=limit)

    @app.get("/api/questions/{question_id}", response_model=StoredGeneratedQuestion)
    def get_generated_question(question_id: str) -> StoredGeneratedQuestion:
        q = db.get_generated_question(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="Generated question not found.")
        return q

    class SaveToggleBody(BaseModel):
        saved: bool

    @app.patch("/api/questions/{question_id}/save", response_model=StoredGeneratedQuestion)
    def toggle_save_question(question_id: str, body: SaveToggleBody) -> StoredGeneratedQuestion:
        q = db.set_question_saved(question_id, body.saved)
        if not q:
            raise HTTPException(status_code=404, detail="Generated question not found.")
        return q

    @app.delete("/api/questions/{question_id}")
    def delete_generated_question(question_id: str) -> Dict[str, bool]:
        ok = db.delete_generated_question(question_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Generated question not found.")
        return {"deleted": True}

    # ------------------------------------------------------------------
    # Mode D — Exam Simulator
    # ------------------------------------------------------------------

    @app.post("/api/exams/generate", response_model=ExamPaperRecord)
    async def generate_exam_paper(req: ExamPaperCreateRequest) -> ExamPaperRecord:
        try:
            return await generator.generate_exam_paper(req)
        except LLMProviderError as exc:
            import traceback
            print(f"GENERATION ERROR: {exc}", flush=True)
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/exams", response_model=List[ExamPaperRecord])
    def list_exam_papers() -> List[ExamPaperRecord]:
        return db.list_exam_papers()

    @app.get("/api/exams/{paper_id}", response_model=ExamPaperRecord)
    def get_exam_paper(paper_id: str) -> ExamPaperRecord:
        paper = db.get_exam_paper(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Exam paper not found.")
        return paper

    class ExamPaperPatch(BaseModel):
        status: Optional[str] = None
        elapsed_seconds: Optional[int] = None

    @app.patch("/api/exams/{paper_id}", response_model=ExamPaperRecord)
    def patch_exam_paper(paper_id: str, body: ExamPaperPatch) -> ExamPaperRecord:
        paper = db.update_exam_paper_state(paper_id, status=body.status, elapsed_seconds=body.elapsed_seconds)
        if not paper:
            raise HTTPException(status_code=404, detail="Exam paper not found.")
        return paper

    @app.delete("/api/exams/{paper_id}")
    def delete_exam_paper(paper_id: str) -> Dict[str, bool]:
        ok = db.delete_exam_paper(paper_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Exam paper not found.")
        return {"deleted": True}

    # ------------------------------------------------------------------
    # Historical Question Bank
    # ------------------------------------------------------------------

    @app.get("/api/historical", response_model=List[HistoricalQuestionRecord])
    def list_historical(
        category: Optional[str] = None,
        programme: Optional[str] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[HistoricalQuestionRecord]:
        return db.list_historical_questions(category=category, programme=programme, year=year, search=search)

    @app.post("/api/historical", response_model=HistoricalQuestionRecord)
    def create_historical(item: HistoricalQuestionCreate) -> HistoricalQuestionRecord:
        # Enrich archetypes/themes/competencies if left empty by manual entry
        cls = classify_question_text(item.prompt_text, explicit_category=item.category)
        enriched = item.model_copy(
            update={
                "archetypes": item.archetypes or cls["archetypes"],
                "themes": item.themes or cls["themes"],
                "competencies": item.competencies or cls["competencies"],
                "title": item.title or item.prompt_text.strip().splitlines()[0][:88],
            }
        )
        return db.create_historical_question(enriched)

    @app.put("/api/historical/{question_id}", response_model=HistoricalQuestionRecord)
    def update_historical(question_id: str, patch: HistoricalQuestionUpdate) -> HistoricalQuestionRecord:
        updated = db.update_historical_question(question_id, patch)
        if not updated:
            raise HTTPException(status_code=404, detail="Historical question not found.")
        return updated

    @app.delete("/api/historical/{question_id}")
    def delete_historical(question_id: str) -> Dict[str, bool]:
        ok = db.delete_historical_question(question_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Historical question not found.")
        return {"deleted": True}

    @app.post("/api/historical/parse", response_model=BulkParseResponse)
    def parse_historical_bulk(req: BulkParseRequest) -> BulkParseResponse:
        if req.format == "csv":
            return parse_csv_import(req.content, default_source=req.default_source)
        if req.format == "json":
            return parse_json_import(req.content, default_source=req.default_source)
        return parse_bulk_text(req.content, default_source=req.default_source)

    @app.post("/api/historical/import", response_model=List[HistoricalQuestionRecord])
    def commit_historical_import(req: BulkImportCommitRequest) -> List[HistoricalQuestionRecord]:
        created: List[HistoricalQuestionRecord] = []
        for item in req.questions:
            cls = classify_question_text(item.prompt_text, explicit_category=item.category)
            enriched = item.model_copy(
                update={
                    "archetypes": item.archetypes or cls["archetypes"],
                    "themes": item.themes or cls["themes"],
                    "competencies": item.competencies or cls["competencies"],
                    "title": item.title or item.prompt_text.strip().splitlines()[0][:88],
                }
            )
            created.append(db.create_historical_question(enriched))
        return created

    @app.get("/api/historical/export")
    def export_historical(format: str = Query(default="json", pattern="^(json|csv)$")):
        records = db.list_historical_questions()
        if format == "csv":
            return PlainTextResponse(
                content=export_historical_to_csv(records),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=nid_historical_questions.csv"},
            )
        return [r.model_dump() for r in records]

    # ------------------------------------------------------------------
    # Trends & Predictions Analytics
    # ------------------------------------------------------------------

    @app.get("/api/analytics/overview", response_model=AnalyticsOverviewResponse)
    def analytics_overview() -> AnalyticsOverviewResponse:
        settings = db.get_settings()
        return compute_analytics_and_predictions(
            historical_records=db.list_historical_questions(),
            attempts=db.list_practice_attempts(limit=500),
            weak_areas=db.list_weak_areas(),
            settings=settings,
        )

    # ------------------------------------------------------------------
    # Practice History & Weak Areas
    # ------------------------------------------------------------------

    @app.get("/api/attempts", response_model=List[PracticeAttemptRecord])
    def list_attempts(
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[PracticeAttemptRecord]:
        return db.list_practice_attempts(category=category, status=status)

    @app.post("/api/attempts", response_model=PracticeAttemptRecord)
    def create_attempt(item: PracticeAttemptCreate) -> PracticeAttemptRecord:
        return db.create_practice_attempt(item)

    @app.patch("/api/attempts/{attempt_id}", response_model=PracticeAttemptRecord)
    def update_attempt(attempt_id: str, patch: PracticeAttemptUpdate) -> PracticeAttemptRecord:
        updated = db.update_practice_attempt(attempt_id, patch)
        if not updated:
            raise HTTPException(status_code=404, detail="Practice attempt not found.")
        return updated

    @app.delete("/api/attempts/{attempt_id}")
    def delete_attempt(attempt_id: str) -> Dict[str, bool]:
        ok = db.delete_practice_attempt(attempt_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Practice attempt not found.")
        return {"deleted": True}

    @app.get("/api/weak-areas", response_model=List[WeakAreaRecord])
    def list_weak_areas() -> List[WeakAreaRecord]:
        return db.list_weak_areas()

    @app.post("/api/weak-areas", response_model=WeakAreaRecord)
    def create_weak_area(item: WeakAreaCreate) -> WeakAreaRecord:
        return db.create_weak_area(item)

    # ------------------------------------------------------------------
    # Live Community Presence Tracker (Strict Real Live Sessions Only)
    # ------------------------------------------------------------------
    _active_clients: Dict[str, float] = {}

    @app.post("/api/presence/ping")
    async def presence_ping(request: Request) -> Dict[str, Any]:
        import time
        now = time.time()
        client_id = None
        try:
            body = await request.json()
            if isinstance(body, dict):
                client_id = body.get("client_id")
        except Exception:
            pass

        if not client_id and request.client:
            client_id = request.client.host
        if not client_id:
            client_id = "anon_session"

        _active_clients[str(client_id)] = now

        # Prune inactive sessions older than 75s (heartbeat is every 20s)
        cutoff = now - 75
        expired = [cid for cid, last in _active_clients.items() if last < cutoff]
        for cid in expired:
            _active_clients.pop(cid, None)

        real_count = max(1, len(_active_clients))

        return {
            "live_count": real_count,
            "real_connected": real_count,
            "timestamp": now,
        }

    @app.get("/api/presence")
    async def get_presence(request: Request) -> Dict[str, Any]:
        return await presence_ping(request)

    return app


app = create_app()
