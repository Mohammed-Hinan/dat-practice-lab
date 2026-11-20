# DAT Practice Lab — Local AI-Powered NID M.Des Exam Preparation

**DAT Practice Lab** is a local-first web application built to prepare candidates for the **NID M.Des DAT Prelims** examination (2027 admission cycle). It connects exclusively to locally hosted Large Language Models (**Ollama**, **LM Studio**, or any **custom local OpenAI-compatible endpoint**), generates original examination-grade questions across all seven categories, persists practice history and historical question banks locally in SQLite, and provides transparent practice-priority analytics.

---

## Key Capabilities

- **Authentic NID M.Des Prompt Engine**: Generates original, context-rich, constraint-driven questions combining 10 core archetypes (A–J) across all 7 categories (`Composition`, `Creativity`, `Design aptitude`, `Drawing`, `Problem identification`, `Product sketch`, `Storyboard`) and 20 official NID M.Des programme tags.
- **Four Practice Modes**:
  - **Mode A — Category Practice**: Single, multi-category, or all 7 categories (guaranteeing at least 1 question per category when all 7 are selected — never skewed by external website tag counts).
  - **Mode B — Balanced Random Practice**: Equal 1/7 probability or adjustable weighted practice.
  - **Mode C — Likely Exam Practice**: Transparent, configurable practice-priority scoring (default: 30% multi-year recurrence, 20% recency, 20% cross-relevance, 15% preparation profile fit, 15% student practice gaps) with explicit separation between **Historical Evidence** and **Model Interpretation**, plus explicit **Low-Confidence Warnings** when historical data is sparse.
  - **Mode D — Exam Simulator**: Timed multi-question mock papers (default 30 min/question, configurable total time) with post-submission rubric unlock and print support.
- **Preparation Profiles**: Multi-select profiles for **NID Gandhinagar — Strategic Design Management**, **NID Haryana — Creative Leadership** *(user-defined preparation profile)*, and **General NID M.Des preparation**.
- **Historical Question Bank**: Manual entry, bulk text, CSV, and JSON import with pre-save review of auto-assigned categories. Unknown years, marks, and sources are preserved as `Unknown` rather than fabricated.
- **Strict Local-Only Privacy & Offline Resilience**: Backend proxy avoids browser CORS issues, blocks external cloud LLM endpoints, never transmits user data externally, and remains fully usable offline for saved questions, historical banks, trends, and practice history when the local model server is stopped.

---

## Prerequisites

