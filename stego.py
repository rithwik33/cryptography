"""
stego.py — LSB (Least Significant Bit) Image Steganography

This module hides arbitrary binary data inside PNG images by modifying the
least significant bit of each color channel value. The modification is
imperceptible to the human eye (typically PSNR > 50 dB).

Embedding format:
    [MAGIC: 32 bits (4 bytes, "STEG")][LENGTH: 32 bits (4 bytes, big-endian)][PAYLOAD: variable bits]

Each bit of the payload replaces the LSB of one channel value (R, G, or B).

Design decisions:
- Images are converted to RGB (3 channels) for embedding. Alpha is not used
  because transparency changes can be visually noticeable and some image
  viewers/editors strip or modify alpha channels.
- A 4-byte MAGIC header ("STEG") is stored first so extraction can verify
  the image actually contains steganographic data.
- A 4-byte length header follows so extraction knows exactly how many
  bytes to read — no delimiters or end-of-message markers needed.
- NumPy is used for fast bitwise operations on pixel arrays.
- Only PNG images are supported because JPEG's lossy compression destroys LSB data.
"""

import numpy as np
from PIL import Image

# ── Constants ────────────────────────────────────────────────────────────────

MAGIC = b"STEG"               # 4-byte magic signature for validation
MAGIC_BITS = len(MAGIC) * 8   # 32 bits
LENGTH_BITS = 32               # 4 bytes for the payload length header
HEADER_BITS = MAGIC_BITS + LENGTH_BITS  # 64 bits total header
HEADER_BYTES = len(MAGIC) + 4  # 8 bytes total header


# ── Capacity ─────────────────────────────────────────────────────────────────

def calculate_capacity(image: Image.Image) -> int:
    """
    Calculate the maximum number of bytes that can be embedded in the image.

    Uses 1 bit per channel (RGB = 3 channels per pixel), minus the 8-byte
    header overhead (4-byte MAGIC + 4-byte length).

    Args:
        image: A PIL Image object.

    Returns:
        Maximum embeddable payload size in bytes.
    """
    img = image.convert("RGB")
    width, height = img.size
    total_bits = width * height * 3  # 3 channels, 1 bit each
    total_bytes = total_bits // 8
    # Subtract the 8-byte header (MAGIC + length)
    return max(0, total_bytes - HEADER_BYTES)


# ── Embedding ────────────────────────────────────────────────────────────────

def embed_data(image: Image.Image, data: bytes) -> Image.Image:
    """
    Embed binary data into an image using LSB steganography.

    The data is preceded by a 4-byte MAGIC signature ("STEG") and a
    4-byte big-endian length header. Each bit of the combined header + data
    replaces the LSB of one channel value in the flattened RGB pixel array.

    Args:
        image: The cover image (PIL Image). Will be converted to RGB.
        data: The binary data to embed (e.g., encrypted ciphertext).

    Returns:
        A new PIL Image (RGB, PNG-compatible) with the data embedded.

    Raises:
        ValueError: If the data exceeds the image's embedding capacity.
        ValueError: If the data is empty.
    """
    if not data:
        raise ValueError("Data to embed cannot be empty.")

    img = image.convert("RGB")
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.flatten()

    # Build payload: MAGIC + 4-byte length header + data
    length_header = len(data).to_bytes(4, byteorder="big")
    payload = MAGIC + length_header + data

    total_bits_needed = len(payload) * 8
    if total_bits_needed > len(flat):
        max_bytes = len(flat) // 8 - HEADER_BYTES  # minus header
        raise ValueError(
            f"Data too large for this image. "
            f"Need {len(data)} bytes but image can hold at most {max_bytes} bytes."
        )

    # Convert payload to a bit array
    payload_array = np.frombuffer(payload, dtype=np.uint8)
    bits = np.unpackbits(payload_array)

    # Clear LSBs of the target channel values and set them to payload bits
    flat[:total_bits_needed] = (flat[:total_bits_needed] & 0xFE) | bits

    # Reshape back to image dimensions
    stego_pixels = flat.reshape(pixels.shape)
    stego_image = Image.fromarray(stego_pixels, mode="RGB")
    return stego_image


# ── Extraction ───────────────────────────────────────────────────────────────

def extract_data(stego_image: Image.Image) -> bytes:
    """
    Extract hidden binary data from a stego image.

    Reads the 4-byte MAGIC header from the LSBs to verify the image contains
    hidden data, then reads the 4-byte length header, and extracts exactly
    that many bytes of payload data.

    Args:
        stego_image: The stego image (PIL Image) containing hidden data.

    Returns:
        The extracted binary data (e.g., encrypted ciphertext).

    Raises:
        ValueError: If the MAGIC header is missing (no hidden data).
        ValueError: If the length header is invalid or exceeds image capacity.
    """
    img = stego_image.convert("RGB")
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.flatten()

    # Need at least HEADER_BITS (64) LSBs for MAGIC + length
    if len(flat) < HEADER_BITS:
        raise ValueError("Image is too small to contain hidden data.")

    # Extract the first 32 LSBs → 4-byte MAGIC header
    magic_bits = flat[:MAGIC_BITS] & 1
    magic_bytes = np.packbits(magic_bits).tobytes()

    if magic_bytes != MAGIC:
        raise ValueError("No hidden data found in this image.")

    # Extract the next 32 LSBs → 4-byte length header
    length_bits = flat[MAGIC_BITS:HEADER_BITS] & 1
    length_bytes = np.packbits(length_bits).tobytes()
    payload_length = int.from_bytes(length_bytes, byteorder="big")

    # Validate payload length
    if payload_length <= 0:
        raise ValueError("No hidden data found in this image.")

    max_payload = (len(flat) // 8) - HEADER_BYTES
    if payload_length > max_payload:
        raise ValueError(
            "Invalid or corrupted data header. "
            "This image may not contain hidden data."
        )

    # Extract the payload bits
    total_bits = HEADER_BITS + (payload_length * 8)
    if total_bits > len(flat):
        raise ValueError("Corrupted data: payload extends beyond image bounds.")

    payload_bits = flat[HEADER_BITS:total_bits] & 1
    payload_bytes = np.packbits(payload_bits).tobytes()

    return payload_bytes
