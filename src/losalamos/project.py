# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Project management and filesystem initialization utilities.

Defines :class:`Project` and the convenience functions :func:`new_project`
and :func:`load_project` for working with projects organized around a fixed
folder layout (``admin/``, ``inputs/``, ``outputs/``, ``budget/``).

Each project carries a main Markdown note with metadata (title, client,
contractor, service, etc.). An optional *sources* configuration connects
the project to external note libraries and drives automatic generation of
the TeX definition overlays (``party_a.tex``, ``party_b.tex``,
``project.tex``, ``service.tex``) consumed by document templates.
"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import os
import fnmatch
import re
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
from losalamos.root import FileSys, MbaE
from losalamos.documents import DOCUMENT_TYPES
from losalamos.notes import (
    NoteProject,
    NoteOrganization,
    NoteSapiens,
    NoteBasic,
    NoteAsset,
    NoteTransfer,
)
from losalamos.paths import FOLDER_TEMPLATES, FOLDER_TEMPLATES_CONFIG_PROJECT

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
        "admin/paperwork",
        "admin/meetings",
        "admin/received",
        "admin/messages",
        "admin/config",
        "admin/config/overlays",
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

# Human-readable document type labels per language.
# Keys are BCP-47 language tags (lowercase). Add new languages here.
_DOC_TYPE_LABELS = {
    "en": {
        "invoice": "Invoice",
        "receipt": "Receipt",
        "proposal": "Proposal",
    },
    "pt-br": {
        "invoice": "Cobrança",
        "receipt": "Recibo",
        "proposal": "Proposta",
    },
}

# FUNCTIONS
# ***********************************************************************


# FUNCTIONS -- Project-level
# =======================================================================
def _load_config(source):
    """
    Parse a config dict from a ``.json``, ``.yaml``/``.yml``, or ``.toml`` file.

    :param source: Path to the config file.
    :type source: str or pathlib.Path
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If the file extension is not supported.
    :raises ImportError: If the required parser is not installed.
    :returns: Parsed configuration dict.
    :rtype: dict
    """
    return MbaE.load_config_file(path=source)


def new_project(config):
    """
    Create a new Project from a configuration dictionary or file.

    Builds the project folder structure, installs the main Markdown note
    populated from ``config``, copies the sources config file if one is
    provided, then reloads the project so that all metadata and overlays
    are current on return.

    .. danger::

        This method overwrites all existing default files.

    :param config: Project configuration. Either a mapping or a path to a
        ``.yaml``/``.toml``/``.json`` file.

        **Required keys**:

        - ``folder_base`` (*str*): Directory in which the project folder is created.
        - ``name`` (*str*): Project folder name.

        **Filesystem keys** (not written to the note):

        - ``alias`` (*str*): Short identifier. Defaults to ``None``.
        - ``source`` (*str*): Source reference. Defaults to empty string.
        - ``description`` (*str*): Project description. Defaults to empty string.
        - ``sources`` (*str*): Path to a ``.yaml``/``.toml``/``.json`` sources
          config to copy into ``admin/config/``. Defaults to ``None``.

        **Note metadata keys** (any field accepted by the project note template):

        - ``title``, ``subtitle``, ``subject``, ``category``
        - ``status`` — defaults to ``"on going"`` if not provided
        - ``aliases`` — defaults to ``["{name} project", "Project {name}"]``
        - ``activity_id``, ``service_id``, ``professional_id``
        - ``contractor``, ``contractor_sapiens``, ``client``, ``client_sapiens``
        - ``date_start``, ``date_end``, ``revenue_expected``

    :type config: dict, str, or pathlib.Path
    :raises FileNotFoundError: If a file path is given for ``config`` or
        ``sources`` and the file does not exist.
    :raises ValueError: If any required key is missing or the project folder
        already exists.
    :returns: A new :class:`losalamos.Project` instance with the main note
        and sources config installed.
    :rtype: :class:`losalamos.Project`

    .. dropdown:: Example — inline dict
        :icon: code-square
        :open:

        .. code-block:: python

            import losalamos

            pj = losalamos.new_project(config={
                "folder_base": "C:/projects",
                "name": "Survey2026",
                "alias": "SV26",
                "title": "Environmental Survey 2026",
                "status": "planning",
                "sources": "/vault/sources.toml",
            })

    .. dropdown:: Example — TOML config file
        :icon: code-square
        :open:

        Save a ``project-config.toml``:

        .. code-block:: toml

            folder_base = "/home/user/projects"
            name = "Survey2026"
            alias = "SV26"
            title = "Environmental Survey 2026"
            status = "planning"
            sources = "/vault/sources.toml"

        Then create the project:

        .. code-block:: python

            import losalamos

            pj = losalamos.new_project(config="project-config.toml")

    """
    # Parse config from file if a path was given
    if isinstance(config, (str, Path)):
        config = _load_config(config)

    # Required keys
    required = ["folder_base", "name"]
    for key in required:
        if key not in config:
            raise ValueError(f"Missing required key: '{key}'")

    # System-level keys — applied to the Project object, not the note
    _SYSTEM_KEYS = {"folder_base", "name", "source", "description", "sources", "branch"}
    # Note fields that store cross-note references and need Obsidian wiki-link syntax
    _LINK_FIELDS = {
        "contractor",
        "contractor_sapiens",
        "client",
        "client_sapiens",
        "service_id",
    }

    name = config["name"]
    alias = config.get("alias", None)
    sources_file = config.get("sources", None)
    branch = config.get("branch", None)

    # Create project folder structure
    os.makedirs(config["folder_base"], exist_ok=True)
    if branch is not None:
        folder_root = Path(config["folder_base"]) / branch / name
    else:
        folder_root = Path(config["folder_base"]) / name
    if os.path.isdir(folder_root):
        raise ValueError(f"Project folder already exists '{folder_root}'")

    p = Project(name=name, alias=alias)
    p.branch = branch
    p.source = config.get("source", "")
    p.description = config.get("description", "")
    p.folder_base = config["folder_base"]
    p.update()

    # Pre-place sources file before setup() so _install_config_templates sees
    # it and skips creating a blank template of a different format.
    if sources_file is not None:
        src = Path(sources_file)
        if not src.is_file():
            raise FileNotFoundError(f"Sources config file not found: '{src}'")
        config_dir = Path(p.folder_root) / "admin/config"
        config_dir.mkdir(parents=True, exist_ok=True)
        dst = config_dir / f"sources{src.suffix}"
        shutil.copy2(str(src), str(dst))

    p.setup()

    # Create main project note
    note_file = Path(p.folder_root) / f"{name}.md"
    n = NoteProject(name=name, alias=alias or name)
    n.load_new(file_note=note_file)

    # Set core identity fields
    n.metadata["name"] = name
    # Apply defaults that config may override
    n.metadata["aliases"] = [f"{name} project", f"Project {name}"]
    n.metadata["status"] = "on going"

    # Apply all note-level fields from config (overrides defaults above)
    note_fields = {k: v for k, v in config.items() if k not in _SYSTEM_KEYS}
    for k, v in note_fields.items():
        if k in n.metadata:
            n.metadata[k] = f'"[[{v}]]"' if k in _LINK_FIELDS else v

    n.update()
    n.save()

    # Reload so main_note, sources, and overlays are current on return
    p.update()
    p._setup_remote_folders()

    return p


