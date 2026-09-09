"""
Image preprocessing for handwritten medical text crops.

Preserves aspect ratios and avoids distorting narrow word crops
prior to TrOCR vision-encoder ingestion.
"""

from typing import Any, Dict, Optional, Tuple
from PIL import Image

from handwriting.config import PreprocessingConfig


class AspectRatioPreservingResize:
    """Resizes word/line image crops while strictly preserving aspect ratio.

    Distinguishes three geometric representations:
    1. Raw source dimensions: (orig_width, orig_height) from prescription crop
    2. Preprocessing dimensions: (scaled_width, scaled_height) proportional scale
    3. Model input dimensions: (target_width, target_height) canvas with padding
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.target_width = self.config.target_width
        self.target_height = self.config.target_height
        self.pad_color = self.config.pad_color

        # Map resample string to PIL resample filter
        filter_name = self.config.resample_filter.upper()
        self.resample = getattr(Image.Resampling, filter_name, Image.Resampling.BICUBIC)

    def preprocess(self, image: Image.Image) -> Tuple[Image.Image, Dict[str, Any]]:
        """Preprocess PIL image preserving aspect ratio with padding.

        Args:
            image: Source PIL Image (RGB or grayscale).

        Returns:
            Tuple of:
            - Padded PIL Image of size (target_width, target_height) in RGB mode
            - Metadata dictionary recording raw, scaled, and canvas dimensions
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        orig_w, orig_h = image.size

        if not self.config.preserve_aspect_ratio:
            # Direct stretch resize (if explicitly requested)
            resized = image.resize((self.target_width, self.target_height), self.resample)
            meta = {
                "raw_dimensions": (orig_w, orig_h),
                "scaled_dimensions": (self.target_width, self.target_height),
                "model_input_dimensions": (self.target_width, self.target_height),
                "aspect_ratio_preserved": False,
                "padding": (0, 0, 0, 0),
            }
            return resized, meta

        # Calculate proportional scale to fit within target dimensions
        scale = min(self.target_width / max(orig_w, 1), self.target_height / max(orig_h, 1))
        scaled_w = max(1, int(round(orig_w * scale)))
        scaled_h = max(1, int(round(orig_h * scale)))

        resized = image.resize((scaled_w, scaled_h), self.resample)

        # Create canvas filled with pad_color (white by default for prescription backgrounds)
        canvas = Image.new("RGB", (self.target_width, self.target_height), color=(self.pad_color, self.pad_color, self.pad_color))

        pad_left = (self.target_width - scaled_w) // 2
        pad_top = (self.target_height - scaled_h) // 2

        canvas.paste(resized, (pad_left, pad_top))

        pad_right = self.target_width - scaled_w - pad_left
        pad_bottom = self.target_height - scaled_h - pad_top

        meta = {
            "raw_dimensions": (orig_w, orig_h),
            "scaled_dimensions": (scaled_w, scaled_h),
            "model_input_dimensions": (self.target_width, self.target_height),
            "scale_factor": scale,
            "aspect_ratio_preserved": True,
            "padding": (pad_left, pad_top, pad_right, pad_bottom),
        }
        return canvas, meta

    def __call__(self, image: Image.Image) -> Image.Image:
        """Convenience call operator returning only the processed image canvas."""
        canvas, _ = self.preprocess(image)
        return canvas
