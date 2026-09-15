"""
analysis.py — Security & Image Quality Analysis Utilities

Provides metrics and visualizations for evaluating the quality and detectability
of LSB steganography:

- MSE (Mean Squared Error): Measures average pixel-level distortion.
- PSNR (Peak Signal-to-Noise Ratio): Quantifies visual quality in dB.
- Histogram comparison: Per-channel intensity distributions for original vs stego.
- Bit-plane extraction: Visualizes individual bit planes to reveal LSB patterns.
- Capacity calculation: Reports embeddable bytes for a given image.
"""

import numpy as np
from PIL import Image


# ── MSE ──────────────────────────────────────────────────────────────────────

def calculate_mse(original: Image.Image, stego: Image.Image) -> float:
    """
    Calculate the Mean Squared Error between two images.

    Both images are converted to RGB and compared channel by channel.
    MSE = mean((original - stego) ** 2)

    Args:
        original: The original cover image.
        stego: The stego image with hidden data.

    Returns:
        The MSE value (0.0 means identical images).

    Raises:
        ValueError: If the images have different dimensions.
    """
    orig_arr = np.array(original.convert("RGB"), dtype=np.float64)
    steg_arr = np.array(stego.convert("RGB"), dtype=np.float64)

    if orig_arr.shape != steg_arr.shape:
        raise ValueError(
            f"Image dimensions do not match: {orig_arr.shape} vs {steg_arr.shape}"
        )

    mse = np.mean((orig_arr - steg_arr) ** 2)
    return float(mse)


# ── PSNR ─────────────────────────────────────────────────────────────────────

def calculate_psnr(mse: float, max_pixel: float = 255.0) -> float:
    """
    Calculate the Peak Signal-to-Noise Ratio from MSE.

    PSNR = 10 * log10(MAX² / MSE)

    Higher PSNR = less distortion = better steganography quality.
    - > 40 dB: Excellent — visually indistinguishable
    - 30–40 dB: Good — minor artifacts possible
    - < 30 dB: Poor — noticeable distortion

    Args:
        mse: Mean Squared Error value.
        max_pixel: Maximum pixel value (255 for 8-bit images).

    Returns:
        PSNR in decibels (dB). Returns float('inf') if MSE is 0 (identical images).
    """
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10((max_pixel ** 2) / mse))


# ── Histogram ────────────────────────────────────────────────────────────────

def get_histogram_data(image: Image.Image) -> dict:
    """
    Compute per-channel histograms for an RGB image.

    Args:
        image: A PIL Image object.

    Returns:
        A dictionary with keys 'Red', 'Green', 'Blue', each mapping
        to a list of 256 integer counts.
    """
    img = image.convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    channels = {"Red": 0, "Green": 1, "Blue": 2}
    histograms = {}

    for name, idx in channels.items():
        hist, _ = np.histogram(arr[:, :, idx], bins=256, range=(0, 256))
        histograms[name] = hist.tolist()

    return histograms


# ── Bit Plane ────────────────────────────────────────────────────────────────

def get_bit_plane(image: Image.Image, bit_position: int = 0) -> Image.Image:
    """
    Extract a specific bit plane from an image's Red channel.

    Bit plane 0 = LSB (used in steganography), bit plane 7 = MSB.

    The result is scaled to full contrast (0 or 255) for visualization.

    Args:
        image: A PIL Image object.
        bit_position: Bit position to extract (0–7, where 0 = LSB).

    Returns:
        A grayscale PIL Image showing the extracted bit plane.

    Raises:
        ValueError: If bit_position is not in range 0–7.
    """
    if not 0 <= bit_position <= 7:
        raise ValueError(f"bit_position must be 0–7, got {bit_position}")

    img = image.convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    # Extract bit plane from the Red channel
    bit_plane = (arr[:, :, 0] >> bit_position) & 1
    visual = (bit_plane * 255).astype(np.uint8)

    return Image.fromarray(visual, mode="L")


