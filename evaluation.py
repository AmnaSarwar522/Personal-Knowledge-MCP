from services.embedding import generate_embedding
from services.qdrant_service import search_vectors


USER_ID = 1


TEST_QUERIES = [
    {
        "query": "What is a complex variable?",
        "expected_pages": {2},
    },
    {
        "query": "What are the Cauchy-Riemann equations?",
        "expected_pages": {2, 3},
    },
    {
        "query": "How does the Laplace transform help engineering systems?",
        "expected_pages": {4},
    },
    {
        "query": "What is the difference between Laplace and Fourier transforms?",
        "expected_pages": {5, 7},
    },
    {
        "query": "How is FFT used for audio noise reduction?",
        "expected_pages": {6},
    },
]


def evaluate_query(query: str, expected_pages: set[int], top_k: int = 3):
    query_vector = generate_embedding(query)

    results = search_vectors(
        query_vector=query_vector,
        user_id=USER_ID,
        top_k=top_k,
    )

    retrieved_pages = [
        result.payload.get("page")
        for result in results
        if result.payload
    ]

    relevant = any(
        page in expected_pages
        for page in retrieved_pages
    )

    return relevant, retrieved_pages


def main():
    hits = 0

    for i, item in enumerate(TEST_QUERIES, start=1):
        relevant, pages = evaluate_query(
            item["query"],
            item["expected_pages"],
        )

        if relevant:
            hits += 1

        print(f"\nTest {i}")
        print(f"Query: {item['query']}")
        print(f"Expected pages: {sorted(item['expected_pages'])}")
        print(f"Retrieved pages: {pages}")
        print(f"Hit@3: {'YES' if relevant else 'NO'}")

    precision_at_3 = hits / len(TEST_QUERIES)

    print("\n====================")
    print(f"Hit@3: {hits}/{len(TEST_QUERIES)}")
    print(f"Hit@3 score: {precision_at_3:.2%}")
    print("====================")


if __name__ == "__main__":
    main()
