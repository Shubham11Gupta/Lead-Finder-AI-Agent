"""Suppression manager exports."""

from .manager import (
    add_opt_out_to_suppression,
    is_lead_suppressed,
    load_suppression_registry,
    save_suppression_registry,
)

__all__ = [
    "add_opt_out_to_suppression",
    "is_lead_suppressed",
    "load_suppression_registry",
    "save_suppression_registry",
]

