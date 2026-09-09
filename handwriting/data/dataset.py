"""
Manifest loading and dataset encapsulation for Phase 5 Handwriting Recognition.

Sources data strictly from external manifests under MEDINTEL_DATA_DIR/handwriting/phase5_derived/.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import pandas as pd
from PIL import Image

from handwriting.config import PreprocessingConfig, get_phase5_derived_dir
from handwriting.data.transforms import AspectRatioPreservingResize


@dataclass
class ManifestRecord:
    """Represents a single verified handwriting sample from a manifest."""
    dataset: str
    image_path: Path
    transcription: str
    split: str
    image_filename: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None


class HandwritingManifestLoader:
    """Loads and filters verified Phase 5 handwriting manifests."""

    MANIFEST_FILENAME_MAP = {
        "combined": "combined_clean_manifest.csv",
        "rxhandbd": "rxhandbd_clean_manifest.csv",
        "doctor_bd": "doctor_bd_clean_manifest.csv",
        "all": "phase5_dataset_manifest.csv",
    }

    def __init__(self, phase5_dir: Optional[Path] = None):
        self.phase5_dir = Path(phase5_dir) if phase5_dir else get_phase5_derived_dir()
        self.manifests_dir = self.phase5_dir / "manifests"

    def resolve_manifest_path(self, manifest_identifier: Union[str, Path]) -> Path:
        """Resolve manifest identifier or direct path to an absolute Path."""
        if isinstance(manifest_identifier, Path) and manifest_identifier.is_file():
            return manifest_identifier

        id_lower = str(manifest_identifier).lower()
        if id_lower in self.MANIFEST_FILENAME_MAP:
            target = self.manifests_dir / self.MANIFEST_FILENAME_MAP[id_lower]
        else:
            target = self.manifests_dir / str(manifest_identifier)

        if not target.is_file():
            # Check if direct path provided
            candidate = Path(manifest_identifier)
            if candidate.is_file():
                return candidate
            raise FileNotFoundError(
                f"Manifest not found: '{manifest_identifier}'. Expected at {target}"
            )
        return target

    def load_records(
        self,
        manifest_identifier: Union[str, Path] = "combined",
        split: Optional[str] = None,
        verify_files_exist: bool = False,
    ) -> List[ManifestRecord]:
        """Load manifest records with optional split filtering.

        Args:
            manifest_identifier: 'combined', 'rxhandbd', 'doctor_bd', or direct CSV path.
            split: Optional filter: 'train', 'val', or 'test'.
            verify_files_exist: If True, checks that every image exists on disk.

        Returns:
            List of ManifestRecord objects.
        """
        manifest_path = self.resolve_manifest_path(manifest_identifier)
        df = pd.read_csv(manifest_path)

        # Normalize column names
        df.columns = [c.strip() for c in df.columns]

        if split:
            split_clean = split.strip().lower()
            if "split" not in df.columns:
                raise ValueError(f"Manifest {manifest_path.name} does not contain a 'split' column.")
            df = df[df["split"].str.lower() == split_clean]

        records: List[ManifestRecord] = []
        missing_files: List[Path] = []

        for _, row in df.iterrows():
            # Prefer derived_image_path, fallback to original_image_path
            img_path_str = str(row.get("derived_image_path") or row.get("original_image_path") or "")
            img_path = Path(img_path_str)

            # Support relative path resolution against phase5_dir if needed
            if not img_path.is_absolute() and not img_path.exists():
                img_path = self.phase5_dir / img_path_str

            if verify_files_exist and not img_path.is_file():
                missing_files.append(img_path)

            transcription = str(row.get("transcription") or "").strip()
            # Handle NaN transcriptions
            if transcription.lower() == "nan":
                transcription = ""

            records.append(
                ManifestRecord(
                    dataset=str(row.get("dataset") or "unknown"),
                    image_path=img_path,
                    transcription=transcription,
                    split=str(row.get("split") or "").lower(),
                    image_filename=str(row.get("image_filename") or img_path.name),
                    brand_name=str(row.get("brand_name")) if pd.notna(row.get("brand_name")) else None,
                    generic_name=str(row.get("generic_name")) if pd.notna(row.get("generic_name")) else None,
                )
            )

        if missing_files and verify_files_exist:
            raise FileNotFoundError(
                f"Found {len(missing_files)} missing image files referenced in manifest {manifest_path.name}. "
                f"First missing file: {missing_files[0]}"
            )

        return records


class HandwritingDataset:
    """PyTorch-compatible dataset for handwritten prescription crops."""

    def __init__(
        self,
        records: List[ManifestRecord],
        transform: Optional[Callable[[Image.Image], Any]] = None,
        config: Optional[PreprocessingConfig] = None,
    ):
        """
        Args:
            records: List of ManifestRecord instances.
            transform: Optional transform callable. Defaults to AspectRatioPreservingResize.
            config: PreprocessingConfig if transform is not explicitly passed.
        """
        self.records = records
        self.transform = transform or AspectRatioPreservingResize(config or PreprocessingConfig())

    @classmethod
    def from_manifest(
        cls,
        manifest_identifier: Union[str, Path] = "combined",
        split: Optional[str] = None,
        phase5_dir: Optional[Path] = None,
        config: Optional[PreprocessingConfig] = None,
        verify_files_exist: bool = False,
    ) -> "HandwritingDataset":
        """Factory method to construct dataset directly from a manifest identifier."""
        loader = HandwritingManifestLoader(phase5_dir=phase5_dir)
        records = loader.load_records(
            manifest_identifier=manifest_identifier,
            split=split,
            verify_files_exist=verify_files_exist,
        )
        return cls(records=records, config=config)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        record = self.records[idx]

        if not record.image_path.is_file():
            raise FileNotFoundError(f"Prescription image not found: {record.image_path}")

        try:
            with Image.open(record.image_path) as raw_img:
                raw_img = raw_img.convert("RGB")
                raw_w, raw_h = raw_img.size

                if isinstance(self.transform, AspectRatioPreservingResize):
                    processed_img, meta = self.transform.preprocess(raw_img)
                elif callable(self.transform):
                    processed_img = self.transform(raw_img)
                    meta = {
                        "raw_dimensions": (raw_w, raw_h),
                        "aspect_ratio_preserved": False,
                    }
                else:
                    processed_img = raw_img
                    meta = {"raw_dimensions": (raw_w, raw_h)}

            return {
                "image": processed_img,
                "transcription": record.transcription,
                "dataset": record.dataset,
                "split": record.split,
                "image_path": str(record.image_path),
                "image_filename": record.image_filename,
                "metadata": meta,
            }
        except Exception as e:
            raise IOError(f"Error loading image '{record.image_path}': {str(e)}") from e
