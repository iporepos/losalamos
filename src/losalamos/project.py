# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Project management and filesystem initialization utilities.

This module provides high-level helpers and abstractions for creating,
loading, and managing projects organized around a predefined filesystem
structure. It defines the core :class:`Project` class and convenience
functions for initializing new projects or restoring existing ones
from disk.

The module is designed to evolve as a central coordination layer between
project metadata, filesystem layout, and downstream processing workflows.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import datetime
import pprint
import tempfile
import shutil
import zipfile
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import pandas as pd
from tqdm import tqdm

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import FileSys

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# Subsubsection example
# -----------------------------------------------------------------------

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}
SUBFOLDERS = {
    "folder": [
        # administrative
        # --------------------------------
        "admin/contracts",
        "admin/contracts/main",
        "admin/proposals",
        "admin/documents",
        "admin/paperwork",
        "admin/meetings",
        "admin/received",
        "admin/messages",
        # Accounting
        # --------------------------------
        "budget/inflows",
        "budget/outflows",
        # Inputs
        # --------------------------------
        "inputs/data",
        "inputs/scripts",
        "inputs/documents",
        "inputs/references",
        "inputs/received",
        "inputs/figures",
        "inputs/figures/raw",
        # Outputs
        # --------------------------------
        "outputs/public",
        "outputs/public/history",
        "outputs/public/latest",
    ],
}

# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def new_project(specs):
    """
    Create a new Project from a specification dictionary.

    .. danger::

        This method overwrites all existing default files.

    :param specs: Dictionary containing project specifications.

        **Required keys**:

        - ``folder_base`` (*str*): Path where the project folder will be created.
        - ``name`` (*str*): Name of the project.

        **Optional keys**:

        - ``alias`` (*str*): Alternative identifier. Defaults to ``None``.
        - ``source`` (*str*): Source reference. Defaults to empty string.
        - ``description`` (*str*): Project description. Defaults to empty string.

    :type specs: dict
    :raises ValueError: If any required key is missing.
    :returns: A new `:class:`losalamos.Project` instance initialized with the given specifications.
    :rtype: :class:`losalamos.Project`


    .. dropdown:: Script example
        :icon: code-square
        :open:

        .. code-block:: python

            import losalamos

            # [CHANGE THIS] setup specs dictionary
            project_specs = {
                "folder_base": "C:/to/losalamos", # change this path
                "name": "newProject",
                "alias": "NPrj",
                "source": "Me",
                "description": "Just a test"
            }

            pj = losalamos.new_project(specs=project_specs)

    """
    # --- Required keys ---
    required = ["folder_base", "name"]
    for key in required:
        if key not in specs:
            raise ValueError(f"Missing required key: '{key}'")

    # --- Optional keys with defaults ---
    defaults = {"alias": None, "source": "", "description": ""}
    merged = {**defaults, **specs}

    # --- Use merged dict safely ---
    # create base folder if not exists
    os.makedirs(merged["folder_base"], exist_ok=True)

    folder_root = Path(merged["folder_base"]) / merged["name"]
    if os.path.isdir(folder_root):
        raise ValueError(f"Project folder already exists '{folder_root}'")

    # instantiate project
    p = Project(name=merged["name"], alias=merged["alias"])
    p.source = merged["source"]
    p.description = merged["description"]
    p.folder_base = merged["folder_base"]
    p.update()
    p.setup()

    return p


def load_project(project_folder):
    """
    Loads a Project from folder

    :param project_folder: path to project root folder
    :type project_folder: str or Path
    :returns: A new `:class:`losalamos.Project` instance.
    :rtype: :class:`losalamos.Project`

    .. dropdown:: Script example
        :icon: code-square
        :open:

        Load an existing ``losalamos.Project``

        .. code-block:: python

            # import the package
            import losalamos

            # get project instance
            pj = losalamos.load_project(project_folder="path/to/project/folder")


    """
    if os.path.isdir(project_folder):
        name = os.path.basename(project_folder)
        folder_base = os.path.abspath(Path(project_folder).parent)
        p = Project(name=name, alias=None)
        p.name = name
        p.folder_base = folder_base

        # update project
        p.update()

        # setup
        p.setup()

        return p
    else:
        raise ValueError(f"Project folder not found: {project_folder}'")


# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************


