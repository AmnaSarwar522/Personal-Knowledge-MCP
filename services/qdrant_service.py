import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
)


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "personal_knowledge"

client = QdrantClient(url=QDRANT_URL)


def create_collection():
    existing = [
        collection.name
        for collection in client.get_collections().collections
    ]

    if COLLECTION_NAME not in existing:
        from qdrant_client.models import Distance, VectorParams

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=3072,
                distance=Distance.COSINE,
            ),
        )


def store_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
    source: str,
    user_id: int,
):
    points = []

    for chunk, embedding in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "user_id": user_id,
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


def search_vectors(
    query_vector: list[float],
    user_id: int,
    top_k: int = 5,
):
    user_filter = Filter(
        must=[
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id),
            )
        ]
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=user_filter,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    return results.points


def list_sources(user_id: int):
    sources = set()

    user_filter = Filter(
        must=[
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id),
            )
        ]
    )

    records, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=user_filter,
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


def delete_document_vectors(user_id: int, source: str):
    user_filter = Filter(
        must=[
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id),
            ),
            FieldCondition(
                key="source",
                match=MatchValue(value=source),
            ),
        ]
    )

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=user_filter,
        wait=True,
    )