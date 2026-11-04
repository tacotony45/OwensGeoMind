"""
OwensGeoMind verified GIS workflow candidates.

These workflows provide structured, source-grounded
instructions independently of local AI generation.
"""

WORKFLOWS = {
    "Clip": {
        "name": "Clip (polygon overlay)",
        "algorithm_id": "native:clip",
        "documentation_pages": [1450, 1451],
        "steps": [
            "Load the input vector layer, such as pipeline lines.",
            "Load the polygon overlay layer, such as a city boundary.",
            "Open Vector > Geoprocessing Tools > Clip, or search "
            "for Clip in the Processing Toolbox.",
            "Choose the pipeline as the Input layer.",
            "Choose the city boundary as the Overlay layer.",
            "For the Clipped output, choose a permanent file "
            "destination ending in .gpkg.",
            "Click Run to execute the algorithm.",
            "Check the resulting layer's geometry and attributes.",
        ],
        "notes": [
            "Only input features inside the overlay polygons "
            "are retained, with geometry clipped at the boundary.",
            "Input attribute values are generally preserved.",
            "Stored length or area fields may need recalculation.",
            "A permanent GeoPackage output does not require "
            "running a separate saving algorithm.",
        ],
    },
}


def get_workflow(topic):
    """Return a supported workflow or None."""
    return WORKFLOWS.get(topic)


def format_workflow(workflow):
    """Format a workflow for display."""
    lines = [f"=== VERIFIED WORKFLOW: {workflow['name']} ==="]

    for number, step in enumerate(workflow["steps"], 1):
        lines.append(f"{number}. {step}")

    lines.append("\nImportant notes:")
    for note in workflow["notes"]:
        lines.append(f"- {note}")

    pages = ", ".join(
        str(page) for page in workflow["documentation_pages"]
    )
    lines.append(f"\nQGIS 3.40 User Guide, PDF pages: {pages}")

    return "\n".join(lines)
