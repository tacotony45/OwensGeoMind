import json
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge" / "qgis_3_40"

PDF_PATH = KNOWLEDGE / "user_guide.pdf"
OUTPUT_PATH = KNOWLEDGE / "targeted_passages.jsonl"

TOPICS = {
    "Clip": range(1450, 1458),
    "Buffer": range(1429, 1433),
    "Intersection": range(1457, 1463),
    "Union": range(1465, 1472),
    "CRS": range(127, 140),
}

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def split_text(text):
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for start in range(0, len(text), step):
        chunk = text[start:start + CHUNK_SIZE].strip()

        if len(chunk) >= 100:
            yield chunk


def main():
    total = 0

    with pymupdf.open(PDF_PATH) as doc:
        with OUTPUT_PATH.open("w", encoding="utf-8") as output:
            for topic, pages in TOPICS.items():
                topic_count = 0

                for page_number in pages:
                    if page_number > len(doc):
                        continue

                    text = doc[page_number - 1].get_text(
                        "text", sort=True
                    )

                    for index, passage in enumerate(split_text(text)):
                        record = {
                            "id": (
                                f"qgis340-{topic.lower()}-"
                                f"p{page_number}-c{index}"
                            ),
                            "topic": topic,
                            "source": "QGIS 3.40 Desktop User Guide",
                            "page": page_number,
                            "text": passage,
                        }

                        output.write(
                            json.dumps(record, ensure_ascii=False)
                            + "\n"
                        )

                        total += 1
                        topic_count += 1

                print(f"{topic}: {topic_count} passages")

    print("\n=== OWENSGEOMIND TARGETED INDEX ===")
    print("Total passages:", total)
    print("Output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