# CLASSES -- Project-level
# =======================================================================
# ... {develop}
class Project(FileSys):
    """
    Project filesystem abstraction.

    This class represents a project rooted in a filesystem structure and
    extends :class:`losalamos.root.FileSys`. It initializes and manages
    project metadata and default folder definitions.
    """

    def __init__(self, name="LosAlamosProject", alias="LAProj"):
        """
        Initialize a Project instance.

        :param name: Project name.
        :type name: str
        :param alias: Optional short identifier.
        :type alias: str
        """
        super().__init__(name=name, alias=alias)
        self.load_data()

        self.publish_force = False
        self.publish_delta = 1  # hour

    def load_data(self):
        """
        Initialize internal project data.

        Creates a dataframe describing the default project folder structure
        based on ``SUBFOLDERS`` and assigns it to ``self.data``.
        """
        df = pd.DataFrame(SUBFOLDERS)
        df["file"] = ""
        df["file_template"] = ""
        self.data = df.copy()
        return None

    def publish(
        self,
        targets,
        prefix,
        output_folder=None,
        surface=False,
    ):
        """
        Publish a versioned snapshot of selected directories to a managed output location.

        :param targets: A list of directory paths to be included in the snapshot.
        :type targets: list
        :param prefix: The string prefix used for naming the generated archive file.
        :type prefix: str
        :param output_folder: [optional] The destination directory for the published archives.
        :type output_folder: :class:`pathlib.Path`
        :param surface: If True, target folders are placed at the zip root instead of preserving project subfolder structure.
        :type surface: bool
        :return: A dictionary containing the publication status, the resulting path, and metadata.
        :rtype: dict

        .. note::

             The function performs directory validation, checks for publish frequency constraints
             based on ``self.publish_delta``, and handles the rotation of the previous 'latest'
             archive into a history folder before promoting the new build.

        """

        delta = datetime.timedelta(hours=self.publish_delta)

        # Validation
        # ----------------------------------------------------------------
        if not targets:
            raise ValueError("publish(): 'targets' must be a non-empty list")

        if output_folder is None:
            output_folder = Path(f"{self.folder_root}/outputs").resolve()

        os.makedirs(output_folder, exist_ok=True)

        targets = [Path(t).resolve() for t in targets]
        for t in targets:
            if not t.exists():
                raise FileNotFoundError(f"Target does not exist: {t}")
            if not t.is_dir():
                raise NotADirectoryError(f"Target is not a directory: {t}")

        # setup folders
        # ----------------------------------------------------------------
        latest_dir, history_dir = self._ensure_publish_dirs(output_folder)

        # check latest
        # ----------------------------------------------------------------
        latest_file = self._find_latest(latest_dir, prefix)

        now = datetime.datetime.now()

        if latest_file and not self.publish_force:
            last_ts = self._parse_timestamp_from_name(latest_file.name, prefix)
            age = now - last_ts

            if age < delta:
                return {
                    "published": False,
                    "reason": "delta_not_elapsed",
                    "age": age,
                    "latest": latest_file,
                }

        # build archive
        # ----------------------------------------------------------------
        version_id = self._format_timestamp(now)
        filename = f"{prefix}_V{version_id}.zip"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            staging_root = tmpdir / "payload"
            staging_root.mkdir()

            # Pass surface flag to the staging logic
            self._stage_targets(targets, staging_root, surface=surface)

            staging_zip = tmpdir / filename
            self._zip_with_tqdm(staging_root, staging_zip)

            # rotate latest
            # ----------------------------------------------------------------
            if latest_file:
                shutil.move(
                    str(latest_file),
                    history_dir / latest_file.name,
                )

            # promote
            # ----------------------------------------------------------------
            final_path = latest_dir / filename
            shutil.move(staging_zip, final_path)

        return {
            "published": True,
            "archive": final_path,
            "timestamp": now,
            "rotated": latest_file.name if latest_file else None,
        }

    def _iter_files(self, root: Path):
        for path in root.rglob("*"):
            if path.is_file():
                yield path

    def _zip_with_tqdm(self, src_root: Path, dst_zip: Path):
        files = list(self._iter_files(src_root))
        total_bytes = sum(f.stat().st_size for f in files)

        with tqdm(total=total_bytes, unit="B", unit_scale=True) as bar:
            with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    zf.write(f, f.relative_to(src_root))
                    bar.update(f.stat().st_size)

    def _ensure_publish_dirs(self, output_folder: Path):
        output_folder = Path(output_folder)
        latest = output_folder / "latest"
        history = output_folder / "history"

        latest.mkdir(parents=True, exist_ok=True)
        history.mkdir(parents=True, exist_ok=True)

        return latest, history

    def _find_latest(self, latest_dir: Path, prefix: str):
        files = list(latest_dir.glob(f"{prefix}_V*.zip"))

        if len(files) > 1:
            raise RuntimeError(f"Multiple latest archives detected in {latest_dir}")

        return files[0] if files else None

    def _format_timestamp(self, dt: datetime.datetime) -> str:
        """
        YYYYMMDDThhmmss
        """
        return dt.strftime("%Y%m%dT%H%M%S")

    def _parse_timestamp_from_name(self, filename: str, prefix: str):
        """
        Extract datetime from '<prefix>_VYYYYMMDDThhmmss.zip'
        """
        stem = Path(filename).stem

        expected = f"{prefix}_V"
        if not stem.startswith(expected):
            raise ValueError(f"Invalid archive name: {filename}")

        ts = stem[len(expected) :]

        try:
            return datetime.datetime.strptime(ts, "%Y%m%dT%H%M%S")
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp in archive name: {filename}") from exc

    def _stage_targets(self, targets, staging_root: Path, surface: bool = False):
        """
        Copy target directories into staging_root.
        """
        anchor = Path(self.folder_root).resolve()

        for t in targets:
            t = t.resolve()

            if surface:
                # Place directly in the root of the zip using the folder's name
                dst = staging_root / t.name
            else:
                # Preserve the relative path from the project root
                try:
                    rel = t.relative_to(anchor)
                except ValueError:
                    raise ValueError(f"Target {t} is not under project root {anchor}")
                dst = staging_root / rel

            # Prevent overwriting if two different paths have the same folder name in surface mode
            if dst.exists():
                raise FileExistsError(
                    f"Collision detected at destination: {dst}. "
                    "Disable 'surface' or rename folders."
                )

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(t, dst)

    def _stage_targets_old(self, targets, staging_root: Path):
        """
        Copy target directories into staging_root.

        Each target becomes:
            staging_root/<target_name>/
        """
        for t in targets:
            dst = staging_root / t.name

            if dst.exists():
                raise RuntimeError(f"Duplicate target folder name detected: {t.name}")

            shutil.copytree(t, dst)


# CLASSES -- Module-level
# =======================================================================
# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
