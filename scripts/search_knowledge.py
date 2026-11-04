import json
import math
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "knowledge" / "qgis_3_40" / "embeddings.sqlite"

MODEL = "nomic-embed-text"
OLLAMA_URL = "http://127.0.0.1:11434/api/embed"


def embed_question(question):
    payload = json.dumps({
        "model": MODEL,
        "input": question,
    }).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)

    vectors = result.get("embeddings", [])

    if not vectors or len(vectors[0]) != 768:
        raise RuntimeError("Invalid question embedding.")

    return vectors[0]


def cosine_similarity(a, b):
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def search(question, limit=5):
    question_vector = embed_question(question)

    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute("""
            SELECT id, topic, page, text, embedding
            FROM passages
            WHERE model = ?
        """, (MODEL,)).fetchall()

    results = []

    for passage_id, topic, page, text, embedding in rows:
        vector = json.loads(embedding)
        score = cosine_similarity(question_vector, vector)

        results.append({
            "id": passage_id,
            "topic": topic,
            "page": page,
            "score": score,
            "text": text,
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:limit]


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "How do I clip a pipeline layer using a city boundary?"

    print("=== OWENSGEOMIND SEMANTIC SEARCH ===")
    print("Question:", question)

    try:
        results = search(question)
    except Exception as error:
        raise SystemExit(f"Search failed: {error}")

    for index, result in enumerate(results, start=1):
        print(f"\n=== RESULT {index} ===")
        print("Topic:", result["topic"])
        print("PDF page:", result["page"])
        print("Similarity:", round(result["score"], 4))
        print("Passage ID:", result["id"])
        print("Preview:", " ".join(result["text"][:400].split()))

    if results:
        print("\nSUCCESS: Semantic search completed.")
    else:
        print("\nNo matching passages found.")


if __name__ == "__main__":
    main()
