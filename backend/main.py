from pathlib import Path
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.database import Base, SessionLocal, engine, get_db
from backend.models import Document, User

from services.chunking import create_chunks
from services.embedding import generate_embedding, generate_embeddings
from services.pdf_reader import extract_text_from_pdf
from services.qdrant_service import (
    create_collection,
    delete_document_vectors,
    list_sources as qdrant_list_sources,
    search_vectors,
    store_chunks,
)


app = FastAPI(
    title="Personal Knowledge Base API",
    description="Backend API for the Personal Knowledge MCP Server",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

security = HTTPBearer()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = decode_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user


@app.get("/")
def root():
    return {
        "message": "Personal Knowledge Base API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/auth/signup")
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    email = request.email.lower().strip()

    if len(request.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    return {
        "message": "Account created successfully.",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }


@app.post("/auth/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    email = request.email.lower().strip()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(user.id)

    return {
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
    }


@app.get("/sources")
def sources(
    current_user: User = Depends(get_current_user),
):
    return {
        "sources": qdrant_list_sources(current_user.id),
    }


@app.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    filename = Path(file.filename).name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are currently supported.",
        )

    existing = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.filename == filename,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A document with this filename already exists.",
        )

    user_directory = (
        Path("documents")
        / "users"
        / str(current_user.id)
    )

    user_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = user_directory / filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        pages = extract_text_from_pdf(str(file_path))

        if not pages:
            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="No readable text found in the PDF.",
            )

        chunks = create_chunks(pages)

        if not chunks:
            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail="Could not create text chunks from the PDF.",
            )

        texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(texts)

        create_collection()

        store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            source=filename,
            user_id=current_user.id,
        )

        document = Document(
            filename=filename,
            file_path=str(file_path),
            user_id=current_user.id,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return {
            "message": "Document uploaded and indexed successfully.",
            "document": {
                "id": document.id,
                "filename": document.filename,
                "pages": len(pages),
                "chunks": len(chunks),
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {e}",
        )


@app.get("/documents")
def documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return {
        "documents": [
            {
                "id": document.id,
                "filename": document.filename,
                "uploaded_at": document.uploaded_at.isoformat()
                if document.uploaded_at
                else None,
            }
            for document in records
        ]
    }


@app.get("/documents/{document_id}")
def document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    result = Path(record.file_path)

    if not result.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file no longer exists.",
        )

    content = "\n".join(
        f"--- Page {page['page']} ---\n{page['text']}"
        for page in extract_text_from_pdf(str(result))
    )

    return {
        "document": record.filename,
        "content": content,
    }


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    delete_document_vectors(
        user_id=current_user.id,
        source=record.filename,
    )

    Path(record.file_path).unlink(missing_ok=True)

    db.delete(record)
    db.commit()

    return {
        "message": "Document deleted successfully.",
    }


@app.post("/search")
def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    if request.top_k < 1 or request.top_k > 10:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 10.",
        )

    query_vector = generate_embedding(query)

    results = search_vectors(
        query_vector=query_vector,
        user_id=current_user.id,
        top_k=request.top_k,
    )

    MIN_SCORE = 0.60

    results = [
        result
        for result in results
        if result.score >= MIN_SCORE
    ]

    return {
        "query": query,
        "results": [
            {
                "score": round(result.score, 4),
                "source": (result.payload or {}).get(
                    "source",
                    "Unknown source",
                ),
                "page": (result.payload or {}).get(
                    "page",
                    "Unknown page",
                ),
                "text": (result.payload or {}).get(
                    "text",
                    "",
                ),
            }
            for result in results
        ],
        "message": (
            None
            if results
            else "No confident match found."
        ),
    }