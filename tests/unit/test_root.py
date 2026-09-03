# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Unit tests for MbaE.load_config_file, MbaE.boot (non-CSV), and
FileSys.setup_subfolders (custom root/folder_list params).

From the terminal, run:

.. code-block:: bash

    python ./tests/unit/test_root.py

"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from losalamos.root import MbaE, FileSys

# ***********************************************************************
# CLASSES
# ***********************************************************************


class TestMbaELoadConfigFile(unittest.TestCase):
    """Tests for MbaE.load_config_file."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_lcf_"))
        cls._payload = {"name": "Alpha", "alias": "al", "value": 42}

        # write fixture files once
        cls._json_file = cls._tmp / "cfg.json"
        cls._json_file.write_text(json.dumps(cls._payload), encoding="utf-8")

        cls._yaml_file = cls._tmp / "cfg.yaml"
        cls._yaml_file.write_text(
            "name: Alpha\nalias: al\nvalue: 42\n", encoding="utf-8"
        )

        cls._yml_file = cls._tmp / "cfg.yml"
        cls._yml_file.write_text(
            "name: Alpha\nalias: al\nvalue: 42\n", encoding="utf-8"
        )

        cls._toml_file = cls._tmp / "cfg.toml"
        cls._toml_file.write_text(
            'name = "Alpha"\nalias = "al"\nvalue = 42\n', encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    # --- happy paths ---

    def test_json_round_trip(self):
        """load_config_file should parse a JSON file into the expected dict."""
        result = MbaE.load_config_file(path=self._json_file)
        self.assertEqual(result["name"], "Alpha")
        self.assertEqual(result["alias"], "al")
        self.assertEqual(result["value"], 42)

    def test_yaml_round_trip(self):
        """load_config_file should parse a .yaml file into the expected dict."""
        result = MbaE.load_config_file(path=self._yaml_file)
        self.assertEqual(result["name"], "Alpha")
        self.assertEqual(result["alias"], "al")
        self.assertEqual(result["value"], 42)

    def test_yml_extension_accepted(self):
        """load_config_file should accept .yml as well as .yaml."""
        result = MbaE.load_config_file(path=self._yml_file)
        self.assertEqual(result["name"], "Alpha")

    def test_toml_round_trip(self):
        """load_config_file should parse a TOML file into the expected dict."""
        result = MbaE.load_config_file(path=self._toml_file)
        self.assertEqual(result["name"], "Alpha")
        self.assertEqual(result["alias"], "al")
        self.assertEqual(result["value"], 42)

    def test_str_path_accepted(self):
        """load_config_file should accept a plain string path, not just Path objects."""
        result = MbaE.load_config_file(path=str(self._json_file))
        self.assertEqual(result["name"], "Alpha")

    # --- error paths ---

    def test_missing_file_raises_file_not_found(self):
        """load_config_file must raise FileNotFoundError for a non-existent path."""
        with self.assertRaises(FileNotFoundError):
            MbaE.load_config_file(path=self._tmp / "does_not_exist.json")

    def test_unsupported_extension_raises_value_error(self):
        """load_config_file must raise ValueError for an unsupported extension."""
        bad = self._tmp / "cfg.ini"
        bad.write_text("[section]\nkey=val\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            MbaE.load_config_file(path=bad)

    def test_returns_dict(self):
        """load_config_file must always return a dict on success."""
        for path in (self._json_file, self._yaml_file, self._toml_file):
            with self.subTest(suffix=path.suffix):
                result = MbaE.load_config_file(path=path)
                self.assertIsInstance(result, dict)


class TestMbaEBootNonCSV(unittest.TestCase):
    """Tests for MbaE.boot with JSON and YAML bootfiles."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_boot_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _make_mbae(self):
        return MbaE(name="Initial", alias="IN")

    def test_boot_from_json(self):
        """boot() should load name and alias from a JSON file."""
        boot_file = self._tmp / "boot.json"
        boot_file.write_text(
            json.dumps({"name": "FromJSON", "alias": "FJ"}), encoding="utf-8"
        )
        m = self._make_mbae()
        m.boot(bootfile=str(boot_file))
        self.assertEqual(m.name, "FromJSON")
        self.assertEqual(m.alias, "FJ")

    def test_boot_from_yaml(self):
        """boot() should load name and alias from a YAML file."""
        boot_file = self._tmp / "boot.yaml"
        boot_file.write_text("name: FromYAML\nalias: FY\n", encoding="utf-8")
        m = self._make_mbae()
        m.boot(bootfile=str(boot_file))
        self.assertEqual(m.name, "FromYAML")
        self.assertEqual(m.alias, "FY")

    def test_boot_sets_bootfile_path(self):
        """boot() must set self.bootfile to a Path pointing at the bootfile."""
        boot_file = self._tmp / "boot2.json"
        boot_file.write_text(json.dumps({"name": "P", "alias": "p"}), encoding="utf-8")
        m = self._make_mbae()
        m.boot(bootfile=str(boot_file))
        self.assertIsInstance(m.bootfile, Path)
        self.assertEqual(m.bootfile, Path(boot_file))

    def test_csv_path_still_works(self):
        """boot() must continue to accept the canonical CSV format."""
        boot_file = self._tmp / "boot.csv"
        boot_file.write_text("field;value\nname;CSVName\nalias;CN\n", encoding="utf-8")
        m = self._make_mbae()
        m.boot(bootfile=str(boot_file))
        self.assertEqual(m.name, "CSVName")
        self.assertEqual(m.alias, "CN")


