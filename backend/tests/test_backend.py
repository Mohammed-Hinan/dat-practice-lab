"""Comprehensive backend & local-LLM wire-protocol test suite for DAT Practice Lab."""

from __future__ import annotations

import base64
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.database import Database
from app.llm_service import validate_local_endpoint
from app.main import create_app
from app.ollama_provider import LLMProviderError
from app.prediction_engine import allocate_categories_mode_a, allocate_categories_mode_b
from app.taxonomy import CATEGORIES


def _make_valid_llm_question(
    category: str,
    title: str,
    scenario: str | None = None,
    time_minutes: int = 30,
) -> str:
    payload = {
        "title": title,
        "category": category,
        "programme_tags": ["Strategic Design Management", "Universal Design"],
        "archetypes": ["Problem identification", "Human-centred design"],
        "competencies": ["Observation", "Empathy", "Problem framing", "Visual communication"],
        "difficulty": "Medium",
        "time_minutes": time_minutes,
        "total_marks": 20,
        "scenario": scenario
        or (
            f"At a busy suburban railway foot-over-bridge during evening peak hours ({title}), "
            "commuters carrying heavy bags, elderly passengers, and street hawkers share a narrow "
            "wet staircase with poor signage and erratic lighting."
        ),
        "subquestions": [
            {
                "label": "A",
                "instruction": "Identify five distinct usability, safety, or communication problems affecting different stakeholders in this space.",
                "marks": 10,
                "deliverables": ["Five numbered observations", "Brief stakeholder mapping"],
            },
            {
                "label": "B",
                "instruction": "Select the most urgent problem, justify your prioritisation, and sketch a practical low-maintenance intervention.",
                "marks": 10,
                "deliverables": ["One annotated sketch", "Short implementation rationale"],
            },
        ],
        "constraints": [
            "Intervention must not require structural demolition",
            "Must work during power outages",
        ],
        "sketching_requirements": [
            "Include at least one perspective or cutaway annotated sketch showing human scale"
        ],
        "visual_sketch_prompt": "eye-level 1-point perspective of suburban Indian railway footbridge during rain, commuters holding umbrellas, elderly passenger gripping handrail",
        "evaluation_rubric": [
            {"criterion": "Depth of observation & stakeholder empathy", "marks": 5},
            {"criterion": "Prioritisation logic & problem framing", "marks": 5},
            {"criterion": "Practicality & constraint sensitivity", "marks": 5},
            {"criterion": "Clarity of visual & written communication", "marks": 5},
        ],
        "practice_priority": 4,
        "priority_reason": "Addresses recurring public-infrastructure and inclusive design competencies.",
        "prediction_confidence": "Low",
        "historical_pattern_references": [],
        "suggested_time_split": [
            {"activity": "Understand scenario & stakeholders", "minutes": 4},
            {"activity": "Identify & prioritise issues", "minutes": 6},
            {"activity": "Sketch & annotate intervention", "minutes": 15},
            {"activity": "Refine & verify constraints", "minutes": max(1, time_minutes - 25)},
        ],
    }
    return json.dumps(payload)


def _extract_requested_category(user_prompt: str) -> str:
    for c in CATEGORIES:
        if f"Required Category (exact string): {c}" in user_prompt:
            return c
    return "Design aptitude"


