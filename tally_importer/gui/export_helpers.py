"""Shared helpers for the export flow across tabs."""
from __future__ import annotations

_MAX_DIALOG_ERRORS = 20


def format_error_lines(errors: list[dict]) -> list[str]:
    """Return a list of human-readable error strings, one per failed row."""
    return [f"Row {e['row']}: " + "; ".join(e["errors"]) for e in errors]


def build_error_detail(errors: list[dict], max_shown: int = _MAX_DIALOG_ERRORS) -> str:
    """Return a human-readable summary of validation errors for the export dialog.

    Shows up to *max_shown* individual row errors; any remaining are summarised
    as "...and N more error(s)".
    """
    lines = format_error_lines(errors)
    detail = "\n".join(lines[:max_shown])
    if len(errors) > max_shown:
        detail += f"\n...and {len(errors) - max_shown} more error(s)"
    return detail
