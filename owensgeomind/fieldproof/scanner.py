
"""FieldProof Lite: Read-only GIS quality-control scanner."""

from qgis.core import QgsVectorLayer
from .rules import DEFAULT_REQUIRED_FIELDS, is_missing


def scan_layer(layer, required_fields=None):
    """Inspect a QGIS vector layer without changing its data."""

    if not isinstance(layer, QgsVectorLayer):
        raise TypeError("A QGIS vector layer is required.")

    if not layer.isValid():
        raise ValueError("The selected layer is invalid.")

    if required_fields is None:
        required_fields = DEFAULT_REQUIRED_FIELDS

    issues = []
    field_names = set(layer.fields().names())

    # Check whether required columns exist.
    for field_name in required_fields:
        if field_name not in field_names:
            issues.append({
                "feature_id": None,
                "rule": "MISSING_FIELD",
                "message": f"Required field '{field_name}' is missing.",
            })

    seen_ids = {}

    # Examine every feature in the selected layer.
    for feature in layer.getFeatures():
        feature_id = feature.id()

        for field_name in required_fields:
            if field_name not in field_names:
                continue

            value = feature[field_name]

            if is_missing(value):
                issues.append({
                    "feature_id": feature_id,
                    "rule": "MISSING_VALUE",
                    "message": f"Missing value in '{field_name}'.",
                })

            elif field_name == "asset_id":
                asset_id = str(value).strip()

                if asset_id in seen_ids:
                    issues.append({
                        "feature_id": feature_id,
                        "rule": "DUPLICATE_ASSET_ID",
                        "message": (
                            f"Asset ID '{asset_id}' duplicates "
                            f"feature {seen_ids[asset_id]}."
                        ),
                    })
                else:
                    seen_ids[asset_id] = feature_id

        # Validate feature geometry.
        geometry = feature.geometry()

        if geometry.isNull() or geometry.isEmpty():
            issues.append({
                "feature_id": feature_id,
                "rule": "EMPTY_GEOMETRY",
                "message": "Feature has empty or missing geometry.",
            })

        elif not geometry.isGeosValid():
            issues.append({
                "feature_id": feature_id,
                "rule": "INVALID_GEOMETRY",
                "message": "Feature geometry is invalid.",
            })

    return issues
