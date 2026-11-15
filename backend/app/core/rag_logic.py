import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.vector_store_path = os.getenv("VECTOR_STORE_PATH", "./vector_store")
        self.vector_store: Optional[FAISS] = None
        self._load_vector_store()

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        if self.embeddings is None:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            )
        return self.embeddings

    def _get_llm(self, provider: str = "local", api_key: Optional[str] = None, ollama_model: str = "qwen2.5:3b"):
        """Factory method to get the requested LLM."""
        if provider == "local":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=ollama_model,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )

        if provider == "groq":
            return ChatGroq(
                temperature=0,
                model=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
                api_key=api_key or os.getenv("GROQ_API_KEY")
            )

        raise ValueError("Provider must be 'local' or 'groq'.")

    def generate(
        self,
        prompt: str,
        provider: str = "local",
        api_key: Optional[str] = None,
        ollama_model: str = "qwen2.5:3b",
    ) -> str:
        """Generate text without requiring an indexed document collection."""
        response = self._get_llm(provider, api_key, ollama_model).invoke(prompt)
        content = response.content
        if not isinstance(content, str):
            return str(content)
        return content

    def retrieve_context(self, question: str, limit: int = 3) -> dict:
        """Return relevant document excerpts without invoking an LLM."""
        if self.vector_store is None:
            return {"documents": [], "sources": []}

        documents = self.vector_store.similarity_search(question, k=limit)
        return {
            "documents": [
                {
                    "content": document.page_content,
                    "source": document.metadata.get("source", "unknown"),
                }
                for document in documents
            ],
            "sources": list(
                dict.fromkeys(
                    document.metadata.get("source", "unknown")
                    for document in documents
                )
            ),
        }

    def _load_vector_store(self):
        """Loads FAISS vector store if it exists."""
        if os.path.exists(os.path.join(self.vector_store_path, "index.faiss")):
            self.vector_store = FAISS.load_local(
                self.vector_store_path,
                self._get_embeddings(),
                allow_dangerous_deserialization=True
            )
        else:
            self.vector_store = None

    def add_documents(self, chunks):
        """Adds document chunks to the vector store and saves it."""
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(chunks, self._get_embeddings())
        else:
            self.vector_store.add_documents(chunks)
        
        self.vector_store.save_local(self.vector_store_path)

    def get_rag_chain(self, provider: str = "local", api_key: Optional[str] = None, ollama_model: str = "qwen2.5:3b"):
        """Creates and returns the RAG chain."""
        if self.vector_store is None:
            raise ValueError("Vector store is empty. Please upload documents first.")

        llm = self._get_llm(provider, api_key, ollama_model)
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer, just say that you don't know. "
            "Use three sentences maximum and keep the answer concise."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        return create_retrieval_chain(retriever, question_answer_chain)

    def query(self, question: str, provider: str = "local", api_key: Optional[str] = None, ollama_model: str = "qwen2.5:3b"):
        """Query the RAG system."""
        chain = self.get_rag_chain(provider, api_key, ollama_model)
        response = chain.invoke({"input": question})
        return {
            "answer": response["answer"],
            "sources": [doc.metadata.get("source", "unknown") for doc in response["context"]]
        }

    def delete_document(self, filename: str):
        """Removes a document from the FAISS index by source metadata."""
        if self.vector_store:
            docs = list(self.vector_store.docstore._dict.values())
            remaining_chunks = [
                document
                for document in docs
                if document.metadata.get("source") != filename
            ]
            if len(remaining_chunks) == len(docs):
                return
            
            if not remaining_chunks:
                self.vector_store = None
                if os.path.exists(self.vector_store_path):
                    import shutil
                    shutil.rmtree(self.vector_store_path)
            else:
                self.vector_store = FAISS.from_documents(
                    remaining_chunks, self._get_embeddings()
                )
                self.vector_store.save_local(self.vector_store_path)
