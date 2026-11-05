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

    "Buffer": {
        "name": "Buffer (distance around features)",
        "algorithm_id": "native:buffer",
        "documentation_pages": [],
        "steps": [
            "Select the vector layer you want to buffer.",
            "Check the input layer CRS and its coordinate units.",
            "For meter-based planar buffers, choose a suitable local projected CRS with meter units.",
            "If needed, reproject the layer using Export > Save Features As and select the appropriate output CRS.",
            "Use the newly reprojected layer as the input.",
            "Open the Processing Toolbox and search for Buffer.",
            "Enter the buffer distance in the layer's coordinate units.",
            "Choose an output destination and click Run.",
            "Inspect the resulting geometry and verify the distance.",
        ],
        "notes": [
            "EPSG:4326 uses degrees, not meters.",
            "Changing the project CRS alone does not reproject the input layer.",
            "EPSG:3857 should not be assumed accurate for local distance measurements.",
            "Choose a projected CRS appropriate to the location and purpose.",
            "OwensGeoMind's Create Buffer tool requires a projected input layer with meter units.",
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
