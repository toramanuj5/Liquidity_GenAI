from fastapi.responses import HTMLResponse  # Add this import at the top
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core.pdf_processor import PDFProcessor
from backend.db.session import SessionLocal, init_db
import os

app = FastAPI(
    title="Liquidity GenAI Compliance API",
    version="1.0"
)

# Initialize components
pdf_processor = PDFProcessor()

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:8501",  # Streamlit
    "http://localhost:8000"   # FastAPI itself
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
@app.on_event("startup")
def startup_event():
    init_db()  # Creates tables if they don't exist

# --- Core Endpoints ---
@app.post("/upload")
async def upload_pdf(
    file: UploadFile, 
    doc_type: str = "policy"
):
    """Handle PDF uploads with type classification"""
    if doc_type not in ["policy", "regulation"]:
        raise HTTPException(400, "doc_type must be 'policy' or 'regulation'")

    # Temporary save (atomic write pattern)
    temp_dir = "data/temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = f"{temp_dir}/{file.filename}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        result = pdf_processor.process_pdf(temp_path, doc_type)
        return {
            "status": "success",
            "document_id": str(result["id"]),
            "saved_to": result["path"]
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)  # Cleanup temp file

# --- Utility Endpoints ---
@app.get("/")
def health_check():
    return {"status": "healthy"}

# Mount static directories
app.mount("/faiss_index", StaticFiles(directory="data/faiss_index"), name="faiss_index")

# Temporary testing endpoint - List all documents
@app.get("/documents", response_class=HTMLResponse)
async def list_documents():
    db = SessionLocal()
    documents = db.query(Document).all()
    db.close()
    
    html_content = """
    <html>
        <body>
            <h1>Uploaded Documents</h1>
            <table border="1">
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Path</th>
                </tr>
    """
    for doc in documents:
        html_content += f"""
                <tr>
                    <td>{doc.id}</td>
                    <td>{doc.title}</td>
                    <td>{doc.source}</td>
                    <td>{doc.file_path}</td>
                </tr>
        """
    html_content += """
            </table>
            <h2><a href="/upload-form">Upload New File</a></h2>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Browser-friendly upload form
@app.get("/upload-form", response_class=HTMLResponse)
async def upload_form():
    return HTMLResponse("""
    <html>
        <body>
            <h1>Upload PDF</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <label>Document Type:</label>
                <select name="doc_type" required>
                    <option value="policy">Internal Policy</option>
                    <option value="regulation">Regulation</option>
                </select><br><br>
                <input type="file" name="file" accept=".pdf" required><br><br>
                <button type="submit">Upload</button>
            </form>
            <p><a href="/documents">View All Documents</a></p>
        </body>
    </html>
    """)