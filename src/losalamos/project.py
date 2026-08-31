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
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import fnmatch
import datetime
import pprint
import tempfile
import shutil
import zipfile
from pathlib import Path
from typing import Union, List, Optional

# ... {develop}

# External imports
# =======================================================================
import pandas as pd
from tqdm import tqdm

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import FileSys
from losalamos.documents import DOCUMENT_TYPES
from losalamos.notes import NoteProject, NoteOrganization, NoteSapiens

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
    :returns: A new :class:`losalamos.Project` instance initialized with the given specifications.
    :rtype: :class:`losalamos.Project`


    .. dropdown:: Example
        :icon: code-square
        :open:

        Import the package.

        .. code-block:: python

            import losalamos

        Define the specification dictionary. ``folder_base`` and ``name`` are required;
        all other keys are optional.

        .. code-block:: python

            project_specs = {
                "folder_base": "C:/path/to/base",
                "name": "newProject",
                "alias": "NPrj",
                "source": "Me",
                "description": "Just a test",
            }

        Create the project.

        .. code-block:: python

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
    Load a Project from a folder path.

    :param project_folder: Path to the project root folder.
    :type project_folder: str or Path
    :returns: A new :class:`losalamos.Project` instance.
    :rtype: :class:`losalamos.Project`

    .. dropdown:: Example
        :icon: code-square
        :open:

        Import the package.

        .. code-block:: python

            import losalamos

        Load an existing project by pointing to its root folder.

        .. code-block:: python

            pj = losalamos.load_project(project_folder="path/to/project/folder")

    """
    if os.path.isdir(project_folder):
        name = os.path.basename(project_folder)
        folder_base = os.path.abspath(Path(project_folder).parent)
        p = Project(name=name, alias=name)
        p.name = name
        p.folder_base = folder_base

        # update project
        p.update()

        # setup
        p.setup()

        return p
    else:
        raise ValueError(f"Project folder not found: {project_folder}'")


def archive(
    sources: Union[str, Path, List[Union[str, Path]]],
    folder: Union[str, Path],
    name: str,
    ignore_subfolders: bool = False,
    ignore_names: Optional[List[str]] = None,
    ignore_patterns: Optional[List[str]] = None,
) -> Path:
    """
    Archive one or more files/folders into a single timestamped zip file.

    Sources are merged into a shared tree at the zip root rather than being
    namespaced under separate top-level folders — equivalent to pasting each
    source folder into the same destination one after another. Same-named
    subfolders combine their contents non-destructively. A file present in
    only one source appears once in the result; a relative path present in
    more than one source raises an error rather than silently overwriting.

    :param sources: A single path or a list of paths (files and/or folders) to merge and include.
    :type sources: str, pathlib.Path, or list
    :param folder: Target folder where the zip file will be written. Must already exist.
    :type folder: str or pathlib.Path
    :param name: Base name for the archive (timestamp is appended).
    :type name: str
    :param ignore_subfolders: If ``True``, only the top-level files of each
        source are archived; all subfolders (and their contents) are skipped.
        Applied independently per source.
    :type ignore_subfolders: bool
    :param ignore_names: Exact folder or file names to exclude, anywhere in
        the tree (e.g. ``["cache", "settings.txt"]``). File names must
        include their extension.
    :type ignore_names: list of str or None
    :param ignore_patterns: Glob-style patterns (``*`` syntax) matched against
        the filename only (not the full path), e.g. ``["*.tmp", "~*"]``.
        Folders are matched the same way by their folder name and, if
        matched, their entire contents are excluded.
    :type ignore_patterns: list of str or None
    :raises NotADirectoryError: If ``folder`` does not exist as a directory.
    :raises FileNotFoundError: If any path in ``sources`` does not exist.
    :raises FileExistsError: If two sources resolve to the same relative path
        in the merged tree (conflicting file).
    :returns: Absolute path to the created zip file.
    :rtype: pathlib.Path

    .. dropdown:: Example
        :icon: code-square
        :open:

        Import the package.

        .. code-block:: python

            import losalamos

        Archive two source folders into a single zip, skipping temporary files
        and a cache subfolder.

        .. code-block:: python

            zip_path = losalamos.archive(
                sources=["path/to/data", "path/to/figures"],
                folder="path/to/output",
                name="myArchive",
                ignore_names=["cache"],
                ignore_patterns=["*.tmp", "~*"],
            )

        The returned path points to the timestamped zip file.

        .. code-block:: python

            print(zip_path)
            # path/to/output/myArchive_20260101T120000.zip

    """
    ignore_names = set(ignore_names or [])
    ignore_patterns = ignore_patterns or []

    def _is_ignored_name(part: str) -> bool:
        if part in ignore_names:
            return True
        for pat in ignore_patterns:
            if fnmatch.fnmatch(part, pat):
                return True
        return False

    def _path_is_ignored(rel_path: Path) -> bool:
        # check every component (folders and filename) against name/pattern rules
        return any(_is_ignored_name(part) for part in rel_path.parts)

    # normalize sources to a list
    # --------------------------------------------------
    if isinstance(sources, (str, Path)):
        sources = [sources]
    sources = [Path(s).absolute() for s in sources]

    # validate target folder
    # --------------------------------------------------
    folder = Path(folder).absolute()
    if not folder.is_dir():
        raise NotADirectoryError(
            f"Target folder does not exist: '{folder}'. "
            "Please create it before calling archive()."
        )

    # validate sources
    # --------------------------------------------------
    for s in sources:
        if not s.exists():
            raise FileNotFoundError(f"Source path does not exist: '{s}'")

    # build merged map of {relative_path: absolute_path}, detecting conflicts
    # --------------------------------------------------
    merged = {}
    for s in tqdm(sources, desc="Scanning sources", unit="source"):
        if s.is_file():
            if _is_ignored_name(s.name):
                continue
            files = {Path(s.name): s}
        else:
            if ignore_subfolders:
                candidates = [f for f in s.iterdir() if f.is_file()]
            else:
                candidates = [f for f in s.rglob("*") if f.is_file()]

            files = {}
            for f in candidates:
                rel = f.relative_to(s)
                if _path_is_ignored(rel):
                    continue
                files[rel] = f

        for rel_path, abs_path in files.items():
            if rel_path in merged:
                raise FileExistsError(
                    f"Conflicting path across sources: '{rel_path}' "
                    f"(from '{abs_path}' and '{merged[rel_path]}')"
                )
            merged[rel_path] = abs_path

    # build timestamp and output path
    # --------------------------------------------------
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    zip_name = f"{name}_{timestamp}.zip"
    zip_path = folder / zip_name

    # write zip
    # --------------------------------------------------
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path, abs_path in tqdm(
            merged.items(), desc="Writing archive", unit="file"
        ):
            zf.write(abs_path, arcname=rel_path)

    return zip_path


def publish(
    sources: Union[str, Path, List[Union[str, Path]]],
    folder: Union[str, Path],
    name: str,
    ignore_subfolders: bool = False,
    ignore_names: Optional[List[str]] = None,
    ignore_patterns: Optional[List[str]] = None,
) -> Path:
    """
    Archive ``sources`` and publish the result under a managed
    ``history``/``latest`` structure.

    Builds (or reuses) a folder layout at ``folder/name/`` containing two
    subfolders, ``history`` and ``latest``. The new archive is built
    directly into ``latest`` first; only after it is successfully created
    is the previously-existing zip (if any) moved into ``history``. This
    ordering ensures that if archiving fails, ``latest`` still holds the
    last good publish rather than being left empty or having prematurely
    rotated a valid zip away. Each zip keeps its own timestamped filename
    from :func:`archive`, so nothing is overwritten on rotation.

    :param sources: A single path or a list of paths (files and/or folders) to merge and archive. See :func:`archive`.
    :type sources: str, pathlib.Path, or list
    :param folder: Output archive main folder. The managed structure is
        created at ``folder/name/``. Must already exist.
    :type folder: str or pathlib.Path
    :param name: Base name for the archive and the managed subfolder under
        ``folder``.
    :type name: str
    :param ignore_subfolders: See :func:`archive`.
    :type ignore_subfolders: bool
    :param ignore_names: See :func:`archive`.
    :type ignore_names: list of str or None
    :param ignore_patterns: See :func:`archive`.
    :type ignore_patterns: list of str or None
    :raises NotADirectoryError: If ``folder`` does not exist as a directory.
    :raises FileNotFoundError: If any path in ``sources`` does not exist.
    :raises FileExistsError: If two sources resolve to the same relative path
        in the merged tree (conflicting file).
    :returns: Absolute path to the newly published zip file inside ``latest``.
    :rtype: pathlib.Path

    .. dropdown:: Example
        :icon: code-square
        :open:

        Import the package.

        .. code-block:: python

            import losalamos

        Publish two source folders to a managed output location. On the first
        call the ``latest`` subfolder is created; on subsequent calls the
        previous zip is rotated into ``history`` before the new one is written.

        .. code-block:: python

            zip_path = losalamos.publish(
                sources=["path/to/data", "path/to/figures"],
                folder="path/to/output",
                name="myDeliverable",
                ignore_patterns=["*.tmp"],
            )

        The returned path points to the new zip inside ``latest``.

        .. code-block:: python

            print(zip_path)
            # path/to/output/myDeliverable/latest/myDeliverable_20260101T120000.zip

    """
    folder = Path(folder).absolute()
    if not folder.is_dir():
        raise NotADirectoryError(
            f"Target folder does not exist: '{folder}'. "
            "Please create it before calling publish()."
        )

    # set up managed structure: folder/name/{history,latest}
    # --------------------------------------------------
    root = folder / name
    folder_history = root / "history"
    folder_latest = root / "latest"
    folder_history.mkdir(parents=True, exist_ok=True)
    folder_latest.mkdir(parents=True, exist_ok=True)

    # snapshot what's currently in latest BEFORE building the new archive
    # --------------------------------------------------
    previous_zips = [
        f for f in folder_latest.iterdir() if f.is_file() and f.suffix == ".zip"
    ]

    # build the new archive directly into latest
    # if this raises, 'latest' still holds the previous good zip untouched
    # --------------------------------------------------
    zip_path = archive(
        sources=sources,
        folder=folder_latest,
        name=name,
        ignore_subfolders=ignore_subfolders,
        ignore_names=ignore_names,
        ignore_patterns=ignore_patterns,
    )

    # only now rotate the previously-existing zip(s) into history
    # --------------------------------------------------
    for existing in tqdm(previous_zips, desc="Rotating to history", unit="file"):
        shutil.move(str(existing), str(folder_history / existing.name))

    return zip_path


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

        self.main_note_path = None
        self.main_note = None

        self.contractor_path = None
        self.contractor = None
        self.contractor_note_path = None
        self.contractor_note = None

        self.documents = {}

        self.sources = {}


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

    def update(self):
        """
        Refresh derived attributes from the current configuration.

        Calls the parent :meth:`FileSys.update` and then resolves
        ``folder_base``, ``folder_root``, and ``main_note_path`` as
        :class:`pathlib.Path` objects when ``folder_base`` is set.
        Loads the main project note only if the file already exists on disk.
        """
        super().update()
        if self.folder_base is not None:
            self.folder_base = Path(self.folder_base)
            self.folder_root = Path(self.folder_root)
            self.main_note_path = self.folder_base / self.name / f"{self.name}.md"
            if self.main_note_path.exists():
                self.load_main_note()


    def load_main_note(self):
        """
        Load the project's main Markdown note from disk.

        Reads ``self.main_note_path`` and stores the resulting
        :class:`~losalamos.notes.NoteProject` in ``self.main_note``.
        """
        self.main_note = NoteProject(name=self.name, alias=self.alias)
        self.main_note.load(file_note=self.main_note_path)
        return None

    def get_title(self):

        return self.get_attribute(entry_key="title",  clean_cref=True)

    def get_subtitle(self):
        return self.get_attribute(entry_key="subtitle", clean_cref=True)

    def get_contractor(self):
        return self.get_attribute(entry_key="contractor", clean_cref=True)

    def get_contractor_sapiens(self):
        return self.get_attribute(entry_key="contractor_sapiens", clean_cref=True)

    def _collect_md_files(self, sources):
        """Scan directories and return a stem-to-path map of Markdown files."""
        if sources is None:
            return {}
        file_map = {}
        for source in sources:
            for f in Path(source).glob("*.md"):
                file_map[f.stem] = f
        return file_map

    def load_contractor(self):
        """
        Load the contractor note from ``self.sources``.

        Reads the contractor name from the project's main note metadata and
        searches for a matching ``.md`` file in ``self.sources["organizations"]``
        first, then in ``self.sources["sapiens"]``. On success, stores the loaded
        note in ``self.contractor`` and the resolved path in ``self.contractor_path``.

        :raises FileNotFoundError: If no note matching the contractor name is found
            in any configured source.
        :returns: None
        :rtype: None
        """
        contractor = self.get_contractor()

        sources_organizations = self.sources.get("organizations", None)
        sources_sapiens = self.sources.get("sapiens", None)

        # organizations take precedence in the search over individuals
        path = self._collect_md_files(sources_organizations).get(contractor)
        if path is not None:
            note = NoteOrganization(name=contractor, alias=contractor)
            note.load(file_note=path)
            self.contractor_path = path
            self.contractor = note
            return None

        # case for a sapiens contractor
        path = self._collect_md_files(sources_sapiens).get(contractor)
        if path is not None:
            note = NoteSapiens(name=contractor, alias=contractor)
            note.load(file_note=path)
            self.contractor_path = path
            self.contractor = note
            return None

        raise FileNotFoundError(f"No contractor found for '{contractor}'")

    def load_contractor_sapiens(self):
        """
        Load the individual (sapiens) contractor note from ``self.sources``.

        Reads the ``contractor_sapiens`` name from the project's main note
        metadata and searches ``self.sources["sapiens"]`` for a matching
        ``.md`` file. If ``self.contractor`` has not been loaded yet, calls
        :meth:`load_contractor` first. On success, stores the loaded note in
        ``self.contractor_sapiens`` and the resolved path in
        ``self.contractor_sapiens_path``.

        :raises FileNotFoundError: If no note matching the contractor_sapiens
            name is found in the configured sapiens sources.
        :returns: None
        :rtype: None
        """
        contractor_sapiens = self.get_contractor_sapiens()
        sources_sapiens = self.sources.get("sapiens", None)
        if self.contractor is None:
            self.load_contractor()

        path = self._collect_md_files(sources_sapiens).get(contractor_sapiens)
        if path is not None:
            note = NoteSapiens(name=contractor_sapiens, alias=contractor_sapiens)
            note.load(file_note=path)
            self.contractor_sapiens_path = path
            self.contractor_sapiens = note
            return None

        raise FileNotFoundError(f"No sapiens found for '{contractor_sapiens}'")

    def get_attribute(self, entry_key, clean_cref=True):
        s = self.main_note.metadata.get(entry_key, f"[{entry_key.upper()}]")
        s = s.strip("\"'")  # YAML frontmatter sometimes preserves surrounding quotes
        if clean_cref:
            s = NoteProject.clean_cref(entry_key=s)
        return s


    def add_document(
            self,
            document_type,
            name=None,
            template_overlay=None,
            condensed=True,
            zip_export=False,
            compile_pdf=True,
            subfolder="inputs/documents",
            force_new=False,
    ):
        """
        Create a new document inside the project, optionally condensed
        into a flattened+split pair of files and/or compiled to PDF.

        :param document_type: Key into :data:`losalamos.documents.DOCUMENT_TYPES`.
        :type document_type: str
        :param name: Folder/registry name. Defaults to ``document_type``.
            Must be non-empty and free of path separators.
        :type name: str or None
        :param template_overlay: Forwarded to :meth:`Document.new`.
        :type template_overlay: str, pathlib.Path, or None
        :param condensed: If True, flatten+split into main.tex/preamble.tex
            via a temp staging dir. If False, keep the live template tree.
        :type condensed: bool
        :param zip_export: Zip the condensed export (deletes the folder).
            Requires condensed=True; mutually exclusive with compile_pdf.
        :type zip_export: bool
        :param compile_pdf: Compile to PDF via :meth:`DocumentTeX.to_pdf`.
        :type compile_pdf: bool
        :param subfolder: Project-relative target folder.
        :type subfolder: str
        :param force_new: If True, force the new folder even if it already exists.
        :type force_new: bool
        :raises ValueError: Unknown document_type; invalid name; or
            zip_export combined with condensed=False or compile_pdf=True.
        :raises FileExistsError: Target folder already exists.
        :returns: The reloaded document instance, or the zip Path when
            zip_export=True.
        :rtype: losalamos.documents.Document or pathlib.Path

        .. dropdown:: Example
            :icon: code-square
            :open:

            Load an existing project.

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")

            Add an invoice document. The template is condensed into a flat
            ``main.tex`` / ``preamble.tex`` pair and compiled to PDF.

            .. code-block:: python

                doc = pj.add_document(
                    document_type="invoice",
                    name="invoice_client_2026",
                    condensed=True,
                    compile_pdf=True,
                )

            The returned instance is also registered in ``pj.documents``.

            .. code-block:: python

                print(pj.documents["invoice"])

        """
        if document_type not in DOCUMENT_TYPES:
            raise ValueError(
                f"Unknown document type: '{doc}'. "
                f"Available types: {sorted(DOCUMENT_TYPES)}"
            )

        if name is None:
            name = document_type

        documents_folder = Path(self.folder_root) / subfolder
        documents_folder.mkdir(parents=True, exist_ok=True)

        target_folder = documents_folder

        if force_new:
            dst_folder = target_folder / name
            if dst_folder.exists():
                shutil.rmtree(str(target_folder / name))

        klass = DOCUMENT_TYPES[document_type]

        if condensed:
            target_folder = Path(tempfile.mkdtemp(prefix="losalamos_add_doc_"))

        instance = klass(name=name)

        instance.new(
            folder=target_folder,
            name=name,
            template_overlay=template_overlay
        )

        if condensed:
            instance.export(name=name, folder_root=documents_folder, flatten=True, split=True, zip_export=zip_export)
            shutil.rmtree(target_folder)
            target_folder = documents_folder / name

        return_instance = klass(name=name)
        return_instance.load_data(file_data=target_folder / name / "main.tex")

        if compile_pdf:
            return_instance.to_pdf()

        self.documents[document_type] = return_instance

        return return_instance





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

             The method performs directory validation, checks for publish frequency constraints
             based on ``self.publish_delta``, and handles the rotation of the previous 'latest'
             archive into a history folder before promoting the new build.

        .. dropdown:: Example
            :icon: code-square
            :open:

            Load an existing project.

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")

            Select the output folders to snapshot and trigger the publish. By
            default the archive lands under ``<project_root>/outputs/``.

            .. code-block:: python

                result = pj.publish(
                    targets=[
                        pj.folder_root / "outputs/public",
                        pj.folder_root / "inputs/figures",
                    ],
                    prefix="myProject_delivery",
                )

            Inspect the result dictionary to confirm publication and retrieve
            the archive path.

            .. code-block:: python

                if result["published"]:
                    print(result["archive"])
                else:
                    print("Skipped:", result["reason"])

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
        """Yield all files under ``root`` recursively."""
        for path in root.rglob("*"):
            if path.is_file():
                yield path

    def _zip_with_tqdm(self, src_root: Path, dst_zip: Path):
        """Write all files from ``src_root`` into ``dst_zip`` with a progress bar."""
        files = list(self._iter_files(src_root))
        total_bytes = sum(f.stat().st_size for f in files)

        with tqdm(total=total_bytes, unit="B", unit_scale=True) as bar:
            with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    zf.write(f, f.relative_to(src_root))
                    bar.update(f.stat().st_size)

    def _ensure_publish_dirs(self, output_folder: Path):
        """Create and return the ``latest`` and ``history`` subdirectories under ``output_folder``."""
        output_folder = Path(output_folder)
        latest = output_folder / "latest"
        history = output_folder / "history"

        latest.mkdir(parents=True, exist_ok=True)
        history.mkdir(parents=True, exist_ok=True)

        return latest, history

    def _find_latest(self, latest_dir: Path, prefix: str):
        """Return the single versioned zip matching ``prefix`` in ``latest_dir``, or ``None``."""
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
