from langchain_pipeline.pdf_loader import load_and_split_pdf
from langchain_pipeline.embedder import get_embedder
from langchain_pipeline.vector_store import save_to_faiss

embedder = get_embedder()
chunks = load_and_split_pdf("data/basel3_final.pdf")
save_to_faiss(chunks, embedder)
