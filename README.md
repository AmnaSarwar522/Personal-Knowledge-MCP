# Personal Knowledge-Base MCP Server

A Personal Knowledge-Base MCP Server that provides semantic search over student-owned documents using the Model Context Protocol (MCP), Google Gemini embeddings, and Qdrant.

The project combines a reusable MCP server with a lightweight authenticated web backend for document upload and source management.

---

## Project Overview

This project exposes a personal knowledge base as callable MCP tools.

Instead of relying on keyword matching, documents are:

1. Extracted page-by-page from PDF files.
2. Split into smaller semantic chunks.
3. Converted into vector embeddings using Google Gemini.
4. Stored in Qdrant.
5. Retrieved using semantic similarity search.

The MCP server exposes the knowledge base through reusable tools that can be called by an MCP-compatible client such as MCP Inspector.

---

## Architecture

```text
                         ┌──────────────────────┐
                         │      User / Client    │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
             ┌───────────────┐             ┌───────────────┐
             │ Web Frontend  │             │  MCP Client   │
             │ Upload/Search │             │ MCP Inspector │
             └───────┬───────┘             └───────┬───────┘
                     │                             │
                     ▼                             ▼
             ┌───────────────┐             ┌───────────────┐
             │ FastAPI       │             │ FastMCP       │
             │ Backend       │             │ MCP Server    │
             │ Authentication│             │               │
             │ Uploads       │             │ 3 MCP Tools   │
             └───────┬───────┘             └───────┬───────┘
                     │                             │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Document Processing  │
                         │                      │
                         │ PDF Extraction       │
                         │ Chunking             │
                         │ Gemini Embeddings    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Qdrant Vector Store  │
                         │                      │
                         │ personal_knowledge   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Ranked Search Results│
                         │                      │
                         │ Score                │
                         │ Source               │
                         │ Page                 │
                         │ Text                 │
                         └──────────────────────┘
```

---

## Features

* PDF document ingestion
* Page-by-page PDF text extraction
* Recursive text chunking
* Google Gemini `gemini-embedding-001` embeddings
* Qdrant vector storage
* Semantic similarity search
* Source and page citations
* Confidence filtering for low-relevance queries
* Full-document retrieval
* Indexed-source listing
* Authenticated backend API
* PDF upload support
* User document storage
* MCP Inspector support
* Retrieval evaluation
* 100% Hit@3 on the current evaluation dataset

---

# MCP Tools

The MCP server exposes three tools.

## 1. `search_notes`

Searches the indexed knowledge base using semantic similarity.

### Arguments

```text
query
top_k
```

### Returns

Each result contains:

```text
similarity score
source filename
page number
relevant text chunk
```

### Example

```text
Query:
What is a complex variable?

Result:
Score: 0.7239
Source: Complex_Variables_Project_Report.pdf
Page: 2
Text: ...
```

---

## 2. `get_document`

Returns the complete text of an indexed document.

### Argument

```text
doc_id
```

### Example

```text
Complex_Variables_Project_Report.pdf
```

This allows an MCP client to retrieve the complete source document after identifying a relevant result through semantic search.

---

## 3. `list_sources`

Lists the documents currently indexed in the knowledge base.

### Example output

```text
1. Complex_Variables_Project_Report.pdf
```

This provides a simple way for an MCP client to discover which source documents are available.

---

# Backend API

The project also includes a FastAPI backend used for document management and authentication.

The backend is located in:

```text
backend/
```

The API can be started with:

```powershell
uvicorn backend.main:app --reload
```

The development server runs at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available through FastAPI:

```text
http://127.0.0.1:8000/docs
```

---

## Backend Health Check

The backend provides a health endpoint:

```text
GET /health
```

A successful response confirms that the FastAPI application is running.

Example:

```json
{
  "status": "ok"
}
```

---

## Authentication

Protected backend endpoints require authentication using a Bearer token.

For example, attempting to access a protected endpoint without authentication returns:

```text
401 Unauthorized
```

with:

```json
{
  "detail": "Not authenticated"
}
```

This confirms that authentication protection is active.

---

# Document Upload

Documents can be uploaded through the backend.

Uploaded user documents are stored under:

```text
documents/users/
```

The ingestion pipeline processes an uploaded PDF through the following stages:

```text
PDF Upload
    ↓
PDF Text Extraction
    ↓
Page Metadata
    ↓
Recursive Chunking
    ↓
Gemini Embeddings
    ↓
Qdrant
    ↓
Semantic Search
```

