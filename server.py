from pathlib import Path

import pymupdf
from mcp.server.fastmcp import FastMCP

from services.embedding import generate_embedding
from services.qdrant_service import (
    search_vectors,
    list_sources as qdrant_list_sources,
)


mcp = FastMCP("Personal Knowledge Base")

USER_ID = 1


@mcp.tool()
def search_notes(query: str, top_k: int = 5) -> str:
    """Search personal notes using semantic similarity."""
    query_vector = generate_embedding(query)

    results = search_vectors(
        query_vector=query_vector,
        user_id=USER_ID,
        top_k=top_k,
    )

    MIN_SCORE = 0.60

    results = [
        result
        for result in results
        if result.score >= MIN_SCORE
    ]

    if not results:
        return "No confident match found."

    output = []

    for i, result in enumerate(results, start=1):
        payload = result.payload or {}

        text = payload.get("text", "")
        source = payload.get("source", "Unknown source")
        page = payload.get("page", "Unknown page")
        score = result.score

        output.append(
            f"Result {i}\n"
            f"Score: {score:.4f}\n"
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Text: {text}"
        )

    return "\n\n---\n\n".join(output)


@mcp.tool()
def get_document(doc_id: str) -> str:
    """Get the full text of an indexed PDF document."""
    document_path = Path("documents") / doc_id

    if not document_path.exists():
        return f"Document not found: {doc_id}"

    if document_path.suffix.lower() != ".pdf":
        return f"Unsupported document type: {doc_id}"

    try:
        with pymupdf.open(document_path) as document:
            pages = []

            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()

                if text:
                    pages.append(
                        f"--- Page {page_number} ---\n{text}"
                    )

        if not pages:
            return f"No text found in document: {doc_id}"

        return "\n\n".join(pages)

    except Exception as e:
        return f"Failed to read document: {e}"


@mcp.tool()
def list_sources() -> str:
    """List all indexed source documents."""
    sources = qdrant_list_sources(USER_ID)

    if not sources:
        return "No indexed sources found."

    return "\n".join(
        f"{index}. {source}"
        for index, source in enumerate(sources, start=1)
    )


if __name__ == "__main__":
    mcp.run()