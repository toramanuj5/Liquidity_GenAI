# backend/app/router.py

from fastapi import APIRouter, UploadFile, File
import os

from langchain_community.document_loaders import PyPDFLoader
#from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from pydantic import BaseModel
from app.qa_engine import get_qa_chain
from app.feedback_log import log_feedback

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    
    temp_pdf_path = f"/app/data/{file.filename}"
    with open(temp_pdf_path, "wb") as f:
        f.write(contents)

    # Load PDF
    loader = PyPDFLoader(temp_pdf_path)
    documents = loader.load()

    # Split text
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Embed using HuggingFace
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Extract text and metadata for FAISS
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    from langchain_community.vectorstores import FAISS
    vectorstore = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)

    # Save to local disk
    vectorstore.save_local("/app/vector_store")

    return {"message": f"{file.filename} processed and stored."}

class QueryRequest(BaseModel):
    question: str
    source: str | None = None

@router.post("/query")
async def query_pdf(request: QueryRequest):
    chain = get_qa_chain(request.source)
    answer = chain.run(request.question)

    # Log feedback to database
    log_feedback(request.question, answer, request.source)

    return {"answer": answer}
