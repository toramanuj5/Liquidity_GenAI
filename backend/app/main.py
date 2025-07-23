from fastapi import FastAPI, UploadFile, HTTPException, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from core.pdf_processor import PDFProcessor
from db.session import SessionLocal, init_db
from db.models import Document
import os
import logging

app = FastAPI(
    title="Liquidity GenAI Compliance API",
    version="1.0"
)

# Initialize components
pdf_processor = PDFProcessor()

# Create required directories
os.makedirs("data/faiss_index", exist_ok=True)
os.makedirs("data/regulations", exist_ok=True)
os.makedirs("data/internal_policies", exist_ok=True)
os.makedirs("data/temp", exist_ok=True)

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:8501",
    "http://localhost:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization with retries
@app.on_event("startup")
async def startup_event():
    import time
    max_retries = 5
    for attempt in range(max_retries):
        try:
            init_db()
            print("✅ Database initialized successfully")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"⚠️ Retrying database initialization (attempt {attempt + 1})...")
            time.sleep(5)

# --- Core Endpoints ---
@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    doc_type: str = Form(..., description="Type of document (policy|regulation)")
):
    """Handle PDF uploads with type classification"""
    try:
        result = await pdf_processor.process_pdf(file, doc_type)
        return JSONResponse({
            "status": "success",
            "document_id": str(result["id"]),
            "saved_to": result["path"],
            "text_extracted": len(result["text"]) > 0
        })
    except Exception as e:
        raise HTTPException(
            status_code=400 if "validation" in str(e).lower() else 500,
            detail=str(e)
        )

# --- Utility Endpoints ---
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "endpoints": {
            "upload_form": "/upload-form",
            "list_documents": "/documents",
            "upload_api": "/upload"
        }
    }

# Mount static directories
app.mount("/faiss_index", StaticFiles(directory="data/faiss_index"), name="faiss_index")

# --- HTML Endpoints ---
@app.get("/documents", response_class=HTMLResponse)
async def list_documents():
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        html_content = """
        <html>
            <head>
                <title>Document List</title>
                <style>
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h1>Uploaded Documents</h1>
                <table>
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
                <p>API Status: <a href="/">/</a></p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()

@app.get("/upload-form", response_class=HTMLResponse)
async def upload_form():
    return HTMLResponse("""
    <html>
        <head>
            <title>Upload PDF</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                form { margin-top: 20px; }
                input, select { margin-bottom: 10px; padding: 8px; width: 300px; }
                button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
                button:hover { background: #45a049; }
                .error { color: red; margin-top: 10px; }
            </style>
        </head>
        <body>
            <h1>Upload PDF</h1>
            <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                <div>
                    <label>Document Type:</label><br>
                    <select name="doc_type" required>
                        <option value="">Select type...</option>
                        <option value="policy">Internal Policy</option>
                        <option value="regulation">Regulation</option>
                    </select>
                </div>
                <div>
                    <label>PDF File:</label><br>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <button type="submit">Upload</button>
            </form>
            <div id="result" class="error"></div>
            <p><a href="/documents">View All Documents</a> | <a href="/">API Status</a></p>
            <script>
                document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    try {
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        document.getElementById('result').innerHTML = 
                            response.ok ? '✅ Upload successful!' : `❌ Error: ${result.detail}`;
                    } catch (error) {
                        document.getElementById('result').innerHTML = 
                            `❌ Network error: ${error.message}`;
                    }
                });
            </script>
        </body>
    </html>
    """)