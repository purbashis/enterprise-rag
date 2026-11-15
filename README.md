# Fieldwork — Local-First AI Research Agents

A compact portfolio project for goal-directed research workflows. A coordinator
combines document retrieval, persistent memory, free web search and optional
read-only public API calls, then asks a free model to synthesize the evidence.

## Architecture

```text
TypeScript + Vite UI
        │
        ▼
FastAPI coordinator ── SQLite memory
        ├───────────── FAISS + local sentence-transformer embeddings
        ├───────────── DuckDuckGo HTML search
        ├───────────── read-only public API tool
        └───────────── Ollama (local) or optional Groq free tier
```

The project intentionally uses one application container and existing modules
instead of a large microservice fleet. SQLite, FAISS, embeddings and Ollama run
locally at no model/API cost. Groq is optional and requires a free-tier key;
availability and quotas depend on Groq's current terms.

## Run locally

Requirements: Python 3.12+, Node.js 24+, and optionally [Ollama](https://ollama.com/).

```powershell
# Terminal 1: backend
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. For local inference, install Ollama and pull the
small default model:

```powershell
ollama pull qwen2.5:3b
```

Choose **Groq** in the UI to use its optional free tier. The key is sent only
with the current request and is not stored by the app.

## Run with Docker

```powershell
docker compose up --build
```

Open `http://localhost:8000`. Uploaded files, the FAISS index and SQLite memory
are persisted under `backend/data` and `backend/vector_store`. Ollama can run on
the host and is reachable by the container at `host.docker.internal:11434`.
Set `GROQ_API_KEY` in the shell before starting Compose to enable Groq.

## Agent workflow

`POST /agent/run` executes a bounded sequence:

1. Search persistent memory for related work.
2. Retrieve matching document chunks when files are indexed.
3. Optionally search DuckDuckGo.
4. Optionally call an allowlisted, read-only public API.
5. Synthesize the available evidence with the selected free model and save the
   result to SQLite memory.

API calls are HTTPS GET only and limited to `api.github.com`,
`api.open-meteo.com`, and `jsonplaceholder.typicode.com`. This is deliberate:
the backend must not become an unrestricted network proxy. PDF and TXT uploads
are limited to 20 MB.

Interactive API reference: `http://localhost:8000/docs`.

### FAISS import error

Install dependencies and launch the backend with the same interpreter. For
example, from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Check that interpreter with
`.\.venv\Scripts\python.exe -c "import faiss; print(faiss.__version__)"`.
Installing FAISS into a different Python/Conda environment will not make it
available to the running server.

## Deployment notes

The Docker image serves the built UI and API together and can be placed behind
an external load balancer. An AWS Application Load Balancer is **not free** and
costs extra; high availability also requires shared durable storage for uploads,
FAISS and memory. This local SQLite/FAISS setup is a portfolio/demo architecture,
not a multi-replica production data plane. Do not claim AWS HA unless those paid
infrastructure components have actually been provisioned and tested.