def load_project(project_folder, vault=None):
    """
    Load a Project from a folder path.

    If ``admin/config/sources.toml`` (or ``.yaml``/``.json``) exists in the
    project, it is parsed and merged into :attr:`~Project.sources`
    automatically. Overlay files in ``admin/config/overlays/`` are then
    regenerated from the loaded metadata.

    :param project_folder: Path to the project root folder.
    :type project_folder: str or Path
    :param vault: Optional path to the vault root. When provided and the
        project sits one level below *vault*, :attr:`~Project.branch` is set
        to the intermediate folder name so that remote-folder mirroring
        preserves the full ``vault/branch/name`` layout.
    :type vault: str or Path or None
    :returns: A new :class:`losalamos.Project` instance.
    :rtype: :class:`losalamos.Project`

    .. dropdown:: Example
        :icon: code-square
        :open:

        .. code-block:: python

            import losalamos

            pj = losalamos.load_project(project_folder="path/to/project/folder")

    """
    if os.path.isdir(project_folder):
        project_path = Path(project_folder).resolve()
        name = project_path.name

        if vault is not None:
            vault_path = Path(vault).resolve()
            branch_folder = project_path.parent
            if branch_folder != vault_path:
                folder_base = str(vault_path)
                branch = branch_folder.name
            else:
                folder_base = str(vault_path)
                branch = None
        else:
            folder_base = str(project_path.parent)
            branch = None

        p = Project(name=name, alias=name)
        p.folder_base = folder_base
        p.branch = branch

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

    Extends :class:`~losalamos.root.FileSys` with metadata loading, external
    note resolution, and TeX overlay generation.

    The :attr:`sources` dict maps note categories to lists of directory paths
    scanned when resolving contractors, clients, and services. It is
    auto-populated from ``admin/config/sources.toml`` (also ``.yaml`` or
    ``.json``) each time the project is opened:

    .. code-block:: toml

        # admin/config/sources.toml
        [folders.search]
        organizations = ["/vault/organizations"]   # NoteOrganization notes
        sapiens       = ["/vault/people"]          # NoteSapiens notes
        services      = ["/vault/services"]        # NoteBasic notes, matched by service_id

        [folders.remote]                           # optional remote vault roots
        documents = "/vault/documents"
        data      = "/vault/data"

        [templates.documents]                      # document template directories
        invoice  = "/vault/templates/invoice"
        proposal = "/vault/templates/proposal"

    Overlays are written to ``admin/config/overlays/`` and applied to
    document templates via the ``files_overlay`` parameter of
    :meth:`add_document`.
    """

    def __init__(self, name="LosAlamosProject", alias="LAProj"):
        """
        Initialize a Project instance.

        :param name: Project name.
        :type name: str
        :param alias: Optional short identifier.
        :type alias: str
        """
        # must precede super().__init__() — update() is called during init chain
        self.branch = None
        self.folder_remote_documents = None
        self.folder_remote_data = None
        super().__init__(name=name, alias=alias)
        self.load_data()

        self.publish_force = False
        self.publish_delta = 1  # hour
        self.undefined_fill = "[ --- ]"

        self.main_note_path = None
        self.main_note = None

        self.contractor_path = None
        self.contractor = None
        self.contractor_sapiens_path = None
        self.contractor_sapiens = None

        self.client_path = None
        self.client = None

        self.service_path = None
        self.service = None

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

    def setup(self):
        """
        Set up the project folder structure and install default config templates.

        Delegates folder and file setup to the parent :meth:`FileSys.setup`,
        then copies any missing config templates into ``admin/config/`` via
        :meth:`_install_config_templates`.

        .. danger::

            This method overwrites all existing default files (parent behaviour).
        """
        super().setup()
        self._install_config_templates()
        self._setup_remote_folders()

    def _install_config_templates(self):
        """Copy missing config templates into ``admin/config/``, preferring TOML over YAML over JSON."""
        config_dir = Path(self.folder_root) / "admin/config"
        # rank by preferred format; lower rank wins
        rank = {".toml": 0, ".yaml": 1, ".yml": 2, ".json": 3}
        best = {}
        for src in FOLDER_TEMPLATES_CONFIG_PROJECT.iterdir():
            ext = Path(src.name).suffix.lower()
            if ext not in rank:
                continue
            stem = Path(src.name).stem
            if stem not in best or rank[ext] < best[stem][0]:
                best[stem] = (rank[ext], src)
        for stem, (_, src) in best.items():
            # skip if the stem already exists in any supported format
            if any((config_dir / f"{stem}{ext}").is_file() for ext in rank):
                continue
            dst = config_dir / src.name
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def update(self):
        """
        Refresh derived attributes from the current configuration.

        Calls the parent :meth:`FileSys.update` and then resolves
        ``folder_base``, ``folder_root``, and ``main_note_path`` as
        :class:`pathlib.Path` objects when ``folder_base`` is set.
        Loads the main project note only if the file already exists on disk,
        then attempts to regenerate overlay files via :meth:`_update_overlays`.
        """
        super().update()
        if self.folder_base is not None:
            self.folder_base = Path(self.folder_base)
            if self.branch is not None:
                self.folder_root = Path(self.folder_base) / self.branch / self.name
            else:
                self.folder_root = Path(self.folder_base) / self.name
            self.main_note_path = self.folder_root / f"{self.name}.md"
            if self.main_note_path.exists():
                self.load_main_note()
                self._load_sources_config()
                self._update_overlays()
            self._resolve_remote_folders()

    def _resolve_remote_folders(self):
        """
        Resolve ``folder_remote_documents`` and ``folder_remote_data`` from
        ``self.sources``.

        Uses the relative offset of ``folder_root`` from ``folder_base`` to
        mirror the vault layout (including any branch tier) into the remote
        root. Falls back to ``folder_root`` when the key is absent or blank.
        """
        try:
            rel = self.folder_root.relative_to(self.folder_base)
        except (ValueError, TypeError):
            rel = Path(self.name)

        remote = self.sources.get("folders", {}).get("remote", {})

        docs_root = remote.get("documents", "")
        if docs_root:
            self.folder_remote_documents = Path(docs_root) / rel
        else:
            self.folder_remote_documents = self.folder_root

        data_root = remote.get("data", "")
        if data_root:
            self.folder_remote_data = Path(data_root) / rel
        else:
            self.folder_remote_data = self.folder_root

    def _setup_remote_folders(self):
        """
        Create curated remote-vault subfolders when a remote root is configured.

        Only acts when the resolved remote path differs from ``folder_root``
        (i.e. a remote root was actually set in sources). Safe to call multiple
        times; existing folders are skipped.
        """
        if (
            self.folder_remote_documents is not None
            and self.folder_remote_documents != self.folder_root
        ):
            self.setup_subfolders(
                root=self.folder_remote_documents,
                folder_list=["inputs/documents"],
            )
        if (
            self.folder_remote_data is not None
            and self.folder_remote_data != self.folder_root
        ):
            self.setup_subfolders(
                root=self.folder_remote_data,
                folder_list=["inputs/data"],
            )

    def _update_overlays(self):
        """Regenerate overlay files; party_b and service overlays skip silently if sources are not configured."""
        self.make_overlay_project()
        self.contractor = None
        self.contractor_sapiens = None
        self.client = None
        self.service = None
        try:
            self.make_overlay_party_b_contractor()
        except FileNotFoundError:
            pass
        try:
            self.make_overlay_party_b_client()
        except FileNotFoundError:
            pass
        try:
            self.make_overlay_service()
        except FileNotFoundError:
            pass

    def _load_sources_config(self):
        """
        Load ``self.sources`` from ``admin/config/sources.*`` if present.

        Checks for ``sources.toml``, ``sources.yaml``, ``sources.yml``, and
        ``sources.json`` in that order; the first match is parsed and merged
        into :attr:`sources`. Parse errors and missing files are silently
        ignored.
        """
        config_dir = Path(self.folder_root) / "admin/config"
        for fname in ("sources.toml", "sources.yaml", "sources.yml", "sources.json"):
            path = config_dir / fname
            if not path.is_file():
                continue
            try:
                data = self.load_config_file(path=path)
                if isinstance(data, dict):
                    self.sources.update(data)
            except Exception:
                pass
            return

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
        """Return the project title from the main note metadata."""
        return self.get_attribute(entry_key="title", clean_cref=True)

    def get_subtitle(self):
        """Return the project subtitle from the main note metadata."""
        return self.get_attribute(entry_key="subtitle", clean_cref=True)

    def get_contractor(self):
        """Return the contractor name from the main note metadata."""
        return self.get_attribute(entry_key="contractor", clean_cref=True)

    def get_contractor_sapiens(self):
        """Return the contractor's individual representative name from the main note metadata."""
        return self.get_attribute(entry_key="contractor_sapiens", clean_cref=True)

    def get_client(self):
        """Return the client name from the main note metadata."""
        return self.get_attribute(entry_key="client", clean_cref=True)

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

        :attr:`sources` is populated automatically from
        ``admin/config/sources.toml`` on project load; it can also be set
        manually before calling this method.

        :raises FileNotFoundError: If no note matching the contractor name is found
            in any configured source.
        :returns: None
        :rtype: None
        """
        contractor = self.get_contractor()

        search = self.sources.get("folders", {}).get("search", {})
        sources_organizations = search.get("organizations", None)
        sources_sapiens = search.get("sapiens", None)

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
        sources_sapiens = (
            self.sources.get("folders", {}).get("search", {}).get("sapiens", None)
        )
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

    def load_client(self):
        """
        Load the client note from ``self.sources``.

        Reads the client name from the project's main note metadata and
        searches for a matching ``.md`` file in ``self.sources["organizations"]``
        first, then in ``self.sources["sapiens"]``. On success, stores the loaded
        note in ``self.client`` and the resolved path in ``self.client_path``.

        :attr:`sources` is populated automatically from
        ``admin/config/sources.toml`` on project load; it can also be set
        manually before calling this method.

        :raises FileNotFoundError: If no note matching the client name is found
            in any configured source.
        :returns: None
        :rtype: None
        """
        client = self.get_client()

        search = self.sources.get("folders", {}).get("search", {})
        sources_organizations = search.get("organizations", None)
        sources_sapiens = search.get("sapiens", None)

        # organizations take precedence in the search over individuals
        path = self._collect_md_files(sources_organizations).get(client)
        if path is not None:
            note = NoteOrganization(name=client, alias=client)
            note.load(file_note=path)
            self.client_path = path
            self.client = note
            return None

        path = self._collect_md_files(sources_sapiens).get(client)
        if path is not None:
            note = NoteSapiens(name=client, alias=client)
            note.load(file_note=path)
            self.client_path = path
            self.client = note
            return None

        raise FileNotFoundError(f"No client found for '{client}'")

    def load_service(self):
        """
        Load the service note from ``self.sources``.

        Reads ``service_id`` from the project's main note metadata and
        searches ``self.sources["services"]`` for a matching ``.md`` file.
        The service name is expected in the note's ``abstract`` field. On
        success, stores the loaded note in ``self.service`` and the resolved
        path in ``self.service_path``.

        :attr:`sources` is populated automatically from
        ``admin/config/sources.toml`` on project load; it can also be set
        manually before calling this method.

        :raises FileNotFoundError: If no note matching the service_id is found
            in the configured services sources.
        :returns: None
        :rtype: None
        """
        service_id = self.get_attribute(entry_key="service_id", clean_cref=True)
        sources_services = (
            self.sources.get("folders", {}).get("search", {}).get("services", None)
        )

        path = self._collect_md_files(sources_services).get(service_id)
        if path is not None:
            note = NoteBasic(name=service_id, alias=service_id)
            note.load(file_note=path)
            self.service_path = path
            self.service = note
            return None

        raise FileNotFoundError(f"No service found for '{service_id}'")

    def make_overlay_service(self):
        """
        Create a ``service.tex`` overlay from the project's service data.

        Loads :attr:`service` if not yet set. The service ID is read from the
        project note's ``service_id`` field; the service name is read from
        the :attr:`service` note's ``abstract`` field.

        :raises FileNotFoundError: If the service note cannot be found in
            ``self.sources``.
        :returns: Path to the written overlay file.
        :rtype: pathlib.Path

        .. dropdown:: Example — sources via config file
            :icon: code-square
            :open:

            Place ``sources.toml`` in the project's ``admin/config/`` folder:

            .. code-block:: toml

                [folders.search]
                services = ["/vault/services"]   # folder containing <service_id>.md files

            The file is read automatically on project load. Each service note
            must have an ``abstract`` metadata field with the display name:

            .. code-block:: yaml

                # /vault/services/7891.md (front-matter excerpt)
                abstract: "Environmental Assessment"

            Then generate the overlay:

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")
                path = pj.make_overlay_service()
                # → <project>/admin/config/overlays/service.tex

        .. dropdown:: Example — sources set manually
            :icon: code-square
            :open:

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")
                pj.sources = {"folders": {"search": {"services": ["path/to/service/notes"]}}}

                path = pj.make_overlay_service()
        """
        if self.service is None:
            self.load_service()

        service_id = self.get_attribute(entry_key="service_id", clean_cref=True)
        service_name = self._meta(self.service.metadata, "abstract")

        placeholders = {
            "[Service name]": service_name if service_name else self.undefined_fill,
            "[Service ID]": service_id if service_id else self.undefined_fill,
        }
        return self.make_overlay_file(
            name="service",
            source_file="documents/tex/professional/base/definitions/service.tex",
            placeholders=placeholders,
        )

    def make_overlay_file(self, name, source_file, placeholders=None):
        """
        Create a populated overlay file from a template.

        Reads ``source_file``, replaces every key in ``placeholders`` with its
        corresponding value, and writes the result to the project's overlay
        folder (``admin/config/overlays/``).

        :param name: Base name for the output file, without extension. The
            extension is taken from ``source_file``. If ``name`` already carries
            the correct extension it is used as-is.
        :type name: str
        :param source_file: Template to use as the source. An absolute path is
            used directly; a relative path is resolved from the package's
            ``data/templates`` folder.
        :type source_file: str or pathlib.Path
        :param placeholders: Mapping of literal strings to find in the template
            to their replacement values. Each key is replaced everywhere it
            appears. Defaults to ``None`` (file copied verbatim).
        :type placeholders: dict or None
        :raises FileNotFoundError: If the resolved ``source_file`` does not exist.
        :returns: Path to the written overlay file.
        :rtype: pathlib.Path
        """
        source = Path(source_file)
        if not source.is_absolute():
            source = FOLDER_TEMPLATES / source_file

        if not source.is_file():
            raise FileNotFoundError(f"Overlay source file not found: '{source}'")

        # determine output filename: append source extension unless already present
        suffix = source.suffix
        name_path = Path(name)
        if name_path.suffix.lower() == suffix.lower():
            output_name = name_path.name
        else:
            output_name = name_path.stem + suffix

        content = source.read_text(encoding="utf-8")
        if placeholders:
            for placeholder, value in placeholders.items():
                content = content.replace(placeholder, str(value))

        output_dir = Path(self.folder_root) / "admin/config/overlays"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_name
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def _meta(self, metadata, key):
        """Read a metadata value and strip surrounding YAML quote artifacts."""
        v = metadata.get(key) or ""
        return str(v).strip("\"'")

    def _build_party_b_placeholders(self, entity, representative=None):
        """
        Build the placeholder dict for a ``party_b.tex`` overlay from note objects.

        Handles two entity types:

        - :class:`~losalamos.notes.NoteOrganization` — org fields (name, type,
          CNPJ, address) are drawn from the entity; representative fields are
          drawn from ``representative`` when provided, or left empty otherwise.
        - :class:`~losalamos.notes.NoteSapiens` — entity acts directly; all
          party-B fields (including representative fields) are populated from
          the same note using CPF as the ID type.

        :param entity: The party — an organization or an individual.
        :type entity: :class:`~losalamos.notes.NoteOrganization` or :class:`~losalamos.notes.NoteSapiens`
        :param representative: The person representing the organization. Ignored
            when ``entity`` is a :class:`~losalamos.notes.NoteSapiens`.
        :type representative: :class:`~losalamos.notes.NoteSapiens` or None
        :returns: Placeholder mapping suitable for :meth:`make_overlay_file`.
            Empty fields are replaced with :attr:`undefined_fill`.
        :rtype: dict
        """
        m = entity.metadata

        if isinstance(entity, NoteOrganization):
            placeholders = {
                "[Client name]": self._meta(m, "name"),
                "[Client type]": self._meta(m, "org_type"),
                "[ID category]": "CNPJ",
                "[Client ID]": self._meta(m, "cnpj"),
                "[Client address]": self._meta(m, "address"),
            }
            r = representative.metadata if representative is not None else {}
            placeholders.update(
                {
                    "[Representative name]": self._meta(r, "name"),
                    "[Representative role]": self._meta(r, "profession"),
                    "[Representative ID category]": self._meta(r, "civil_id_type")
                    or "CPF",
                    "[Representantive ID]": self._meta(r, "civil_id")
                    or self._meta(r, "cpf"),
                    "[Phone]": self._meta(r, "phone"),
                    "[Email]": self._meta(r, "email_pro") or self._meta(r, "email"),
                    "[Profession]": self._meta(r, "profession"),
                    "[Professional council]": self._meta(r, "profession_org"),
                    "[Professional ID]": self._meta(r, "profession_id"),
                    "[Degree]": self._meta(r, "degree"),
                }
            )
        else:  # NoteSapiens — individual acting directly
            placeholders = {
                "[Client name]": self._meta(m, "name"),
                "[Client type]": "Individual",
                "[ID category]": self._meta(m, "civil_id_type") or "CPF",
                "[Client ID]": self._meta(m, "civil_id") or self._meta(m, "cpf"),
                "[Client address]": self._meta(m, "address"),
                "[Representative name]": self._meta(m, "name"),
                "[Representative role]": self._meta(m, "profession"),
                "[Representative ID category]": self._meta(m, "civil_id_type") or "CPF",
                "[Representantive ID]": self._meta(m, "civil_id")
                or self._meta(m, "cpf"),
                "[Phone]": self._meta(m, "phone"),
                "[Email]": self._meta(m, "email_pro") or self._meta(m, "email"),
                "[Profession]": self._meta(m, "profession"),
                "[Professional council]": self._meta(m, "profession_org"),
                "[Professional ID]": self._meta(m, "profession_id"),
                "[Degree]": self._meta(m, "degree"),
            }

        return {k: (v if v else self.undefined_fill) for k, v in placeholders.items()}

    def make_overlay_project(self):
        """
        Create a ``project.tex`` overlay populated from the project's main note.

        Fills only the fields that are known at the project level:

        - ``[Document Field]`` — the ``subject`` metadata field, with surrounding
          quotes and wiki-link brackets stripped automatically.
        - ``[Project ID]`` — the project name (``self.name``).

        All remaining placeholders (``[Document Type]``, ``[Certifier]``, etc.)
        are left unchanged in the output file for downstream overlays or manual
        editing.

        :raises FileNotFoundError: If the built-in ``project.tex`` template is
            missing.
        :returns: Path to the written overlay file.
        :rtype: pathlib.Path

        .. dropdown:: Example
            :icon: code-square
            :open:

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")

                path = pj.make_overlay_project()
                # → <project>/admin/config/overlays/project.tex

            The file can then be passed to :meth:`add_document`:

            .. code-block:: python

                pj.add_document(
                    document_type="invoice",
                    files_overlay={"definitions/project.tex": path},
                )
        """
        subject = self.get_attribute(entry_key="subject", clean_cref=True)
        placeholders = {
            "[Document Field]": subject if subject else self.undefined_fill,
            "[Project ID]": self.name,
        }
        return self.make_overlay_file(
            name="project",
            source_file="documents/tex/professional/base/definitions/project.tex",
            placeholders=placeholders,
        )

    def make_overlay_party_b_contractor(self):
        """
        Create a ``party_b_contractor.tex`` overlay from the project's contractor data.

        Loads :attr:`contractor` if not yet set. When the contractor is an
        organization, also loads :attr:`contractor_sapiens` as the representative.
        Delegates to :meth:`make_overlay_file` using the built-in ``party_b.tex``
        template.

        Two scenarios are handled automatically:

        **Contractor is an organization** — :attr:`contractor` is a
        :class:`~losalamos.notes.NoteOrganization`; :attr:`contractor_sapiens`
        provides the representative's fields. Both must be resolvable from
        ``self.sources``.

        **Contractor is an individual** — :attr:`contractor` is a
        :class:`~losalamos.notes.NoteSapiens`; all party-B fields (entity and
        representative) are derived from the same note.

        :raises FileNotFoundError: If the contractor or sapiens representative
            cannot be found in ``self.sources``.
        :returns: Path to the written overlay file.
        :rtype: pathlib.Path

        .. dropdown:: Example — organization contractor with representative
            :icon: code-square
            :open:

            The project note has ``contractor: AMA Consultoria`` and
            ``contractor_sapiens: John Doe``.

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")
                pj.sources = {
                    "folders": {
                        "search": {
                            "organizations": ["path/to/org/notes"],
                            "sapiens": ["path/to/people/notes"],
                        }
                    }
                }

                path = pj.make_overlay_party_b_contractor()
                # → <project>/admin/config/overlays/party_b_contractor.tex
                # org fields from "AMA Consultoria.md", rep fields from "John Doe.md"

            The resulting file can be passed directly to :meth:`add_document`:

            .. code-block:: python

                pj.add_document(
                    document_type="contract",
                    files_overlay={"definitions/party_b.tex": path},
                )

        .. dropdown:: Example — individual contractor
            :icon: code-square
            :open:

            The project note has ``contractor: John Doe`` (no ``contractor_sapiens``).

            .. code-block:: python

                pj.sources = {"sapiens": ["path/to/people/notes"]}

                path = pj.make_overlay_party_b_contractor()
                # entity and representative fields both come from "John Doe.md"
        """
        if self.contractor is None:
            self.load_contractor()

        representative = None
        if isinstance(self.contractor, NoteOrganization):
            if self.contractor_sapiens is None:
                self.load_contractor_sapiens()
            representative = self.contractor_sapiens

        placeholders = self._build_party_b_placeholders(
            entity=self.contractor,
            representative=representative,
        )
        return self.make_overlay_file(
            name="party_b_contractor",
            source_file="documents/tex/professional/base/definitions/party_b.tex",
            placeholders=placeholders,
        )

    def make_overlay_party_b_client(self):
        """
        Create a ``party_b_client.tex`` overlay from the project's client data.

        Loads :attr:`client` if not yet set. The client note can be either an
        organization or an individual — the mapping follows the same rules as
        :meth:`make_overlay_party_b_contractor`. No separate client representative
        note is loaded; if the client is an organization and representative fields
        are needed, populate them manually via :meth:`make_overlay_file` with a
        custom placeholder dict built from :meth:`_build_party_b_placeholders`.

        :raises FileNotFoundError: If the client cannot be found in ``self.sources``.
        :returns: Path to the written overlay file.
        :rtype: pathlib.Path

        .. dropdown:: Example — organization client
            :icon: code-square
            :open:

            The project note has ``client: Big Boss Inc.``

            .. code-block:: python

                import losalamos

                pj = losalamos.load_project("path/to/myProject")
                pj.sources = {
                    "folders": {
                        "search": {
                            "organizations": ["path/to/org/notes"],
                            "sapiens": ["path/to/people/notes"],
                        }
                    }
                }

                path = pj.make_overlay_party_b_client()
                # → <project>/admin/config/overlays/party_b_client.tex
                # org fields from "Big Boss Inc..md"; representative fields are empty

        .. dropdown:: Example — invoice targeting the contractor as party B
            :icon: code-square
            :open:

            For an invoice, party B is typically the contractor, not the project
            client. Use :meth:`make_overlay_party_b_contractor` and pass the
            result to :meth:`add_document`.

            .. code-block:: python

                path = pj.make_overlay_party_b_contractor()

                pj.add_document(
                    document_type="invoice",
                    files_overlay={"definitions/party_b.tex": path},
                )
        """
        if self.client is None:
            self.load_client()

        placeholders = self._build_party_b_placeholders(
            entity=self.client,
            representative=None,
        )
        return self.make_overlay_file(
            name="party_b_client",
            source_file="documents/tex/professional/base/definitions/party_b.tex",
            placeholders=placeholders,
        )

    def get_attribute(self, entry_key, clean_cref=True):
        """
        Read a metadata field from the project's main note.

        :param entry_key: Metadata field name (e.g. ``"title"``, ``"client"``).
        :type entry_key: str
        :param clean_cref: If ``True`` (default), strip Obsidian wiki-link
            brackets from the returned value.
        :type clean_cref: bool
        :returns: Field value with surrounding YAML quote characters stripped.
            Returns a bracketed placeholder (e.g. ``[TITLE]``) when the field
            is absent or has a ``None`` value (empty YAML field).
        :rtype: str
        """
        s = self.main_note.metadata.get(entry_key, f"[{entry_key.upper()}]")
        if s is None:
            return f"[{entry_key.upper()}]"
        s = s.strip("\"'")  # YAML frontmatter sometimes preserves surrounding quotes
        if clean_cref:
            s = NoteProject.clean_cref(entry_key=s)
        return s

    def add_document(
        self,
        document_type,
        name=None,
        template_overlay=None,
        files_overlay=None,
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
        :param files_overlay: Forwarded to :meth:`Document.new`.
        :type files_overlay: dict or None
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
            template_overlay=template_overlay,
            files_overlay=files_overlay,
        )

        if condensed:
            instance.export(
                name=name,
                folder_root=documents_folder,
                flatten=True,
                split=True,
                zip_export=zip_export,
            )
            shutil.rmtree(target_folder)
            target_folder = documents_folder / name

        return_instance = klass(name=name)
        return_instance.load_data(file_data=target_folder / name / "main.tex")

        if compile_pdf:
            return_instance.to_pdf()

        self.documents[document_type] = return_instance

        return return_instance

    def _next_asset_id(self) -> str:
        """
        Scan the project tree for asset notes and return the next file ID.

        Globs all ``.md`` files under the project root, reads front-matter
        for those whose ``note_type`` is ``asset``, and collects the numeric
        part of each ``asset_id`` field (e.g. ``F003`` → ``3``). Returns the
        next available zero-padded identifier.

        :returns: Next asset ID, e.g. ``"F004"``.
        :rtype: str
        """
        numbers = []
        for md_file in Path(self.folder_root).rglob("*.md"):
            meta = NoteBasic.parse_metadata(note_file=md_file)
            if not meta or meta.get("note_type") != "asset":
                continue
            asset_id = meta.get("asset_id", "")
            if (
                isinstance(asset_id, str)
                and asset_id.startswith("F")
                and asset_id[1:].isdigit()
            ):
                numbers.append(int(asset_id[1:]))
        n = max(numbers) + 1 if numbers else 1
        return f"F{n:03d}"

    def get_assets(self) -> pd.DataFrame:
        """
        Return a DataFrame of all asset notes found under the project root.

        Scans every ``.md`` file for ``note_type: asset`` front-matter and
        collects ``asset_id``, ``asset_type``, ``name``, and ``asset_file``
        (with wiki-link and quote wrappers stripped). Rows are sorted by
        ``asset_id``.

        :returns: DataFrame with columns ``asset_id``, ``asset_type``, ``name``,
            ``asset_file``. Empty DataFrame when no assets exist.
        :rtype: pandas.DataFrame
        """
        rows = []
        for md_file in Path(self.folder_root).rglob("*.md"):
            meta = NoteBasic.parse_metadata(note_file=md_file)
            if not meta or meta.get("note_type") != "asset":
                continue
            raw_file = str(meta.get("asset_file") or "")
            # strip surrounding quotes and [[...]] wiki-link brackets
            clean_file = raw_file.strip("\"'").strip("[]")
            rows.append(
                {
                    "asset_id": meta.get("asset_id", ""),
                    "asset_type": meta.get("asset_type", ""),
                    "name": meta.get("name", md_file.stem),
                    "asset_file": clean_file,
                }
            )
        rows.sort(key=lambda r: r["asset_id"])
        return pd.DataFrame(
            rows, columns=["asset_id", "asset_type", "name", "asset_file"]
        )

    def _next_transfer_id(self):
        """
        Return the next available transfer ID as a zero-padded string.

        Globs all ``.md`` files under the project root, reads front-matter
        for those whose ``note_type`` is ``transfer``, and collects the
        numeric part of each ``name`` field that ends with a ``T``-prefixed
        ID (e.g. ``INFLOW_proj_T003`` → ``3``). Returns the next available
        zero-padded identifier.

        :returns: Next transfer ID, e.g. ``"T004"``.
        :rtype: str
        """
        pattern = re.compile(r"T(\d+)$", re.IGNORECASE)
        numbers = []
        for md_file in Path(self.folder_root).rglob("*.md"):
            meta = NoteBasic.parse_metadata(note_file=md_file)
            if not meta or meta.get("note_type") != "transfer":
                continue
            name = str(meta.get("name", ""))
            m = pattern.search(name)
            if m:
                numbers.append(int(m.group(1)))
        n = max(numbers) + 1 if numbers else 1
        return f"T{n:03d}"

    def add_transfer(
        self,
        transfer_type,
        date,
        account,
        value,
        status=None,
        commitment=None,
        recurrence=None,
        method=None,
        protocol=None,
        related_asset=None,
    ):
        """
        Create a new transfer note under ``budget/inflows/`` or ``budget/outflows/``.

        The target folder is chosen from *transfer_type*: ``"inflow"`` writes
        to ``budget/inflows/`` and ``"outflow"`` to ``budget/outflows/``.

        :param transfer_type: Direction of the transfer. Must be ``"inflow"``
            or ``"outflow"``.
        :type transfer_type: str
        :param date: Date of the transfer, e.g. ``"2026-09-02"``.
        :type date: str
        :param account: Account name or identifier.
        :type account: str
        :param value: Monetary value of the transfer.
        :type value: float or str
        :param status: Execution status. One of ``"Executed"``,
            ``"Cancelled"``, or ``"Prospected"``.
        :type status: str or None
        :param commitment: Financial commitment type. One of
            ``"Contracted"`` or ``"Optional"``.
        :type commitment: str or None
        :param recurrence: Recurrence period. One of ``"Monthly"`` or
            ``"Yearly"``.
        :type recurrence: str or None
        :param method: Payment method. Defaults to ``"Manual"`` when
            ``None``.
        :type method: str or None
        :param protocol: Payment protocol. One of ``"Bill"`` or
            ``"Transfer"``.
        :type protocol: str or None
        :param related_asset: Optional reference to a related asset note.
        :type related_asset: str or None
        :raises ValueError: If *transfer_type* is not ``"inflow"`` or
            ``"outflow"``.
        :returns: The newly created transfer note.
        :rtype: losalamos.notes.NoteTransfer
        """
        transfer_type = transfer_type.lower()
        if transfer_type not in ("inflow", "outflow"):
            raise ValueError(
                f"transfer_type must be 'inflow' or 'outflow', got '{transfer_type}'"
            )

        transfer_id = self._next_transfer_id()
        name = f"{transfer_type.upper()}_{self.name}_{transfer_id}"
        target_folder = Path(self.folder_root) / f"budget/{transfer_type}s"
        target_folder.mkdir(parents=True, exist_ok=True)

        note_file = target_folder / f"{name}.md"
        note = NoteTransfer(name=name, alias=name)
        note.load_new(file_note=note_file)
        note.metadata["name"] = name
        note.metadata["date"] = date
        note.metadata["transfer_type"] = transfer_type
        note.metadata["account"] = account
        note.metadata["value"] = value
        note.metadata["status"] = status
        note.metadata["commitment"] = commitment
        note.metadata["recurrence"] = recurrence
        note.metadata["method"] = method if method is not None else "Manual"
        note.metadata["protocol"] = protocol
        note.metadata["related_asset"] = related_asset
        note.update()
        note.save()

        return note

    def get_transfers(self) -> pd.DataFrame:
        """
        Return a DataFrame of all transfer notes found under the project root.

        Scans every ``.md`` file for ``note_type: transfer`` front-matter and
        collects the transfer schema fields. Rows are sorted by ``name``.

        :returns: DataFrame with columns ``name``, ``date``, ``transfer_type``,
            ``status``, ``account``, ``value``, ``commitment``, ``recurrence``,
            ``method``, ``protocol``, ``related_asset``. Empty DataFrame when
            no transfers exist.
        :rtype: pandas.DataFrame
        """
        _cols = [
            "name",
            "date",
            "transfer_type",
            "status",
            "account",
            "value",
            "commitment",
            "recurrence",
            "method",
            "protocol",
            "related_asset",
        ]
        rows = []
        for md_file in Path(self.folder_root).rglob("*.md"):
            meta = NoteBasic.parse_metadata(note_file=md_file)
            if not meta or meta.get("note_type") != "transfer":
                continue
            rows.append({col: meta.get(col, "") for col in _cols})
        rows.sort(key=lambda r: r["name"])
        return pd.DataFrame(rows, columns=_cols)

    def _localize_doc_type(self, asset_type) -> str:
        """
        Return the human-readable document type label for the project's language.

        Reads ``language`` from the main note metadata and looks up *asset_type*
        in :data:`_DOC_TYPE_LABELS`. Falls back to ``"en"`` when the language is
        unset or not listed in the table, and to ``asset_type.title()`` when the
        specific type has no translation.

        :param asset_type: Asset type string in uppercase, e.g. ``"INVOICE"``.
        :type asset_type: str
        :returns: Localized label, e.g. ``"Cobrança"`` for ``"INVOICE"`` in ``pt-br``.
        :rtype: str
        """
        lang = "en"
        if self.main_note is not None:
            val = self.main_note.metadata.get("language")
            if val:
                lang = str(val).lower().strip()
        labels = _DOC_TYPE_LABELS.get(lang, _DOC_TYPE_LABELS.get("en", {}))
        return labels.get(asset_type.lower(), asset_type.title())

    def _patch_project_tex(self, doc_folder, file_id, asset_type) -> None:
        """
        Write default field values into ``definitions/project.tex``.

        Sets ``\\DocVersion`` to ``001``, ``\\DocFileID`` to *file_id*, and
        ``\\DocType`` to the localized document type label returned by
        :meth:`_localize_doc_type`. Does nothing when the file is absent.

        :param doc_folder: Root of the document folder containing ``definitions/``.
        :type doc_folder: pathlib.Path
        :param file_id: Asset file ID, e.g. ``"F003"``.
        :type file_id: str
        :param asset_type: Asset type string in uppercase, e.g. ``"INVOICE"``.
        :type asset_type: str
        """
        project_tex = Path(doc_folder) / "definitions" / "project.tex"
        if not project_tex.is_file():
            return

        content = project_tex.read_text(encoding="utf-8")
        doc_type_label = self._localize_doc_type(asset_type=asset_type)

        def _set_cmd(cmd_name, value, text):
            return re.sub(
                r"(\\newcommand\{\\" + re.escape(cmd_name) + r"\}\{)[^}]*(\})",
                lambda m: m.group(1) + value + m.group(2),
                text,
            )

        content = _set_cmd("DocVersion", "001", content)
        content = _set_cmd("DocFileID", file_id, content)
        content = _set_cmd("DocType", doc_type_label, content)

        project_tex.write_text(content, encoding="utf-8")

    def _standard_files_overlay(self) -> dict:
        """Return the default files_overlay dict from ``admin/config/overlays/``."""
        overlays_dir = Path(self.folder_root) / "admin/config/overlays"
        _map = {
            "definitions/project.tex": overlays_dir / "project.tex",
            "definitions/party_b.tex": overlays_dir / "party_b_contractor.tex",
        }
        return {dst: str(src) for dst, src in _map.items() if src.is_file()}

    def _locate_document_source(self, name) -> Path:
        """
        Locate the working source folder for a document by name.

        Checks ``inputs/documents/{name}/`` under the local project root first,
        then under ``folder_remote_documents`` if a remote documents root is
        configured.

        :param name: Document folder name, e.g. ``"INVOICE_C034_F003"``.
        :type name: str
        :raises FileNotFoundError: If the source folder is not found in either
            the local or (when configured) the remote location.
        :returns: Path to the document source folder.
        :rtype: pathlib.Path
        """
        local = Path(self.folder_root) / "inputs/documents" / name
        if local.is_dir():
            return local
        if (
            self.folder_remote_documents is not None
            and self.folder_remote_documents != self.folder_root
        ):
            remote = self.folder_remote_documents / "inputs/documents" / name
            if remote.is_dir():
                return remote
            raise FileNotFoundError(
                f"Document source not found for '{name}'. "
                f"Checked: '{local}', '{remote}'"
            )
        raise FileNotFoundError(
            f"Document source not found for '{name}'. Checked: '{local}'"
        )

    def _add_asset_document(self, asset_type, files_overlay, config=None):
        """
        Core creation logic for asset documents (invoice, receipt, proposal, etc.).

        Creates the document working tree at ``inputs/documents/{name}/``, registers
        the document via :meth:`add_document`, patches ``definitions/project.tex``
        with the asset identity fields, writes the sidecar asset note at
        ``inputs/documents/{name}.md`` (always local, visible to Obsidian), and
        optionally rewrites the services table via :meth:`~losalamos.documents.Document.apply_config`.

        :param asset_type: Asset type string in uppercase, e.g. ``"INVOICE"``.
        :type asset_type: str
        :param files_overlay: File overlay dict passed to :meth:`add_document`.
        :type files_overlay: dict or None
        :param config: Optional config dict forwarded to :meth:`~losalamos.documents.Document.apply_config`.
            When provided, rewrites the document's services table.
        :type config: dict or None
        :returns: The newly created document instance.
        :rtype: losalamos.documents.Document
        """
        asset_id = self._next_asset_id()
        name = f"{asset_type}_{self.name}_{asset_id}"

        template_overlay = (
            self.sources.get("templates", {})
            .get("documents", {})
            .get(asset_type.lower(), None)
        )

        doc = self.add_document(
            document_type=asset_type.lower(),
            name=name,
            template_overlay=template_overlay,
            files_overlay=files_overlay or None,
            subfolder="inputs/documents",
            condensed=False,
            compile_pdf=False,
        )

        source_folder = Path(self.folder_root) / "inputs/documents" / name
        self._patch_project_tex(
            doc_folder=source_folder,
            file_id=asset_id,
            asset_type=asset_type,
        )

        if config is not None:
            doc.apply_config(config=config)

        note_file = Path(self.folder_root) / "inputs/documents" / f"{name}.md"
        asset_note = NoteAsset(name=name, alias=name)
        asset_note.load_new(file_note=note_file)
        asset_note.metadata["name"] = name
        asset_note.metadata["project"] = self.name
        asset_note.metadata["asset_type"] = asset_type
        asset_note.metadata["asset_id"] = asset_id
        asset_note.metadata["asset_file"] = f'"[[{name}.pdf]]"'
        asset_note.update()
        asset_note.save()

        return doc

    def _build_asset_document(self, asset_type, file_id, subfolder):
        """
        Core build logic for asset documents (invoice, receipt, proposal, etc.).

        Locates the source via :meth:`_locate_document_source`, reads
        ``\\DocVersion`` from ``definitions/project.tex`` (dots removed, ``V``
        prefix added), compiles via ``latexmk`` with cleanup, ships the PDF to
        ``{subfolder}/{asset_type}_{project}_{file_id}_{version}.pdf``, and
        updates ``asset_file`` in the sidecar note at ``inputs/documents/{name}.md``.

        :param asset_type: Asset type string in uppercase, e.g. ``"INVOICE"``.
        :type asset_type: str
        :param file_id: Asset file ID assigned at creation, e.g. ``"F003"``.
        :type file_id: str
        :param subfolder: Project-relative target folder for the PDF, e.g. ``"budget/documents"``.
        :type subfolder: str
        :raises FileNotFoundError: If the document source folder or ``main.tex`` is not found.
        :returns: Path to the compiled PDF.
        :rtype: pathlib.Path
        """
        name = f"{asset_type}_{self.name}_{file_id}"
        doc_folder = self._locate_document_source(name=name)

        main_tex = doc_folder / "main.tex"
        if not main_tex.is_file():
            raise FileNotFoundError(f"main.tex not found in '{doc_folder}'")

        # Read \DocVersion from definitions/project.tex
        project_tex = doc_folder / "definitions" / "project.tex"
        version_raw = "[Version]"
        if project_tex.is_file():
            m = re.search(
                r"\\newcommand\{\\DocVersion\}\{([^}]+)\}",
                project_tex.read_text(encoding="utf-8"),
            )
            if m:
                version_raw = m.group(1)
        version_tag = "V" + version_raw.replace(".", "")

        target_dir = Path(self.folder_root) / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        pdf_name = f"{asset_type}_{self.name}_{file_id}_{version_tag}.pdf"
        pdf_output = target_dir / pdf_name

        klass = DOCUMENT_TYPES[asset_type.lower()]
        doc = klass(name=name)
        doc.load_data(file_data=main_tex)
        doc.to_pdf(file_output=pdf_output, cleanup=True)

        note_file = Path(self.folder_root) / "inputs/documents" / f"{name}.md"
        if note_file.is_file():
            asset_note = NoteAsset(name=name, alias=name)
            asset_note.load(file_note=note_file)
            asset_note.metadata["asset_file"] = f'"[[{pdf_name}]]"'
            asset_note.update()
            asset_note.save()

        return pdf_output

    def add_invoice(self, config=None):
        """
        Create a new invoice document.

        The working tree is created at ``inputs/documents/INVOICE_{project}_{file_id}/``
        and the sidecar note at ``inputs/documents/INVOICE_{project}_{file_id}.md``.
        No compilation or condensing is performed.

        The template directory is read from
        ``sources["templates"]["documents"]["invoice"]`` in the project's
        ``admin/config/sources.toml``. The following overlays are applied
        when present in ``admin/config/overlays/``:

        - ``project.tex`` → ``definitions/project.tex``
        - ``party_b_contractor.tex`` → ``definitions/party_b.tex``

        :param config: Optional config dict forwarded to
            :meth:`~losalamos.documents.Invoice.apply_config`. When provided,
            rewrites ``partials/services-invoice.tex`` from the services list
            and invoice settings in the dict.
        :type config: dict or None
        :returns: The newly created invoice document instance.
        :rtype: losalamos.documents.Document
        """
        return self._add_asset_document(
            asset_type="INVOICE",
            files_overlay=self._standard_files_overlay(),
            config=config,
        )

    def add_receipt(self, invoice_id=None, config=None):
        """
        Create a new receipt document inside ``budget/documents/``.

        When *invoice_id* is provided, all files from the linked invoice
        folder (except ``main.tex``) become file overlays, so the receipt
        inherits the invoice's project definitions, party files, and any
        other configured assets. Without *invoice_id*, the standard
        ``admin/config/overlays/`` files are applied instead.

        The asset ID counter is shared with invoices, so IDs never collide
        across document types within the same project.

        :param invoice_id: Asset file ID of a previously created invoice,
            e.g. ``"F003"``. When provided, the invoice folder's files
            (excluding ``main.tex``) become file overlays on the receipt.
        :type invoice_id: str or None
        :param config: Optional config dict forwarded to
            :meth:`~losalamos.documents.Receipt.apply_config`. When provided,
            rewrites ``partials/services-receipt.tex`` from the services list
            and invoice settings in the dict.
        :type config: dict or None
        :raises FileNotFoundError: If *invoice_id* is given but the
            corresponding invoice folder does not exist.
        :returns: The newly created receipt document instance.
        :rtype: losalamos.documents.Document
        """
        if invoice_id is not None:
            invoice_name = f"INVOICE_{self.name}_{invoice_id}"
            invoice_folder = self._locate_document_source(name=invoice_name)
            files_overlay = {
                src.relative_to(invoice_folder).as_posix(): str(src)
                for src in invoice_folder.rglob("*")
                if src.is_file() and src.name != "main.tex"
            }
        else:
            files_overlay = self._standard_files_overlay()

        return self._add_asset_document(
            asset_type="RECEIPT",
            files_overlay=files_overlay,
            config=config,
        )

    def build_invoice(self, file_id):
        """
        Compile a previously created invoice to PDF.

        Reads ``\\DocVersion`` from ``definitions/project.tex``, compiles
        via ``latexmk`` with cleanup, and places the result at
        ``inputs/documents/INVOICE_{project}_{file_id}_{version}.pdf``.
        Updates the ``asset_file`` field in the sidecar note.

        :param file_id: Asset file ID assigned at creation, e.g. ``"F003"``.
        :type file_id: str
        :raises FileNotFoundError: If the invoice folder or ``main.tex`` is not found.
        :returns: Path to the compiled PDF.
        :rtype: pathlib.Path
        """
        return self._build_asset_document(
            asset_type="INVOICE", file_id=file_id, subfolder="inputs/documents"
        )

    def build_receipt(self, file_id):
        """
        Compile a previously created receipt to PDF.

        Reads ``\\DocVersion`` from ``definitions/project.tex``, compiles
        via ``latexmk`` with cleanup, and places the result at
        ``inputs/documents/RECEIPT_{project}_{file_id}_{version}.pdf``.
        Updates the ``asset_file`` field in the sidecar note.

        :param file_id: Asset file ID assigned at creation, e.g. ``"F003"``.
        :type file_id: str
        :raises FileNotFoundError: If the receipt folder or ``main.tex`` is not found.
        :returns: Path to the compiled PDF.
        :rtype: pathlib.Path
        """
        return self._build_asset_document(
            asset_type="RECEIPT", file_id=file_id, subfolder="inputs/documents"
        )

    def add_proposal(self):
        """
        Create a new proposal document.

        The working tree is created at ``inputs/documents/PROPOSAL_{project}_{file_id}/``
        and the sidecar note at ``inputs/documents/PROPOSAL_{project}_{file_id}.md``.
        No compilation or condensing is performed.

        The template directory is read from
        ``sources["templates"]["documents"]["proposal"]`` in the project's
        ``admin/config/sources.toml``. The following overlays are applied
        when present in ``admin/config/overlays/``:

        - ``project.tex`` → ``definitions/project.tex``
        - ``party_b_contractor.tex`` → ``definitions/party_b.tex``

        :returns: The newly created proposal document instance.
        :rtype: losalamos.documents.Document
        """
        return self._add_asset_document(
            asset_type="PROPOSAL",
            files_overlay=self._standard_files_overlay(),
        )

    def build_proposal(self, file_id):
        """
        Compile a previously created proposal to PDF.

        Reads ``\\DocVersion`` from ``definitions/project.tex``, compiles
        via ``latexmk`` with cleanup, and places the result at
        ``admin/proposals/PROPOSAL_{project}_{file_id}_{version}.pdf``.
        Updates the ``asset_file`` field in the sidecar note.

        :param file_id: Asset file ID assigned at creation, e.g. ``"F005"``.
        :type file_id: str
        :raises FileNotFoundError: If the proposal folder or ``main.tex`` is not found.
        :returns: Path to the compiled PDF.
        :rtype: pathlib.Path
        """
        return self._build_asset_document(
            asset_type="PROPOSAL", file_id=file_id, subfolder="admin/proposals"
        )

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
