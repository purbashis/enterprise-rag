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
        self.embeddings = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        self.vector_store_path = os.getenv("VECTOR_STORE_PATH", "./vector_store")
        self.vector_store: Optional[FAISS] = None
        self._load_vector_store()

    def _get_llm(self, provider: str = "groq", api_key: Optional[str] = None, ollama_model: str = "mistral"):
        """Factory method to get the requested LLM."""
        if provider == "local":
            # Assuming Ollama is running locally
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(model=ollama_model, base_url="http://localhost:11434")
        
        elif provider == "custom":
            if not api_key:
                raise ValueError("Custom API key is required.")
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=api_key,
                model="gpt-3.5-turbo", # Default or allow configuration
                temperature=0
            )

        else: # Default: Groq
            return ChatGroq(
                temperature=0,
                model_name=os.getenv("MODEL_NAME", "llama-3.3-70b-versatile"),
                api_key=api_key or os.getenv("GROQ_API_KEY")
            )

    def _load_vector_store(self):
        """Loads FAISS vector store if it exists."""
        if os.path.exists(os.path.join(self.vector_store_path, "index.faiss")):
            self.vector_store = FAISS.load_local(
                self.vector_store_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
        else:
            self.vector_store = None

    def add_documents(self, chunks):
        """Adds document chunks to the vector store and saves it."""
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        else:
            self.vector_store.add_documents(chunks)
        
        self.vector_store.save_local(self.vector_store_path)

    def get_rag_chain(self, provider: str = "groq", api_key: Optional[str] = None, ollama_model: str = "mistral"):
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

    def query(self, question: str, provider: str = "groq", api_key: Optional[str] = None, ollama_model: str = "mistral"):
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
            # Note: FAISS doesn't directly support deleting by metadata easily in all versions.
            # A common workaround is to recreate the index excluding the target source.
            docs = self.vector_store.docstore._dict.values()
            remaining_chunks = [d for d in docs if d.metadata.get("source") != filename]
            
            if not remaining_chunks:
                self.vector_store = None
                if os.path.exists(self.vector_store_path):
                    import shutil
                    shutil.rmtree(self.vector_store_path)
            else:
                self.vector_store = FAISS.from_documents(remaining_chunks, self.embeddings)
                self.vector_store.save_local(self.vector_store_path)