---

# Document Ingestion

The project includes an ingestion script:

```text
ingest.py
```

It can be executed with:

```powershell
python ingest.py
```

The ingestion pipeline performs:

```text
PDF
 ↓
Page extraction
 ↓
Chunking
 ↓
Gemini embeddings
 ↓
Qdrant storage
```

Each indexed chunk contains metadata including:

```text
text
page
source
```

This metadata allows search results to provide source citations and page numbers.

---

# Vector Database

The project uses Qdrant as its vector database.

The current collection is:

```text
personal_knowledge
```

Qdrant stores the generated document embeddings together with their metadata.

For local development, Qdrant can be run at:

```text
http://localhost:6333
```

Example Docker command:

```powershell
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

---

# Embeddings

The project uses Google Gemini embeddings.

The configured embedding model is:

```text
gemini-embedding-001
```

The Gemini API key is configured through an environment variable:

```text
GEMINI_API_KEY=your_api_key_here
```

The `.env` file must never be committed to Git.

---

# Semantic Search

The system performs semantic retrieval rather than simple keyword matching.

For example, a query such as:

```text
How are complex numbers used in engineering?
```

can retrieve content discussing:

```text
AC circuits
control systems
signal processing
complex exponentials
```

even when the exact wording of the query does not appear in the document.

Search results are ranked by vector similarity score.

---

# Confidence Filtering

The search system uses a similarity confidence threshold to reduce irrelevant results.

The current threshold is approximately:

```text
0.60
```

Relevant queries can produce scores such as:

```text
0.72
0.76
0.79
```

Low-confidence results below the configured threshold are filtered.

When no sufficiently relevant result is found, the system can return:

```text
No confident match found.
```

This prevents unrelated document content from being presented as a confident answer.

---

# Retrieval Evaluation

A five-query evaluation dataset was used to measure retrieval quality.

The evaluation checks whether at least one expected relevant page appears within the top three retrieved results.

The current evaluation result is:

```text
====================
Hit@3: 5/5
Hit@3 score: 100.00%
====================
```

## Evaluation Queries

### Test 1

```text
What is a complex variable?
```

Expected page:

```text
[2]
```

Result:

```text
Retrieved pages: [2, 2, 2]
Hit@3: YES
```

---

### Test 2

```text
What are the Cauchy-Riemann equations?
```

Expected pages:

```text
[2, 3]
```

Result:

```text
Retrieved pages: [2, 3, 3]
Hit@3: YES
```

---

### Test 3

```text
How does the Laplace transform help engineering systems?
```

Expected page:

```text
[4]
```

Result:

```text
Retrieved pages: [4, 4, 4]
Hit@3: YES
```

---

### Test 4

```text
What is the difference between Laplace and Fourier transforms?
```

Expected pages:

```text
[5, 7]
```

Result:

```text
Retrieved pages: [7, 4, 5]
Hit@3: YES
```

---

### Test 5

```text
How is FFT used for audio noise reduction?
```

Expected page:

```text
[6]
```

Result:

```text
Retrieved pages: [6, 5, 6]
Hit@3: YES
```

---

## Final Evaluation

```text
Tests: 5
Successful hits: 5
Hit@3: 100%
```

The evaluation script can be run with:

```powershell
python evaluation.py
```

---

# MCP Server

The main MCP server is:

```text
server.py
```

The server uses FastMCP and exposes:

```text
search_notes
get_document
list_sources
```

The registered tools have been verified programmatically.

Example verification:

```powershell
python -c "from server import mcp; print(list(mcp._tool_manager._tools.keys()))"
```

Expected output:

```text
['search_notes', 'get_document', 'list_sources']
```

---

# Running MCP Inspector

The MCP server can be tested using MCP Inspector:

```powershell
mcp dev server.py
```

The MCP Inspector can then be used to:

* Discover the available tools
* Test `search_notes`
* Test `get_document`
* Test `list_sources`
* Inspect tool arguments
* Inspect returned results

---

# Project Structure

The current project structure includes the MCP server, backend API, frontend, document processing services, and evaluation pipeline.

```text
Personal-Knowledge-MCP/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── models.py
│   └── database.py
│
├── frontend/
│   └── ...
│
├── services/
│   ├── chunking.py
│   ├── embedding.py
│   ├── pdf_reader.py
│   └── qdrant_service.py
│
├── documents/
│   └── users/
│       └── ...
│
├── .env
├── .gitignore
├── evaluation.py
├── ingest.py
├── requirements.txt
├── server.py
└── README.md
```

---

# Installation

## 1. Clone the project

```powershell
git clone <repository-url>
cd Personal-Knowledge-MCP
```

---

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

---

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

Main dependencies include:

```text
mcp
qdrant-client
google-genai
PyMuPDF
langchain-text-splitters
fastapi
uvicorn
python-multipart
python-jose
sqlalchemy
python-dotenv
email-validator
```

---

# Environment Configuration

Create a `.env` file in the project root.

Example:

```text
GEMINI_API_KEY=your_api_key_here
```

Additional backend/database configuration can be stored in environment variables as required by the application.

Never commit secret API keys to Git.

---

# Running the Backend

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
uvicorn backend.main:app --reload
```

