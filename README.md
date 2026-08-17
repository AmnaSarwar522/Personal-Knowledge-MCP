# Personal Knowledge-Base MCP Server

A Personal Knowledge-Base MCP Server that provides semantic search over a student-owned document collection using the Model Context Protocol (MCP), Gemini embeddings, and Qdrant.

## Project Overview

This project exposes a personal knowledge base as callable MCP tools.

Instead of relying on keyword matching, the system converts user queries into vector embeddings and retrieves semantically relevant document chunks from Qdrant.

## Architecture

```text
User / MCP Client
       |
       v
MCP Server (FastMCP)
       |
       +----------------------+
       |                      |
       v                      v
 search_notes()        get_document()
       |
       v
Gemini Embedding API
       |
       v
Qdrant Vector Database
       |
       v
Ranked Chunks
       |
       v
Source + Page + Score + Text
## Features

* PDF document ingestion
* Page-by-page text extraction
* Recursive text chunking
* Gemini `gemini-embedding-001` embeddings
* Qdrant vector storage
* Semantic similarity search
* Source and page citations
* Confidence threshold for low-relevance queries
* Full-document retrieval
* Indexed-source listing
* MCP Inspector support

## MCP Tools

### `search_notes`

Searches the knowledge base using semantic similarity.

Arguments:

* `query`: search question or topic
* `top_k`: maximum number of results

Returns:

* similarity score
* source filename
* page number
* relevant text chunk

### `get_document`

Returns the complete text of an indexed PDF document.

Argument:

* `doc_id`: document filename

Example:

```text
Complex_Variables_Project_Report.pdf
```

### `list_source_documents`

Lists all indexed source documents.

Example output:

```text
1. Complex_Variables_Project_Report.pdf
```

## Project Structure

```text
Personal-Knowledge-MCP/
├── documents/
│   └── Complex_Variables_Project_Report.pdf
├── services/
│   ├── chunking.py
│   ├── embedding.py
│   ├── pdf_reader.py
│   └── qdrant_service.py
├── .env
├── .gitignore
├── evaluation.py
├── ingest.py
├── requirements.txt
└── server.py
```

## Setup

### 1. Create and activate virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Gemini API key

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
```

Never commit `.env` to Git.

### 4. Start Qdrant

The project uses local Qdrant at:

```text
http://localhost:6333
```

Example Docker command:

```powershell
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

## Document Ingestion

Place the PDF inside:

```text
documents/
```

Run:

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

Each stored chunk contains:

```text
text
page
source
```

## Running the MCP Server

Start the MCP Inspector:

```powershell
mcp dev server.py
```

The MCP server uses STDIO transport.

Available tools:

```text
search_notes
get_document
list_source_documents
```

## Retrieval Evaluation

A small evaluation set of five queries was used to check whether at least one expected relevant page appeared within the top three retrieved results.

Evaluation result:

```text
Tests: 5
Successful hits: 5
Hit@3: 100%
```

Example evaluation queries included:

* What is a complex variable?
* What are the Cauchy-Riemann equations?
* How does the Laplace transform help engineering systems?
* What is the difference between Laplace and Fourier transforms?
* How is FFT used for audio noise reduction?

## Confidence Filtering

The search tool uses an initial similarity threshold of:

```text
0.60
```

For example, relevant queries produced scores around:

```text
0.79
0.76
0.75
```

while an unrelated query produced scores around:

```text
0.52
```

Therefore low-scoring results are filtered and the tool returns:

```text
No confident match found.
```

## Technologies

* Python
* FastMCP
* Model Context Protocol (MCP)
* Google Gemini Embeddings
* Qdrant
* PyMuPDF
* LangChain Text Splitters
* Docker
* MCP Inspector

## Current Knowledge Source

The current demonstration corpus is:

```text
Complex_Variables_Project_Report.pdf
```

The document contains 7 pages and was split into 30 chunks for the indexed `personal_knowledge` collection.

## Security

* API keys are stored in `.env`
* `.env` is excluded through `.gitignore`
* Secrets should never be committed to source control

## Future Improvements

* Support Markdown and TXT documents
* Add document-level persistent IDs
* Improve duplicate-chunk handling
* Expand the evaluation dataset
* Add more retrieval metrics
* Support multiple document collections
* Add optional Qdrant Cloud deployment
