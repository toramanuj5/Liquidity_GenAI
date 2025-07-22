# backend/app/qa_engine.py for Metadata-aware QA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from transformers import pipeline

def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization=True)

def get_qa_chain(source_filter=None):
    vectorstore = load_vectorstore()

    if source_filter:
        retriever = vectorstore.as_retriever(search_kwargs={"filter": {"source": source_filter}})
    else:
        retriever = vectorstore.as_retriever()

    hf_pipeline = pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        max_length=512,
        temperature=0.1
    )

    llm = HuggingFacePipeline(pipeline=hf_pipeline)

    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