def _start_local_mock_server(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_local_endpoint_guard_blocks_cloud_apis():
    assert validate_local_endpoint("http://localhost:11434") == "http://localhost:11434"
    assert validate_local_endpoint("http://127.0.0.1:1234/v1") == "http://127.0.0.1:1234/v1"
    with pytest.raises(LLMProviderError):
        validate_local_endpoint("ftp://invalid.endpoint.internal")
    with pytest.raises(LLMProviderError):
        validate_local_endpoint("not_a_valid_url")


def test_mode_a_all_seven_categories_and_multi_category():
    allocated_all = allocate_categories_mode_a(list(CATEGORIES), len(CATEGORIES))
    assert len(allocated_all) == len(CATEGORIES)
    assert set(allocated_all) == set(CATEGORIES)
    assert "Logos, Symbols & Signs" in allocated_all

    allocated_two = allocate_categories_mode_a(["Problem identification", "Design aptitude"], 4)
    assert len(allocated_two) == 4
    assert allocated_two.count("Problem identification") == 2
    assert allocated_two.count("Design aptitude") == 2


def test_mode_b_completely_balanced_distribution():
    allocated = allocate_categories_mode_b(len(CATEGORIES), "completely_balanced", [])
    assert len(allocated) == len(CATEGORIES)
    assert set(allocated) == set(CATEGORIES)


def test_empty_historical_bank_produces_low_confidence_warning(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    client = TestClient(create_app(db_instance=db))

    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["confidence_level"] == "Low"
    assert data["low_confidence_warning"] is not None
    assert "No historical NID M.Des questions" in data["low_confidence_warning"]
    assert data["dataset_summary"]["total_records"] == 0


def test_historical_bulk_csv_json_import_edit_and_prediction_scoring(tmp_path: Path):
    db = Database(tmp_path / "hist.db")
    client = TestClient(create_app(db_instance=db))

    # 1. CSV import with unknown year & marks preserved as None
    csv_text = (
        "title,prompt_text,year,category,programme_tags,marks,source\n"
        "Monsoon Commuter Shelter,Observe commuters waiting at a rain-swept bus stop and identify 5 problems then sketch an intervention.,2024,Problem identification,Universal Design; Strategic Design Management,20,Past Paper\n"
        "Wordless Tea Stall Story,Create a 5-frame storyboard without dialogue showing a stray dog helping an elderly vendor at a railway tea stall.,,Storyboard,Animation Film Design,,Memory Recall\n"
        "Bamboo Kitchen Organizer,Explain three properties of split bamboo and redesign a compact spice rack for small urban kitchens.,2023,Product sketch,Product Design,25,Archive\n"
    )
    parse_csv = client.post("/api/historical/parse", json={"format": "csv", "content": csv_text})
    assert parse_csv.status_code == 200
    drafts = parse_csv.json()["drafts"]
    assert len(drafts) == 3
    assert drafts[1]["year"] is None
    assert drafts[1]["marks"] is None
    saved_csv = client.post("/api/historical/import", json={"questions": drafts}).json()
    assert len(saved_csv) == 3

    # 2. Bulk text import with inline tags
    bulk_text = (
        "[2022] [Category: Composition] Design a wordless civic poster raising awareness about water conservation in apartment complexes.\n\n"
        "[2021] Redesign a foldable walking cane for elderly commuters navigating crowded metro stations."
    )
    parse_txt = client.post("/api/historical/parse", json={"format": "text", "content": bulk_text})
    assert parse_txt.status_code == 200
    txt_drafts = parse_txt.json()["drafts"]
    assert len(txt_drafts) == 2
    assert txt_drafts[0]["year"] == 2022
    assert txt_drafts[0]["category"] == "Composition"
    client.post("/api/historical/import", json={"questions": txt_drafts})

    # 3. JSON import to reach >= 10 dated questions across >= 3 years -> Medium confidence
    json_items = [
        {
            "prompt_text": f"Analyse everyday accessibility and public infrastructure friction in a civic facility variant {i}, identify 5 issues and sketch an inclusive service kiosk.",
            "year": 2020 + (i % 5),
            "category": CATEGORIES[i % len(CATEGORIES)],
            "programme_tags": ["Universal Design", "Strategic Design Management"],
            "marks": 20,
            "source": "Verified Compilation",
        }
        for i in range(8)
    ]
    parse_json = client.post(
        "/api/historical/parse",
        json={"format": "json", "content": json.dumps(json_items)},
    )
    assert parse_json.status_code == 200
    client.post("/api/historical/import", json={"questions": parse_json.json()["drafts"]})

    # Edit one record
    edit_res = client.put(
        f"/api/historical/{saved_csv[1]['id']}",
        json={"notes": "Verified from student notebook"},
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["notes"] == "Verified from student notebook"

    # Verify CSV export
    exp = client.get("/api/historical/export?format=csv")
    assert exp.status_code == 200
    assert "Monsoon Commuter Shelter" in exp.text

    # Analytics reflects 13 records across 5 distinct years -> Medium confidence, non-zero scores
    ana = client.get("/api/analytics/overview").json()
    assert ana["dataset_summary"]["total_records"] == 13
    assert ana["dataset_summary"]["distinct_years"] >= 4
    assert ana["confidence_level"] in ("Medium", "High")
    assert ana["theme_priorities"][0]["practice_priority_score"] > 50


def test_real_http_ollama_and_lmstudio_wire_protocols_plus_originality_retry(tmp_path: Path):
    """Spins up real local HTTP servers speaking Ollama and OpenAI/LM Studio JSON protocols."""
    ollama_state = {"chat_calls": 0}

    class OllamaMockHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path == "/api/tags":
                body = json.dumps({"models": [{"name": "qwen2.5:7b"}, {"name": "llama3.1:8b"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length).decode())
            if self.path == "/api/chat":
                ollama_state["chat_calls"] += 1
                n = ollama_state["chat_calls"]
                user_msg = req["messages"][1]["content"]
                cat = _extract_requested_category(user_msg)
                # Call 1 returns invalid JSON to verify schema retry
                if n == 1:
                    content = "{ broken json not valid"
                # Call 3 deliberately duplicates Call 2 to verify originality retry!
                elif n == 3:
                    content = _make_valid_llm_question(
                        cat,
                        "Monsoon Railway Footbridge Audit",
                        scenario="Commuters and elderly passengers navigating a wet suburban railway footbridge with erratic lighting and hawker stalls blocking stairs.",
                    )
                else:
                    unique_scenarios = [
                        f"A rural primary health centre vaccination morning ({n}) where multilingual mothers, nurses, and cold-chain staff coordinate under limited shade.",
                        f"A compact urban hostel laundry terrace ({n}) shared by 60 design students during humid monsoon weeks with limited drying space.",
                        f"A heritage terracotta artisan workshop ({n}) adapting traditional clay cooling vessels for modern small-apartment balconies.",
                        f"A night-shift interstate bus terminal canteen ({n}) serving drowsy travellers, drivers, and elderly passengers with zero digital signage.",
                        f"A crowded municipal public library children's reading corner ({n}) transitioning between quiet study and tactile storytelling sessions.",
                        f"An electric cargo tricycle fleet ({n}) delivering fragile glass milk bottles through narrow historic lanes at dawn.",
                        f"A coastal fishermen's dry-dock repair yard ({n}) repurposing discarded nylon nets into modular community shade structures.",
                        f"A steep hill-station school walkway ({n}) navigated daily by young children carrying heavy schoolbags in fog and rain.",
                        f"A busy city flower market auction yard ({n}) at 5 AM managing perishable marigold crates, wet stone floors, and handcart traffic.",
                        f"A neighbourhood tailoring collective ({n}) sorting fabric offcuts into durable school pouches without industrial machinery.",
                    ]
                    title = "Monsoon Railway Footbridge Audit" if n == 2 else f"Original NID Challenge #{n} ({cat})"
                    scen = (
                        "Commuters and elderly passengers navigating a wet suburban railway footbridge with erratic lighting and hawker stalls blocking stairs."
                        if n == 2
                        else unique_scenarios[n % len(unique_scenarios)]
                    )
                    content = _make_valid_llm_question(cat, title, scenario=scen)

                resp = json.dumps({"message": {"role": "assistant", "content": content}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)
                return
            self.send_response(404)
            self.end_headers()

    class LMStudioMockHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path == "/v1/models":
                body = json.dumps({"data": [{"id": "qwen2.5-7b-instruct"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length).decode())
            if self.path == "/v1/chat/completions":
                user_msg = req["messages"][1]["content"]
                cat = _extract_requested_category(user_msg)
                content = _make_valid_llm_question(
                    cat,
                    f"LM Studio {cat} Examination Prompt",
                    scenario="Inside a quiet regional botanical conservatory, a visiting illustrator drops a sketchbook into a koi pond while a caretaker watches.",
                )
                resp = json.dumps(
                    {"choices": [{"message": {"role": "assistant", "content": content}}]}
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)
                return
            self.send_response(404)
            self.end_headers()

    ollama_srv, ollama_port = _start_local_mock_server(OllamaMockHandler)
    lms_srv, lms_port = _start_local_mock_server(LMStudioMockHandler)

    try:
        db = Database(tmp_path / "wire.db")
        client = TestClient(create_app(db_instance=db))

        # Configure real localhost ports for Ollama and LM Studio
        cfg = client.get("/api/settings").json()
        cfg["provider"] = "ollama"
        cfg["ollama_base_url"] = f"http://127.0.0.1:{ollama_port}"
        cfg["lmstudio_base_url"] = f"http://127.0.0.1:{lms_port}/v1"
        cfg["model"] = "qwen2.5:7b"
        client.put("/api/settings", json=cfg)

        # 1. Verify Ollama discovery over real HTTP
        st_ol = client.post("/api/llm/test", json={"provider": "ollama"}).json()
        assert st_ol["connected"] is True
        assert "qwen2.5:7b" in st_ol["models"]

        # 2. Verify LM Studio discovery over real HTTP
        st_lm = client.post("/api/llm/test", json={"provider": "lmstudio"}).json()
        assert st_lm["connected"] is True
        assert "qwen2.5-7b-instruct" in st_lm["models"]

        # 3. Generate 2 questions: Call 1 triggers JSON retry, Call 2 saves title,
        #    Call 3 duplicates Call 2 -> triggers originality retry -> Call 4 returns unique question!
        gen2 = client.post(
            "/api/questions/generate",
            json={
                "mode": "category",
                "categories": ["Problem identification", "Product sketch"],
                "count": 2,
                "time_minutes": 30,
            },
        )
        assert gen2.status_code == 200
        qs = gen2.json()["questions"]
        assert len(qs) == 2
        assert qs[0]["title"] != qs[1]["title"]
        assert ollama_state["chat_calls"] == 4  # 1 broken JSON + 1 valid + 1 duplicate rejected + 1 original!

        # 4. Generate all categories (including Logos, Symbols & Signs) via Mode A
        gen_all = client.post(
            "/api/questions/generate",
            json={"mode": "category", "categories": list(CATEGORIES), "count": len(CATEGORIES), "time_minutes": 20},
        )
        assert gen_all.status_code == 200
        assert {q["category"] for q in gen_all.json()["questions"]} == set(CATEGORIES)

        # 5. Generate complete 3-question Exam Simulator paper
        exam = client.post(
            "/api/exams/generate",
            json={
                "num_questions": 3,
                "total_time_minutes": 90,
                "difficulty": "Mixed",
                "category_distribution": "balanced",
                "paper_strategy": "prediction_oriented",
                "historical_relevance": "high",
            },
        )
        assert exam.status_code == 200
        paper = exam.json()
        assert len(paper["questions"]) == 3
        assert sum(q["time_minutes"] for q in paper["questions"]) == 90

        # 6. Switch to LM Studio and generate a Storyboard prompt over real HTTP
        cfg["provider"] = "lmstudio"
        cfg["model"] = "qwen2.5-7b-instruct"
        client.put("/api/settings", json=cfg)
        lm_res = client.post(
            "/api/questions/generate",
            json={"mode": "category", "categories": ["Storyboard"], "count": 1, "time_minutes": 30},
        )
        assert lm_res.status_code == 200
        assert lm_res.json()["questions"][0]["provider_used"] == "lmstudio"
        assert lm_res.json()["questions"][0]["category"] == "Storyboard"
    finally:
        ollama_srv.shutdown()
        lms_srv.shutdown()


def test_persistence_across_restart_for_practice_history(tmp_path: Path):
    db_file = tmp_path / "persist.db"
    c1 = TestClient(create_app(db_instance=Database(db_file)))

    create = c1.post(
        "/api/attempts",
        json={
            "question_title": "Hospital OPD Wayfinding Challenge",
            "category": "Problem identification",
            "programme_tags": ["Information Design"],
            "time_allocated_minutes": 30,
            "time_spent_seconds": 1620,
            "self_difficulty": "Medium",
            "status": "completed",
            "notes": "Finished sketch on time",
            "rubric_revealed": True,
        },
    )
    assert create.status_code == 200

    # Re-instantiate with same SQLite file to verify persistence after restart
    c2 = TestClient(create_app(db_instance=Database(db_file)))
    attempts = c2.get("/api/attempts").json()
    assert len(attempts) == 1
    assert attempts[0]["question_title"] == "Hospital OPD Wayfinding Challenge"
    assert attempts[0]["time_spent_seconds"] == 1620


def test_offline_usability_when_llm_disconnected(tmp_path: Path):
    db = Database(tmp_path / "offline.db")
    client = TestClient(create_app(db_instance=db))

    settings = client.get("/api/settings").json()
    settings["provider"] = "ollama"
    settings["ollama_base_url"] = "http://127.0.0.1:19999"
    settings["model"] = "qwen2.5:7b"
    client.put("/api/settings", json=settings)

    status = client.get("/api/llm/status").json()
    assert status["connected"] is False

    gen = client.post("/api/questions/generate", json={"mode": "balanced_random", "count": 1})
    assert gen.status_code == 503
    assert "offline" in gen.json()["detail"].lower() or "unreachable" in gen.json()["detail"].lower()

    assert client.get("/api/dashboard").status_code == 200
    assert client.get("/api/historical").status_code == 200
    assert client.get("/api/attempts").status_code == 200
    assert client.get("/api/analytics/overview").status_code == 200


def test_drawthings_http_sketch_generation_and_serving(tmp_path: Path):
    import base64

    # Minimal valid 1x1 PNG bytes
    tiny_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    tiny_b64 = base64.b64encode(tiny_png).decode()

    class DrawThingsMockHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path == "/sdapi/v1/options":
                body = json.dumps({"model": "dreamshaper_v8_f16.ckpt"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode())
            if self.path in ("/sdapi/v1/txt2img", "/sdapi/v1/img2img"):
                if self.path == "/sdapi/v1/img2img" and "init_images" in payload:
                    init_b64 = payload["init_images"][0]
                    img = Image.open(io.BytesIO(base64.b64decode(init_b64)))
                    expected_h = payload.get("height")
                    if img.height != expected_h:
                        self.send_response(422)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({
                                "error": "HTTPException",
                                "detail": f"init_images height doesn't match {img.height} from the parameter {expected_h}",
                            }).encode()
                        )
                        return
                body = json.dumps({"images": [tiny_b64]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

    srv, port = _start_local_mock_server(DrawThingsMockHandler)
    try:
        db = Database(tmp_path / "dt.db")
        app = create_app(db_instance=db)
        app.state.drawthings_service.sketches_dir = tmp_path / "sketches"
        app.state.drawthings_service.sketches_dir.mkdir(parents=True, exist_ok=True)
        client = TestClient(app)

        cfg = client.get("/api/settings").json()
        cfg["drawthings_base_url"] = f"http://127.0.0.1:{port}"
        cfg["auto_unload_llm_for_sketch"] = False
        cfg["sketch_provider"] = "drawthings"
        client.put("/api/settings", json=cfg)

        st = client.get("/api/drawthings/status").json()
        assert st["connected"] is True
        assert st["active_model"] == "dreamshaper_v8_f16.ckpt"

        gen = client.post(
            "/api/drawthings/generate",
            json={
                "prompt": "foldable bamboo spice rack for compact urban kitchen",
                "style_preset": "product_sketch",
            },
        )
        assert gen.status_code == 200
        data = gen.json()
        assert data["mode"] == "txt2img"
        assert data["image_url"].startswith("/api/sketches/sketch_")

        img_resp = client.get(data["image_url"])
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"] == "image/png"

        # Verify NID / CEED / UCEED Master System Prompt & structured positive/negative prompt crafting
        ess = client.get("/api/drawthings/essence")
        assert ess.status_code == 200
        ess_data = ess.json()
        assert len(ess_data["essence_pillars"]) >= 5
        assert "nid / ceed / uceed visual answer generator" in ess_data["system_prompt"].lower()
        assert "observational_pencil" in ess_data["style_presets"]

        crafted = client.post(
            "/api/drawthings/craft-prompt",
            json={
                "title": "Corner Tea Stall",
                "scenario": "A lively roadside tea stall at dusk with a vendor pouring hot chai into glasses while commuters wait.",
                "category": "Drawing",
                "time_minutes": 20,
                "style_preset": "observational_pencil",
            },
        )
        assert crafted.status_code == 200
        cdata = crafted.json()
        assert len(cdata["visual_sketch_prompt"]) >= 20
        assert "photorealism" in cdata["visual_negative_prompt"].lower()
        assert "spec sheet" in cdata["visual_negative_prompt"].lower()

        # Verify strict diffusion prompt firewall strips photo/table/gibberish triggers even on raw user input
        fw_gen = client.post(
            "/api/drawthings/generate",
            json={
                "prompt": "Hand-drawn NID M.Des examination answer sheet with realistic handwritten annotations achievable in 20 minutes showing a foldable bamboo spice rack",
                "style_preset": "product_sketch",
            },
        )
        assert fw_gen.status_code == 200
        fw_data = fw_gen.json()
        assert fw_data["prompt_used"].startswith("Industrial design pencil sketch of")
        assert "examination answer sheet" not in fw_data["prompt_used"].lower()
        assert "annotations" not in fw_data["prompt_used"].lower()
        assert "20 minutes" not in fw_data["prompt_used"].lower()
        assert "bamboo spice rack" in fw_data["prompt_used"].lower()
        assert "grayscale photo" in fw_data["negative_prompt_used"].lower()

        # Test img2img with an un-normalized 1024x1024 paper sketch upload (verifying no 422 error occurs)
        dummy_1024 = Image.new("RGB", (1024, 1024), color=(240, 240, 240))
        d_buf = io.BytesIO()
        dummy_1024.save(d_buf, format="JPEG")
        dummy_b64 = "data:image/jpeg;base64," + base64.b64encode(d_buf.getvalue()).decode("utf-8")

        img2img_res = client.post(
            "/api/drawthings/generate",
            json={
                "prompt": "clean ergonomic pencil sketch of water bottle",
                "style_preset": "product_sketch",
                "init_image_base64": dummy_b64,
                "denoising_strength": 0.55,
            },
        )
        assert img2img_res.status_code == 200
        i2i_data = img2img_res.json()
        assert i2i_data["mode"] == "img2img"
        # 1024x1024 was auto-scaled to 640x640 (preserving aspect ratio and multiples of 64 within M1 memory budget)
        assert i2i_data["width"] == 640
        assert i2i_data["height"] == 640

        # Verify comparative learning study was conducted on uploaded sketch
        assert i2i_data["learned_analysis"] is not None
        assert len(i2i_data["learned_analysis"]["what_changed"]) >= 15
        assert len(i2i_data["learned_analysis"]["why_changed"]) >= 15
        assert len(i2i_data["learned_analysis"]["actionable_guidelines"]) >= 10

        # Verify rule was persisted to SQLite visual_learning_memory
        lr_res = client.get("/api/drawthings/learned-rules?category=Product+sketch")
        assert lr_res.status_code == 200
        l_rules = lr_res.json()
        assert len(l_rules) >= 1
        assert l_rules[0]["category"] == "Product sketch"

        # Verify a subsequent prompt craft for Product sketch automatically applies this learned rule!
        next_craft = client.post(
            "/api/drawthings/craft-prompt",
            json={
                "title": "Ergonomic Handheld Juicer",
                "scenario": "A manual citrus juicer for street stalls with comfortable grip.",
                "category": "Product sketch",
                "time_minutes": 20,
                "style_preset": "product_sketch",
            },
        )
        assert next_craft.status_code == 200
        nc_data = next_craft.json()
        assert len(nc_data["applied_rules"]) >= 1
        assert "learned from" in nc_data["applied_rules"][0]
    finally:
        srv.shutdown()
