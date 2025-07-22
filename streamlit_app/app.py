# streamlit_app/app.py
import requests
import streamlit as st

st.title("📘 Liquidity Risk RAG QA")

question = st.text_input("Ask your question:")
source = st.text_input("Optional: Filter by PDF name (e.g. Basel-Building-blocks.pdf)")

if st.button("Submit Query") and question:
    response = requests.post("http://localhost:8000/query", json={"question": question, "source": source or None})
    st.markdown("### Answer:")
    st.write(response.json()["answer"])
