# Enterprise RAG Knowledge Assistant

A production-ready Retrieval-Augmented Generation (RAG) system built with **FastAPI**, **LangChain**, and **FAISS**, powered by **Groq Cloud API**.

## 🚀 Features

- **Blazing Fast Inference**: Leveraging Groq's LPU™ Inference Engine with Llama 3 models.
- **Local Embeddings**: High-quality text embeddings using HuggingFace `sentence-transformers` (runs locally, no cost).
- **Efficient Vector Search**: FAISS index for high-performance localized document retrieval.
- **Document Support**: Dynamic support for PDF and TXT files.
- **Enterprise Ready**: Full Docker support with data persistence.
- **API Documentation**: Interactive Swagger UI via FastAPI.

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **LLM Orchestration**: LangChain
- **Vector Store**: FAISS
- **Model API**: Groq Cloud (Llama-3.3-70b-versatile)
- **Embeddings**: HuggingFace (all-MiniLM-L6-v2)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose
- Groq API Key (Get it from [Groq Console](https://console.groq.com/keys))

## ⚙️ Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rag
   ```

2. **Configure Environment Variables**:
   Create a `.env` file in the `backend` directory (already pre-configured for your environment):
   ```env
   GROQ_API_KEY=your_groq_api_key
   MODEL_NAME=llama-3.3-70b-versatile
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```

2. **Option A: Run with Docker Compose** (Recommended if Docker is running):
   ```bash
   docker-compose up --build
   ```

2. **Option B: Run Locally** (if Docker is unavailable):
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.main
   ```

## 🔌 API Endpoints

- **GET /**: Health check.
- **POST /upload**: Upload a PDF or TXT file to index it.
- **POST /query**: Ask questions based on the uploaded documents.

### Example Query Request:
```json
{
  "question": "What are the core features of this system?"
}
```

## 🛡️ Architecture

1. **Data Ingestion**: Documents are loaded and split into semantic chunks.
2. **Indexing**: Chunks are converted to vector embeddings and stored in a FAISS index.
3. **Retrieval**: When a query is made, relevant chunks are retrieved from FAISS.
4. **Augmentation**: Context is injected into a specialized prompt for the LLM.
5. **Generation**: Groq API generates a factual response based on the context.

---
*Created as a Portfolio Project for AI Engineering.*
