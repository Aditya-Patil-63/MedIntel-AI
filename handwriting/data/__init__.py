"""
Handwriting Recognition Data Pipeline.

MedIntel AI — Phase 5.
"""

from handwriting.data.dataset import (
    HandwritingDataset,
    HandwritingManifestLoader,
    ManifestRecord,
)
from handwriting.data.transforms import AspectRatioPreservingResize

__all__ = [
    "ManifestRecord",
    "HandwritingManifestLoader",
    "HandwritingDataset",
    "AspectRatioPreservingResize",
]
