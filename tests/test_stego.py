"""
test_stego.py — Unit tests for stego.py

Tests cover:
- Embed/extract round-trip
- Capacity validation
- MAGIC header verification
- Small and edge-case images
- PNG format preservation
- Various data sizes
"""

import pytest
import numpy as np
from PIL import Image

from stego import embed_data, extract_data, calculate_capacity, MAGIC


def create_test_image(width: int = 100, height: int = 100) -> Image.Image:
    """Create a random RGB test image."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def create_solid_image(width: int = 100, height: int = 100, color=(128, 128, 128)) -> Image.Image:
    """Create a solid-color RGB test image."""
    arr = np.full((height, width, 3), color, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


class TestCapacity:
    """Tests for embedding capacity calculation."""

    def test_capacity_100x100(self):
        """100×100 RGB image: (100*100*3)/8 - 8 = 3742 bytes."""
        img = create_test_image(100, 100)
        assert calculate_capacity(img) == 3742

    def test_capacity_1x1(self):
        """1×1 RGB image: (1*1*3)/8 - 8 → clamped to 0."""
        img = create_test_image(1, 1)
        assert calculate_capacity(img) == 0

    def test_capacity_10x10(self):
        """10×10 RGB image: (10*10*3)/8 - 8 = 29 bytes."""
        img = create_test_image(10, 10)
        assert calculate_capacity(img) == 29

    def test_capacity_rgba_input(self):
        """RGBA image should be auto-converted to RGB for capacity calc."""
        arr = np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
        cap = calculate_capacity(img)
        # After conversion to RGB: 100*100*3/8 - 8 = 3742
        assert cap == 3742


class TestEmbedExtract:
    """Tests for LSB embed/extract round-trip."""

    def test_round_trip_basic(self):
        """Embed then extract should return the original data."""
        img = create_test_image(100, 100)
        data = b"Hello, Steganography!"
        stego = embed_data(img, data)
        extracted = extract_data(stego)
        assert extracted == data

    def test_round_trip_binary_data(self):
        """Should handle arbitrary binary data (all byte values)."""
        img = create_test_image(100, 100)
        data = bytes(range(256))
        stego = embed_data(img, data)
        extracted = extract_data(stego)
        assert extracted == data

    def test_round_trip_single_byte(self):
        """Should handle a single byte of data."""
        img = create_test_image(10, 10)
        data = b"\x42"
        stego = embed_data(img, data)
        extracted = extract_data(stego)
        assert extracted == data

    def test_round_trip_max_capacity(self):
        """Should work when using the full capacity of the image."""
        img = create_test_image(50, 50)
        cap = calculate_capacity(img)
        data = bytes([i % 256 for i in range(cap)])
        stego = embed_data(img, data)
        extracted = extract_data(stego)
        assert extracted == data

    def test_round_trip_various_sizes(self):
        """Test multiple data sizes to ensure robustness."""
        img = create_test_image(100, 100)
        for size in [1, 10, 100, 500, 1000, 2000]:
            data = bytes([i % 256 for i in range(size)])
            stego = embed_data(img, data)
            extracted = extract_data(stego)
            assert extracted == data, f"Failed for data size {size}"

    def test_capacity_exceeded_raises_error(self):
        """Data exceeding image capacity should raise ValueError."""
        img = create_test_image(10, 10)
        cap = calculate_capacity(img)
        oversized_data = b"\x00" * (cap + 1)
        with pytest.raises(ValueError, match="too large"):
            embed_data(img, oversized_data)

    def test_empty_data_raises_error(self):
        """Empty data should raise ValueError."""
        img = create_test_image(100, 100)
        with pytest.raises(ValueError, match="cannot be empty"):
            embed_data(img, b"")

    def test_stego_image_is_rgb(self):
        """Stego output should always be RGB mode."""
        img = create_test_image(100, 100)
        stego = embed_data(img, b"test")
        assert stego.mode == "RGB"

    def test_stego_image_same_dimensions(self):
        """Stego image should have the same dimensions as the original."""
        img = create_test_image(200, 150)
        stego = embed_data(img, b"test data")
        assert stego.size == img.size

    def test_rgba_input_works(self):
        """RGBA input images should be auto-converted to RGB and work correctly."""
        arr = np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
        data = b"RGBA input test"
        stego = embed_data(img, data)
        extracted = extract_data(stego)
        assert extracted == data

    def test_solid_image_round_trip(self):
        """Solid-color image should still work (uniform pixel values)."""
        img = create_solid_image(100, 100)
        data = b"Hidden in solid image"
        stego = embed_data(img, data)
        extracted = extract_data(stego)
        assert extracted == data

    def test_pixel_changes_are_minimal(self):
        """LSB changes should modify pixel values by at most 1."""
        img = create_solid_image(100, 100, color=(100, 100, 100))
        data = b"Test minimal changes"
        stego = embed_data(img, data)

        orig_arr = np.array(img.convert("RGB"), dtype=np.int16)
        steg_arr = np.array(stego, dtype=np.int16)
        diff = np.abs(orig_arr - steg_arr)

        assert np.max(diff) <= 1, "LSB embedding should change values by at most 1"


class TestMagicHeader:
    """Tests for MAGIC header validation during extraction."""

    def test_normal_image_has_no_hidden_data(self):
        """Extracting from a normal (non-stego) image should raise ValueError."""
        img = create_test_image(100, 100)
        with pytest.raises(ValueError, match="No hidden data"):
            extract_data(img)

    def test_magic_header_present_after_embed(self):
        """After embedding, the MAGIC header should be present in LSBs."""
        img = create_test_image(100, 100)
        stego = embed_data(img, b"test")
        # Extract should work without error (MAGIC is valid)
        extracted = extract_data(stego)
        assert extracted == b"test"

    def test_corrupted_magic_raises_error(self):
        """If MAGIC bytes are corrupted, extraction should fail."""
        img = create_test_image(100, 100)
        stego = embed_data(img, b"test data")
        # Corrupt the first few pixels (where MAGIC is stored)
        arr = np.array(stego, dtype=np.uint8)
        arr[0, 0, :] = [255, 255, 255]  # overwrite MAGIC area
        arr[0, 1, :] = [255, 255, 255]
        corrupted = Image.fromarray(arr, mode="RGB")
        with pytest.raises(ValueError, match="No hidden data"):
            extract_data(corrupted)


class TestRealEmbeddingVerification:
    """Tests verifying real pixel changes and PNG serialization round-trips."""

    def test_embedding_causes_real_pixel_differences(self):
        """Embedding non-empty data must cause real pixel value differences."""
        img = create_solid_image(100, 100, color=(120, 130, 140))
        data = b"Steganography embedded payload with sufficient length!"
        stego = embed_data(img, data)

        orig_arr = np.array(img, dtype=np.int16)
        steg_arr = np.array(stego, dtype=np.int16)
        diff = np.abs(orig_arr - steg_arr)

        assert np.any(diff > 0), "Embedding must create real pixel differences!"
        assert int(np.count_nonzero(diff)) > 0

    def test_png_save_and_reload_roundtrip(self):
        """Saving stego image to PNG bytes and reading back must preserve data exactly."""
        import io
        img = create_test_image(120, 120)
        data = b"Testing lossless PNG byte serialization"
        stego = embed_data(img, data)

        buf = io.BytesIO()
        stego.save(buf, format="PNG")
        buf.seek(0)
        reloaded = Image.open(buf)

        extracted = extract_data(reloaded)
        assert extracted == data