Verify the API:

```text
http://127.0.0.1:8000/health
```

Open interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Running the MCP Server

For MCP development and testing:

```powershell
mcp dev server.py
```

Available MCP tools:

```text
search_notes
get_document
list_sources
```

---

# Testing

The project has been syntax-checked across the major components.

Examples:

```powershell
python -m py_compile server.py
python -m py_compile ingest.py
python -m py_compile evaluation.py
python -m py_compile backend\main.py
python -m py_compile backend\auth.py
python -m py_compile backend\models.py
python -m py_compile backend\database.py
python -m py_compile services\embedding.py
python -m py_compile services\pdf_reader.py
python -m py_compile services\qdrant_service.py
```

The retrieval evaluation also passes:

```text
Hit@3: 5/5
Hit@3 score: 100.00%
```

---

# Current Demonstration Corpus

The current demonstration document is:

```text
Complex_Variables_Project_Report.pdf
```

The document contains:

```text
7 pages
```

and the indexed collection contains approximately:

```text
30 chunks
```

The document covers topics including:

* Complex variables
* Complex numbers
* Cauchy-Riemann equations
* Laplace transforms
* Fourier transforms
* FFT
* Engineering applications
* Audio signal processing

---

# Security

The project includes authentication for protected backend endpoints.

Security practices include:

* API keys stored in `.env`
* `.env` excluded through `.gitignore`
* Bearer-token authentication for protected API routes
* User documents stored separately under `documents/users/`
* Secrets are not intended to be committed to Git

A request to a protected endpoint without authentication correctly returns:

```text
401 Unauthorized
```

with:

```json
{
  "detail": "Not authenticated"
}
```

---

# Technologies

* Python
* FastMCP
* Model Context Protocol (MCP)
* FastAPI
* Google Gemini
* Gemini `gemini-embedding-001`
* Qdrant
* PyMuPDF
* LangChain Text Splitters
* SQLAlchemy
* JWT/Bearer Authentication
* Docker
* MCP Inspector

---

# Project Outcome

The project demonstrates a complete semantic knowledge-base pipeline:

```text
User Document
     ↓
PDF Extraction
     ↓
Chunking
     ↓
Gemini Embeddings
     ↓
Qdrant Vector Database
     ↓
Semantic Retrieval
     ↓
MCP Tools
     ↓
MCP Client / Inspector
```

The system successfully retrieves relevant document content using semantic similarity and provides source/page citations.

The current retrieval evaluation achieves:

```text
Hit@3 = 100%
```

with all five evaluation queries successfully retrieving an expected relevant page within the top three results.

---

# Future Improvements

Possible future improvements include:

* Support Markdown and TXT documents
* Improve duplicate-chunk handling
* Add persistent document IDs
* Expand the evaluation dataset
* Add additional retrieval metrics
* Support multiple document collections
* Add Qdrant Cloud deployment
* Add richer frontend search and document-management features
* Add document deletion and re-indexing controls

---

# Submission Summary

This project fulfills the core Personal Knowledge-Base MCP Server requirements by providing:

* A real student-owned document corpus
* PDF ingestion
* Sensible document chunking
* Gemini-based embeddings
* Qdrant vector storage
* Semantic search
* Source and page citations
* Full document retrieval
* Indexed source listing
* FastMCP MCP server
* MCP Inspector compatibility
* Retrieval evaluation
* 100% Hit@3 evaluation score
* Authenticated backend for document management

The core MCP functionality is implemented and verified through the available tools and evaluation pipeline.