class TestFileSysSetupSubfolders(unittest.TestCase):
    """Tests for FileSys.setup_subfolders with custom root and folder_list."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="losalamos_sfolder_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _make_filesys(self):
        return FileSys(name="FS", alias="fs")

    def test_custom_root_creates_folders_there(self):
        """setup_subfolders(root=...) should create folders under the given root."""
        root = self._tmp / "custom_root"
        root.mkdir()
        fs = self._make_filesys()
        fs.setup_subfolders(root=root, folder_list=["alpha", "beta"])
        self.assertTrue((root / "alpha").is_dir())
        self.assertTrue((root / "beta").is_dir())

    def test_custom_folder_list_only_those_created(self):
        """setup_subfolders with folder_list should create exactly the listed folders."""
        root = self._tmp / "exact_root"
        root.mkdir()
        fs = self._make_filesys()
        fs.setup_subfolders(root=root, folder_list=["only_this"])
        self.assertTrue((root / "only_this").is_dir())
        # a folder not in the list should not exist
        self.assertFalse((root / "not_this").exists())

    def test_leading_slash_stripped(self):
        """setup_subfolders should strip a leading '/' from folder stems."""
        root = self._tmp / "slash_root"
        root.mkdir()
        fs = self._make_filesys()
        fs.setup_subfolders(root=root, folder_list=["/with_slash"])
        self.assertTrue((root / "with_slash").is_dir())

    def test_nested_folders_created(self):
        """setup_subfolders should handle nested paths like 'a/b/c'."""
        root = self._tmp / "nested_root"
        root.mkdir()
        fs = self._make_filesys()
        fs.setup_subfolders(root=root, folder_list=["a/b/c"])
        self.assertTrue((root / "a" / "b" / "c").is_dir())

    def test_existing_folder_not_raised(self):
        """setup_subfolders must not raise if a folder already exists."""
        root = self._tmp / "exist_root"
        root.mkdir()
        (root / "pre").mkdir()
        fs = self._make_filesys()
        try:
            fs.setup_subfolders(root=root, folder_list=["pre"])
        except Exception as exc:
            self.fail(f"setup_subfolders raised unexpectedly: {exc}")

    def test_path_object_root_accepted(self):
        """setup_subfolders should accept a Path object for root."""
        root = self._tmp / "path_obj_root"
        root.mkdir()
        fs = self._make_filesys()
        fs.setup_subfolders(root=Path(root), folder_list=["x"])
        self.assertTrue((root / "x").is_dir())


# ***********************************************************************
# SCRIPT
# ***********************************************************************

if __name__ == "__main__":
    unittest.main()
