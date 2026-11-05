import html
import re


def format_chat_message(message):
    """Safely format simple Markdown for the QGIS chat."""

    escaped = html.escape(str(message))

    # Convert **bold text** into HTML bold text.
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        escaped
    )

    # Preserve line breaks.
    escaped = escaped.replace("\n", "<br>")

    return (
        '<div style="white-space:normal;">'
        + escaped
        + "</div>"
    )
