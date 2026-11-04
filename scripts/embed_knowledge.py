import json
import sqlite3
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge" / "qgis_3_40"

SOURCE = KNOWLEDGE / "targeted_passages.jsonl"
DATABASE = KNOWLEDGE / "embeddings.sqlite"

OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
MODEL = "nomic-embed-text"


def embed(text):
    payload = json.dumps({
        "model": MODEL,
        "input": text,
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
        raise RuntimeError("Invalid embedding response.")

    return vectors[0]


def main():
    with SOURCE.open(encoding="utf-8") as file:
        passages = [json.loads(line) for line in file]

    connection = sqlite3.connect(DATABASE)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS passages (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                page INTEGER NOT NULL,
                text TEXT NOT NULL,
                model TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
        """)

        connection.commit()

        print("=== OWENSGEOMIND VECTOR INDEX ===")
        print("Passages to process:", len(passages))

        for index, passage in enumerate(passages, start=1):
            passage_id = passage["id"]

            existing = connection.execute(
                "SELECT model, text FROM passages WHERE id = ?",
                (passage_id,),
            ).fetchone()

            if existing == (MODEL, passage["text"]):
                print(f"[{index}/{len(passages)}] Already indexed")
                continue

            try:
                vector = embed(passage["text"])
            except Exception as error:
                print(f"ERROR at passage {index}: {error}")
                print("You can safely rerun this script.")
                break

            connection.execute("""
                INSERT OR REPLACE INTO passages
                (id, topic, page, text, model, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                passage_id,
                passage["topic"],
                passage["page"],
                passage["text"],
                MODEL,
                json.dumps(vector),
            ))

            connection.commit()

            print(
                f"[{index}/{len(passages)}] "
                f"{passage['topic']} - page {passage['page']}"
            )

            time.sleep(0.1)

        count = connection.execute(
            "SELECT COUNT(*) FROM passages"
        ).fetchone()[0]

        print("\n=== INDEX STATUS ===")
        print("Stored embeddings:", count)
        print("Database:", DATABASE)

        if count == len(passages):
            print("SUCCESS: All passages indexed.")
        else:
            print("Index incomplete. Rerun to continue.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
