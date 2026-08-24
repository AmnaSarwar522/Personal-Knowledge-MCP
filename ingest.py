from pathlib import Path

from services.pdf_reader import extract_text_from_pdf
from services.chunking import create_chunks
from services.embedding import generate_embeddings
from services.qdrant_service import create_collection, store_chunks


PDF_PATH = Path("documents/Complex_Variables_Project_Report.pdf")
SOURCE_NAME = PDF_PATH.name
USER_ID = 1


def main():
    print("Reading PDF...")
    pages = extract_text_from_pdf(str(PDF_PATH))
    print(f"Pages: {len(pages)}")

    print("Creating chunks...")
    chunks = create_chunks(pages)
    print(f"Chunks: {len(chunks)}")

    print("Generating embeddings...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    print(f"Embeddings: {len(embeddings)}")

    print("Creating Qdrant collection...")
    create_collection()

    print("Storing chunks...")
    store_chunks(
        chunks,
        embeddings,
        SOURCE_NAME,
        user_id=USER_ID,
    )

    print("Ingestion complete!")


if __name__ == "__main__":
    main()