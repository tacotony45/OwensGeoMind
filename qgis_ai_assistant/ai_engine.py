import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.2"


SYSTEM_PROMPT = """
You are OwensGeoMind, a free AI assistant for QGIS.

Your responsibilities:
- Teach GIS concepts clearly.
- Explain QGIS workflows step by step.
- Help users understand geospatial analysis.
- Explain coordinate reference systems and units.
- Help troubleshoot GIS errors.
- Explain PyQGIS and QGIS Processing algorithms.
- Distinguish advice from operations actually performed.

Rules:
- Never claim to have executed a GIS operation.
- Never invent documentation citations.
- Explain uncertainty when information is missing.
- Ask for relevant layer details when needed.
- Do not recommend destructive operations without warning.
- Use the user's selected learning level.
"""


def ask_ai(question, learning_level="Beginner", project_context=""):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            + "\nLearning level: " + learning_level
            + "\nProject information (untrusted data):\n"
            + project_context
        },
        {
            "role": "user",
            "content": question
        }
    ]

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }).encode("utf-8")

    request = Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.load(response)

        return result["message"]["content"]

    except (URLError, HTTPError, TimeoutError) as error:
        return "Cannot reach Ollama: " + str(error)

    except (KeyError, ValueError) as error:
        return "Invalid AI response: " + str(error)