# ── Capacity ─────────────────────────────────────────────────────────────────

def calculate_capacity(image: Image.Image) -> dict:
    """
    Calculate embedding capacity statistics for an image.

    Args:
        image: A PIL Image object.

    Returns:
        A dictionary with:
        - 'width': Image width in pixels
        - 'height': Image height in pixels
        - 'total_pixels': Total pixel count
        - 'total_channels': Total channel values (pixels × 3 for RGB)
        - 'max_bytes': Maximum embeddable bytes (minus 8-byte header)
        - 'max_chars_approx': Approximate character count (ASCII)
    """
    img = image.convert("RGB")
    width, height = img.size
    total_pixels = width * height
    total_channels = total_pixels * 3
    max_bytes = (total_channels // 8) - 8  # minus MAGIC (4) + length header (4)

    return {
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "total_channels": total_channels,
        "max_bytes": max(0, max_bytes),
        "max_chars_approx": max(0, max_bytes),  # 1 byte ≈ 1 ASCII char
    }


# ── Pixel Difference & Amplified Visualization ───────────────────────────────

def calculate_pixel_difference_stats(original: Image.Image, stego: Image.Image) -> dict:
    """
    Calculate real pixel-level difference metrics between original and stego images.

    Args:
        original: The original cover image.
        stego: The stego image with hidden data.

    Returns:
        A dictionary with:
        - 'total_pixels': Total number of pixels
        - 'changed_pixels': Number of pixels where at least one channel changed
        - 'pct_pixels_changed': Percentage of pixels changed
        - 'total_channels': Total color channel values (pixels * 3)
        - 'changed_channels': Number of individual channel values changed
        - 'pct_channels_changed': Percentage of channel values changed
    """
    orig_arr = np.array(original.convert("RGB"), dtype=np.int16)
    steg_arr = np.array(stego.convert("RGB"), dtype=np.int16)

    if orig_arr.shape != steg_arr.shape:
        raise ValueError(
            f"Image dimensions do not match: {orig_arr.shape} vs {steg_arr.shape}"
        )

    diff = np.abs(orig_arr - steg_arr)
    changed_channels = int(np.count_nonzero(diff))
    changed_pixels = int(np.count_nonzero(np.any(diff > 0, axis=2)))
    total_pixels = orig_arr.shape[0] * orig_arr.shape[1]
    total_channels = orig_arr.size
    pct_pixels_changed = (changed_pixels / total_pixels * 100) if total_pixels > 0 else 0.0
    pct_channels_changed = (changed_channels / total_channels * 100) if total_channels > 0 else 0.0

    return {
        "total_pixels": total_pixels,
        "changed_pixels": changed_pixels,
        "pct_pixels_changed": pct_pixels_changed,
        "total_channels": total_channels,
        "changed_channels": changed_channels,
        "pct_channels_changed": pct_channels_changed,
    }


def get_amplified_difference_image(original: Image.Image, stego: Image.Image, scale: int = 255) -> Image.Image:
    """
    Create a high-contrast difference image between original and stego images.

    Since LSB steganography only changes channel values by at most +/-1,
    the raw difference is invisible to human eyes. Multiplying by scale (default 255)
    turns any modified channel into bright contrast against a black background.

    Args:
        original: The original cover image.
        stego: The stego image with hidden data.
        scale: Multiplier to amplify differences (default 255).

    Returns:
        A PIL Image (RGB) visualizing the modified pixel locations.
    """
    orig_arr = np.array(original.convert("RGB"), dtype=np.int16)
    steg_arr = np.array(stego.convert("RGB"), dtype=np.int16)

    if orig_arr.shape != steg_arr.shape:
        raise ValueError(
            f"Image dimensions do not match: {orig_arr.shape} vs {steg_arr.shape}"
        )

    diff = np.abs(orig_arr - steg_arr)
    amplified = np.clip(diff * scale, 0, 255).astype(np.uint8)
    return Image.fromarray(amplified, mode="RGB")

