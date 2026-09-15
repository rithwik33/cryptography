"""
test_analysis.py — Unit tests for analysis.py

Tests cover:
- MSE for identical and different images
- PSNR for identical and modified images
- Histogram data generation
- Bit-plane extraction
- Capacity calculation
"""

import pytest
import numpy as np
from PIL import Image

from analysis import (
    calculate_mse,
    calculate_psnr,
    get_histogram_data,
    get_bit_plane,
    calculate_capacity,
    calculate_pixel_difference_stats,
    get_amplified_difference_image,
)



def create_test_image(width=100, height=100, color=(128, 128, 128)):
    """Create a solid RGB test image."""
    arr = np.full((height, width, 3), color, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def create_random_image(width=100, height=100):
    """Create a random RGB test image."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


class TestMSE:
    """Tests for Mean Squared Error calculation."""

    def test_identical_images_mse_zero(self):
        """MSE of identical images should be 0."""
        img = create_test_image()
        assert calculate_mse(img, img) == 0.0

    def test_different_images_mse_positive(self):
        """MSE of different images should be > 0."""
        img1 = create_test_image(color=(100, 100, 100))
        img2 = create_test_image(color=(101, 101, 101))
        mse = calculate_mse(img1, img2)
        assert mse > 0

    def test_mse_known_value(self):
        """MSE for a known pixel difference should match expected value."""
        img1 = create_test_image(10, 10, color=(100, 100, 100))
        img2 = create_test_image(10, 10, color=(110, 100, 100))
        # Difference: channel R differs by 10 for all pixels.
        # MSE = mean over all channels: (10² + 0 + 0) / 3 ≈ 33.33
        mse = calculate_mse(img1, img2)
        assert abs(mse - 33.33) < 0.1

    def test_mse_dimension_mismatch(self):
        """Different-sized images should raise ValueError."""
        img1 = create_test_image(100, 100)
        img2 = create_test_image(50, 50)
        with pytest.raises(ValueError, match="dimensions do not match"):
            calculate_mse(img1, img2)

    def test_mse_non_negative(self):
        """MSE should always be non-negative."""
        img1 = create_random_image()
        img2 = create_random_image()
        mse = calculate_mse(img1, img2)
        assert mse >= 0


class TestPSNR:
    """Tests for Peak Signal-to-Noise Ratio calculation."""

    def test_psnr_identical_images(self):
        """PSNR should be infinity for MSE = 0 (identical images)."""
        assert calculate_psnr(0.0) == float("inf")

    def test_psnr_known_value(self):
        """PSNR for MSE = 25 should be 10 * log10(255² / 25) ≈ 34.15 dB."""
        psnr = calculate_psnr(25.0)
        assert abs(psnr - 34.15) < 0.1

    def test_psnr_lsb_range(self):
        """Typical LSB MSE (~0.25) should yield high PSNR (> 50 dB)."""
        psnr = calculate_psnr(0.25)
        assert psnr > 50

    def test_psnr_large_mse(self):
        """Very large MSE should yield low PSNR."""
        psnr = calculate_psnr(10000.0)
        assert psnr < 20

    def test_psnr_positive_for_nonzero_mse(self):
        """PSNR should be positive for any valid (non-zero) MSE."""
        for mse in [0.001, 0.1, 1.0, 10.0, 100.0]:
            assert calculate_psnr(mse) > 0


class TestHistogram:
    """Tests for histogram data generation."""

    def test_histogram_has_three_channels(self):
        """Histogram should have Red, Green, Blue channels."""
        img = create_test_image()
        hist = get_histogram_data(img)
        assert set(hist.keys()) == {"Red", "Green", "Blue"}

    def test_histogram_bins(self):
        """Each channel histogram should have 256 bins."""
        img = create_test_image()
        hist = get_histogram_data(img)
        for channel in hist.values():
            assert len(channel) == 256

    def test_histogram_sums_to_pixel_count(self):
        """Sum of each channel histogram should equal total pixel count."""
        img = create_test_image(50, 50)
        hist = get_histogram_data(img)
        expected = 50 * 50
        for channel in hist.values():
            assert sum(channel) == expected

    def test_solid_image_histogram(self):
        """Solid-color image should have all counts in one bin."""
        img = create_test_image(10, 10, color=(42, 42, 42))
        hist = get_histogram_data(img)
        assert hist["Red"][42] == 100
        assert hist["Green"][42] == 100
        assert hist["Blue"][42] == 100


class TestBitPlane:
    """Tests for bit-plane extraction."""

    def test_bit_plane_output_is_grayscale(self):
        """Bit plane output should be a grayscale (mode L) image."""
        img = create_test_image()
        bp = get_bit_plane(img, 0)
        assert bp.mode == "L"

    def test_bit_plane_same_dimensions(self):
        """Bit plane should have the same dimensions as the input."""
        img = create_test_image(200, 150)
        bp = get_bit_plane(img, 0)
        assert bp.size == (200, 150)

    def test_bit_plane_values_binary(self):
        """Bit plane pixel values should be either 0 or 255."""
        img = create_random_image()
        bp = get_bit_plane(img, 0)
        arr = np.array(bp)
        unique = set(np.unique(arr))
        assert unique.issubset({0, 255})

    def test_bit_plane_invalid_position(self):
        """Bit positions outside 0-7 should raise ValueError."""
        img = create_test_image()
        with pytest.raises(ValueError):
            get_bit_plane(img, 8)
        with pytest.raises(ValueError):
            get_bit_plane(img, -1)

    def test_bit_plane_0_and_7_differ(self):
        """LSB (bit 0) and MSB (bit 7) planes should generally differ for random images."""
        img = create_random_image()
        bp0 = np.array(get_bit_plane(img, 0))
        bp7 = np.array(get_bit_plane(img, 7))
        # They should not be identical for a random image
        assert not np.array_equal(bp0, bp7)


class TestCapacity:
    """Tests for image capacity calculation."""

    def test_capacity_returns_dict(self):
        """Capacity result should be a dictionary with expected keys."""
        img = create_test_image()
        cap = calculate_capacity(img)
        expected_keys = {"width", "height", "total_pixels", "total_channels", "max_bytes", "max_chars_approx"}
        assert set(cap.keys()) == expected_keys

    def test_capacity_100x100(self):
        """100×100 RGB: max_bytes = (100*100*3)/8 - 8 = 3742."""
        img = create_test_image(100, 100)
        cap = calculate_capacity(img)
        assert cap["max_bytes"] == 3742
        assert cap["width"] == 100
        assert cap["height"] == 100

    def test_capacity_dimensions(self):
        """Capacity should scale with image dimensions."""
        small = calculate_capacity(create_test_image(50, 50))
        large = calculate_capacity(create_test_image(200, 200))
        assert large["max_bytes"] > small["max_bytes"]
 
 
class TestPixelDifference:
    """Tests for pixel difference statistics and amplified difference image."""

    def test_identical_images_zero_difference(self):
        """Identical images should report zero changed pixels and channels."""
        img = create_test_image(50, 50)
        stats = calculate_pixel_difference_stats(img, img)
        assert stats["changed_pixels"] == 0
        assert stats["pct_pixels_changed"] == 0.0
        assert stats["changed_channels"] == 0
        assert stats["pct_channels_changed"] == 0.0
        assert stats["total_pixels"] == 2500

    def test_modified_image_positive_difference(self):
        """Image with one pixel changed should report 1 changed pixel."""
        img1 = create_test_image(10, 10, color=(100, 100, 100))
        arr = np.full((10, 10, 3), (100, 100, 100), dtype=np.uint8)
        arr[0, 0, 0] = 101  # Change one channel of one pixel
        img2 = Image.fromarray(arr, mode="RGB")

        stats = calculate_pixel_difference_stats(img1, img2)
        assert stats["changed_pixels"] == 1
        assert stats["changed_channels"] == 1
        assert stats["pct_pixels_changed"] == 1.0  # 1 / 100 * 100 = 1%

    def test_amplified_difference_output(self):
        """Amplified image should exaggerate 1-bit differences to 255."""
        arr1 = np.zeros((10, 10, 3), dtype=np.uint8)
        arr2 = np.zeros((10, 10, 3), dtype=np.uint8)
        arr2[0, 0, 0] = 1  # 1-bit difference
        img1 = Image.fromarray(arr1, mode="RGB")
        img2 = Image.fromarray(arr2, mode="RGB")

        amp = get_amplified_difference_image(img1, img2, scale=255)
        amp_arr = np.array(amp)
        assert amp_arr[0, 0, 0] == 255
        assert amp_arr[0, 0, 1] == 0
        assert amp_arr[1, 1, 0] == 0

    def test_dimension_mismatch_raises_error(self):
        """Mismatched dimensions should raise ValueError."""
        img1 = create_test_image(50, 50)
        img2 = create_test_image(30, 30)
        with pytest.raises(ValueError, match="dimensions do not match"):
            calculate_pixel_difference_stats(img1, img2)
        with pytest.raises(ValueError, match="dimensions do not match"):
            get_amplified_difference_image(img1, img2)
