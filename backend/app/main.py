from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from app.core.rag_logic import RAGService
from app.services.document_loader import DocumentLoaderService
from pydantic import BaseModel

app = FastAPI(title="Enterprise RAG Knowledge Assistant")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
rag_service = RAGService()
doc_loader = DocumentLoaderService()

UPLOAD_DIR = "./data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
async def root():
    return {"message": "Enterprise RAG API is running"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads and indexes a document."""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process and index
        chunks = doc_loader.process_file(file_path)
        rag_service.add_documents(chunks)
        
        return {"message": f"Successfully indexed {file.filename}", "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_rag(request: QueryRequest):
    """Answers questions based on indexed documents."""
    try:
        result = rag_service.query(request.question)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
