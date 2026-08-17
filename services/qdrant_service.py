from qdrant_client import QdrantClient

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "personal_knowledge"

client = QdrantClient(url=QDRANT_URL)


def create_collection():
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        from qdrant_client.models import Distance, VectorParams

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=3072,
                distance=Distance.COSINE,
            ),
        )


def store_chunks(chunks, embeddings, source):
    from qdrant_client.models import PointStruct
    import uuid

    points = []

    for chunk, embedding in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "source": source,
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )


def search_vectors(query_vector: list[float], top_k: int = 5):
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    return results.points


def list_sources():
    sources = set()

    records, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True,
        with_vectors=False,
    )

    for record in records:
        payload = record.payload or {}
        source = payload.get("source")

        if source:
            sources.add(source)

    return sorted(sources)