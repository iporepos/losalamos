"""
Unit tests for FigureSVG._temp_working_copy context manager.

Export methods (to_image, to_pdf, to_svg) are not tested here because
they require Inkscape available in PATH — covered by benchmarks instead.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from losalamos.figures import FigureSVG

_MINIMAL_SVG = """\
<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="100" height="100">
</svg>
"""


def _make_svg_fig(tmp_root, name="test"):
    """Write a minimal SVG file and return a loaded FigureSVG."""
    svg_path = tmp_root / f"{name}.svg"
    svg_path.write_text(_MINIMAL_SVG, encoding="utf-8")
    fig = FigureSVG(name=name, alias="F")
    fig.load_data(file_data=svg_path)
    return fig


class TestTempWorkingCopy(unittest.TestCase):
    """FigureSVG._temp_working_copy guarantees copy, swap, restore, and cleanup."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="figsvg_test_"))
        cls._fig = _make_svg_fig(cls._tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_file_data_swapped_inside_context(self):
        original = self._fig.file_data
        with self._fig._temp_working_copy() as dst:
            self.assertNotEqual(self._fig.file_data, original)
            self.assertEqual(self._fig.file_data, dst)

    def test_copy_is_in_a_different_directory(self):
        original = self._fig.file_data
        with self._fig._temp_working_copy() as dst:
            self.assertNotEqual(dst.parent, original.parent)

    def test_copy_has_same_suffix(self):
        original = self._fig.file_data
        with self._fig._temp_working_copy() as dst:
            self.assertEqual(dst.suffix, original.suffix)

    def test_copy_file_exists_inside_context(self):
        with self._fig._temp_working_copy() as dst:
            self.assertTrue(dst.is_file())

    def test_file_data_restored_after_context(self):
        original = self._fig.file_data
        with self._fig._temp_working_copy():
            pass
        self.assertEqual(self._fig.file_data, original)

    def test_temp_dir_deleted_after_context(self):
        captured_dir = []
        with self._fig._temp_working_copy() as dst:
            captured_dir.append(dst.parent)
        self.assertFalse(captured_dir[0].exists())

    def test_file_data_restored_on_exception(self):
        original = self._fig.file_data
        try:
            with self._fig._temp_working_copy():
                raise RuntimeError("simulated failure")
        except RuntimeError:
            pass
        self.assertEqual(self._fig.file_data, original)

    def test_temp_dir_deleted_on_exception(self):
        captured_dir = []
        try:
            with self._fig._temp_working_copy() as dst:
                captured_dir.append(dst.parent)
                raise RuntimeError("simulated failure")
        except RuntimeError:
            pass
        self.assertFalse(captured_dir[0].exists())

    def test_custom_suffix_applied(self):
        with self._fig._temp_working_copy(suffix=".tmp") as dst:
            self.assertEqual(dst.suffix, ".tmp")


if __name__ == "__main__":
    unittest.main()
