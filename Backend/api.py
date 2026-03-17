import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))


app = FastAPI(title="AwesomeRag API", version="1.0.0")


allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://127.0.0.1:3000,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question to ask over uploaded documents")
    k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")
    doc_id: str | None = Field(default=None, description="Optional document filter")
    session_id: str | None = Field(default=None, description="Conversation session identifier")


class SessionRequest(BaseModel):
    previous_session_id: str | None = Field(default=None, description="Previous session to clear")


def get_user_id_from_header(x_user_id: str | None) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id.strip()


def save_uploaded_pdfs(files: list[UploadFile], temp_dir: str) -> list[dict[str, str]]:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required")

    saved_paths = []

    for index, uploaded_file in enumerate(files):
        filename = uploaded_file.filename or f"upload_{index}.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Only PDF files are supported: {filename}")

        safe_name = Path(filename).name
        destination = Path(temp_dir) / f"{index}_{safe_name}"
        file_hasher = hashlib.sha256()

        with destination.open("wb") as output_stream:
            while True:
                chunk = uploaded_file.file.read(1024 * 1024)
                if not chunk:
                    break
                output_stream.write(chunk)
                file_hasher.update(chunk)

        saved_paths.append(
            {
                "path": str(destination),
                "source_file": safe_name,
                "doc_key": f"{safe_name}:{file_hasher.hexdigest()}",
            }
        )

    return saved_paths


@app.post("/ingest")
def ingest_documents(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
    x_user_id: str | None = Header(default=None),
):
    from Backend.DB.qdrant import ingest_pdf_paths
    from Backend.session_store import get_or_create_session_id

    user_id = get_user_id_from_header(x_user_id)
    resolved_session_id = get_or_create_session_id(session_id)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_paths = save_uploaded_pdfs(files, temp_dir)
            result = ingest_pdf_paths(pdf_paths, user_id=user_id, session_id=resolved_session_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        for uploaded_file in files:
            uploaded_file.file.close()

    return {
        "message": "Documents ingested successfully",
        **result,
    }


@app.post("/query")
def query_documents(request: QueryRequest, x_user_id: str | None = Header(default=None)):
    from Backend.Query.send_context import answer_with_sources
    from Backend.session_store import append_session_turn, get_or_create_session_id, get_session_history

    user_id = get_user_id_from_header(x_user_id)
    session_id = get_or_create_session_id(request.session_id)

    try:
        history = get_session_history(user_id=user_id, session_id=session_id)
        result = answer_with_sources(
            query=request.query,
            user_id=user_id,
            k=request.k,
            doc_id=request.doc_id,
            chat_history=history,
            session_id=session_id,
        )
        append_session_turn(
            user_id=user_id,
            session_id=session_id,
            question=request.query,
            answer=result["answer"],
        )
        result["session_id"] = session_id
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result


@app.post("/session/new")
def new_session(request: SessionRequest, x_user_id: str | None = Header(default=None)):
    from Backend.session_store import clear_session_history, get_or_create_session_id

    user_id = get_user_id_from_header(x_user_id)

    if request.previous_session_id:
        clear_session_history(user_id=user_id, session_id=request.previous_session_id)

    return {
        "session_id": get_or_create_session_id(None),
        "user_id": user_id,
    }
