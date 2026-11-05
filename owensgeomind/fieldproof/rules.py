"""Validation rules for FieldProof Lite."""

DEFAULT_REQUIRED_FIELDS = ["asset_id"]


def is_missing(value):
    """Return True when an attribute has no useful value."""
    if value is None:
        return True

    if hasattr(value, "isNull") and value.isNull():
        return True

    if isinstance(value, str) and not value.strip():
        return True

    return False
