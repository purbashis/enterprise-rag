import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

class DocumentLoaderService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def load_document(self, file_path: str) -> List:
        """Loads a document and returns its content as a list of LangChain documents."""
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif ext == '.txt':
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        return loader.load()

    def split_documents(self, documents: List) -> List:
        """Splits a list of documents into smaller chunks."""
        return self.text_splitter.split_documents(documents)

    def process_file(self, file_path: str) -> List:
        """Complete workflow: load and split."""
        docs = self.load_document(file_path)
        return self.split_documents(docs)
