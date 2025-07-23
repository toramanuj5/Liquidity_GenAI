from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

class EmbeddingManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50
        )

    def create_index(self, text: str, index_path: str = "data/faiss_index"):
        """Generate FAISS index from text"""
        chunks = self.splitter.split_text(text)
        vectorstore = FAISS.from_texts(chunks, self.embeddings)
        
        # Save index
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        vectorstore.save_local(index_path)
        return vectorstore

    def load_index(self, index_path: str = "data/faiss_index"):
        """Load existing FAISS index"""
        return FAISS.load_local(index_path, self.embeddings)