- **Python 3.10+** (tested with Python 3.15)
- **Node.js 20+** and **npm 10+**
- At least one local LLM runtime:
  - **[Ollama](https://ollama.com/)** (recommended), **or**
  - **[LM Studio](https://lmstudio.ai/)**, **or**
  - Any local OpenAI-compatible server (`llama.cpp` server, `vLLM`, `LocalAI`, etc.)

---

## Installation Instructions

### 1. Backend Setup (FastAPI + SQLite)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Frontend Setup (React + TypeScript + Vite + Tailwind CSS)

```bash
cd frontend
npm install
```

---

## Local LLM Setup

### Option A — Ollama Setup (Default)

1. Install Ollama from [ollama.com](https://ollama.com/) or via Homebrew on macOS:
   ```bash
   brew install ollama
   ```
2. Start the Ollama server:
   ```bash
   ollama serve
   ```
3. Pull an instruction-following model that handles structured JSON cleanly (e.g., 7B–14B quantized):
   ```bash
   ollama pull qwen2.5:7b
   # Alternatives:
   # ollama pull llama3.1:8b
   # ollama pull mistral:7b
   # ollama pull qwen2.5:14b
   ```
4. Default endpoints used by DAT Practice Lab:
   - Base URL: `http://localhost:11434`
   - Chat endpoint: `http://localhost:11434/api/chat`
   - Model discovery: `http://localhost:11434/api/tags`

### Option B — LM Studio Setup

1. Install and open **[LM Studio](https://lmstudio.ai/)**.
2. Download and load an instruct model (e.g., `Qwen2.5-7B-Instruct` or `Llama-3.1-8B-Instruct`).
3. Open the **Developer** tab and click **Start Server** (defaults to port `1234`).
4. Default endpoints used by DAT Practice Lab:
   - Base URL: `http://localhost:1234/v1`
   - Chat endpoint: `http://localhost:1234/v1/chat/completions`
   - Model discovery: `http://localhost:1234/v1/models`

### Option C — Custom Local OpenAI-Compatible Server

In **Settings**, select **Custom OpenAI-Compatible**, enter your local base URL (for example `http://localhost:8001/v1`), optionally provide a local bearer token if required, and click **Test & Discover**.

---

## How to Run the Application

### Quick Start (Both Backend & Frontend)

```bash
chmod +x start.sh
./start.sh
```

Then open **http://localhost:5173** in your browser.

### Manual Two-Terminal Start

**Terminal 1 — Backend (port 8000):**
```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend (port 5173):**
```bash
cd frontend
npm run dev
```

---

## How to Configure Your Local Model

1. Open **Settings** from the left navigation rail.
2. Choose **Ollama**, **LM Studio**, or **Custom OpenAI-Compatible**.
3. Click **Test & Discover** to check connection latency and populate available local models.
4. Select your preferred model from the discovered dropdown (or type a model identifier manually).
5. Adjust **Temperature** (default `0.75`), **Max Output Tokens** (default `2400`), **Preparation Profiles**, and **Practice-Priority Scoring Weights** (default `30 / 20 / 20 / 15 / 15`).
6. Click **Save Settings**.

---

## How to Import Historical Question Data

DAT Practice Lab starts with an honest empty historical bank so it never invents past NID examination years or statistics.

1. Open **Question Bank** in the left navigation rail.
2. Choose **Manual Entry** to enter individual prompts, or **Bulk / CSV / JSON Import**.
3. For **Bulk Text**, separate questions with a blank line or `---`. You may include optional inline metadata tags such as `[2024] [Category: Storyboard] [Marks: 20] [Time: 30]`.
4. For **CSV** or **JSON**, you can upload a file or paste content directly. Sample format templates are provided in:
   - `data/sample_import_template.csv`
   - `data/sample_import_template.json`
5. Click **Parse & Review Assignments** to verify auto-suggested categories and metadata before saving to SQLite (`data/dat_practice_lab.db`).

---

## Running Automated Tests

```bash
cd backend
.venv/bin/pytest -v
```

Frontend type-check and production build:
```bash
cd frontend
npm run build
```

---

## Project Architecture

```text
dat-practice-lab/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI REST endpoints
│   │   ├── database.py              # SQLite persistence layer
│   │   ├── schemas.py               # Strict Pydantic v2 schemas
│   │   ├── taxonomy.py              # 7 categories, 20 programmes, 10 archetypes, 3 profiles
│   │   ├── ollama_provider.py       # Ollama local HTTP client
│   │   ├── lmstudio_provider.py     # LM Studio & OpenAI-compatible local client
│   │   ├── llm_service.py           # Local-only guard, discovery & JSON retry loop
│   │   ├── question_generator.py    # Prompt engine (Modes A, B, C, D) + originality check
│   │   ├── historical_analyser.py   # Transparent historical analytics & auto-classifier
│   │   ├── prediction_engine.py     # Configurable 5-factor practice-priority scoring
│   │   └── question_bank.py         # Manual, bulk text, CSV & JSON parsers/exporters
│   └── tests/test_backend.py        # Pytest suite including live local HTTP wire tests
├── frontend/
│   └── src/
│       ├── App.tsx                  # Minimal editorial navigation shell
│       ├── api.ts & types.ts        # Typed API client
│       └── components/
│           ├── Dashboard.tsx
│           ├── QuestionGenerator.tsx
│           ├── QuestionDisplay.tsx  # Exam-paper view, timer, gated rubric, debug drawer
│           ├── ExamSimulator.tsx
│           ├── QuestionBank.tsx
│           ├── TrendAnalytics.tsx
│           ├── PracticeHistory.tsx
│           └── Settings.tsx
├── data/                            # Local SQLite database + import templates
└── start.sh                         # One-command launcher
```
