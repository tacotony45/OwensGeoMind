import json
from pathlib import Path

import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PDF_PATH = (
    PROJECT_ROOT
    / "knowledge"
    / "qgis_3_40"
    / "user_guide.pdf"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "knowledge"
    / "qgis_3_40"
    / "passages.jsonl"
)

MAX_PAGES = 30
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def split_text(text):
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for start in range(0, len(text), step):
        chunk = text[start:start + CHUNK_SIZE].strip()

        if len(chunk) >= 100:
            yield chunk


def main():
    total_passages = 0

    with pymupdf.open(PDF_PATH) as document:
        page_count = min(MAX_PAGES, len(document))

        with OUTPUT_PATH.open("w", encoding="utf-8") as output:
            for page_number in range(page_count):
                page = document[page_number]
                text = page.get_text("text", sort=True)

                for chunk_index, passage in enumerate(split_text(text)):
                    record = {
                        "id": f"qgis340-p{page_number + 1}-c{chunk_index}",
                        "source": "QGIS 3.40 Desktop User Guide",
                        "page": page_number + 1,
                        "text": passage,
                    }

                    output.write(
                        json.dumps(record, ensure_ascii=False) + "\n"
                    )

                    total_passages += 1

    print("=== OWENSGEOMIND KNOWLEDGE INDEX ===")
    print("Pages processed:", page_count)
    print("Passages created:", total_passages)
    print("Output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
