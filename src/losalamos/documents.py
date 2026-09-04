# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Handle Documents editing, managing and builds.

Class hierarchy
---------------

.. code-block:: text

    DataSet
    └── Document                    (base for all document types)
        └── DocumentTeX             (base for all TeX documents)
            └── Essay               (base for essay-style documents)
                ├── Academic        (academic documents)
                │   ├── Article
                │   ├── Preprint
                │   └── PrintArticle
                └── Professional    (professional documents)
                    ├── Report      (standard report; PDF/note → outputs/)
                    ├── Invoice
                    │   ├── Receipt
                    │   └── Proposal
                    │       ├── Agreement
                    │       └── Contract

Template resolution
-------------------
Every ``new()`` call merges up to three template layers in priority order:

.. code-block:: text

    BASE_TEMPLATE  ←  VARIANT_TEMPLATE  ←  template_overlay (user)

- ``BASE_TEMPLATE``    : defined on ``DocumentTeX``; canonical TeX base shared
                         by all document types.
- ``VARIANT_TEMPLATE`` : defined per subclass; files that differentiate the
                         document type (cover, class options, etc.).
- ``template_overlay`` : optional user-supplied folder for private or
                         client-specific files (logos, confidential covers).

Each layer wins over the one to its left. Files absent from a layer are
inherited transparently from the layer below.

"""

# ***********************************************************************
# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import os
import re
import json
import shutil
from pathlib import Path

# External imports
# =======================================================================
# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import DataSet, MbaE
from losalamos.paths import FOLDER_TEMPLATES_DOCUMENTS

# ... {develop}


# ***********************************************************************
# CONSTANTS
# ***********************************************************************

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# ***********************************************************************
# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def escape_percent_latex(text: str) -> str:
    # Replace % not preceded by an odd number of backslashes
    return re.sub(r"(?<!\\)%", r"\%", text)


# FUNCTIONS -- Module-level
# =======================================================================


def _load_files_overlay(source):
    """
    Parse a ``files_overlay`` config file into a dict.

    :param source: Path to a ``.json``, ``.yaml``/``.yml``, or ``.toml`` file
        whose contents map destination-relative paths to source file paths.
    :type source: str or pathlib.Path
    :raises FileNotFoundError: If ``source`` does not exist on the filesystem.
    :raises ValueError: If the file extension is not a supported format.
    :raises ImportError: If the required third-party parser (PyYAML, tomli)
        is not installed.
    :returns: Mapping of destination-relative paths to source file paths.
    :rtype: dict
    """
    return MbaE.load_config_file(path=source)


# ***********************************************************************
# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================


class Document(DataSet):
    """
    Base class for all document types.

    Handles generic file loading and the three-layer template merge
    used by :meth:`new`. Subclasses specialise behaviour by overriding
    :attr:`BASE_TEMPLATE` and :attr:`VARIANT_TEMPLATE`.
    """

    BASE_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "txt/demo"
    VARIANT_TEMPLATE = None

    def __init__(self, name="MyDocument", alias="Doc"):
        super().__init__(name=name, alias=alias)

    def __str__(self):
        """
        String representation of a text-based :class:`Document`.

        :class:`DataSet` (the parent class) assumes ``self.data`` is a
        :class:`pandas.DataFrame` and previews it with ``.head()``/``.tail()``.
        :class:`Document` overrides ``self.data`` to hold a plain list of
        text lines (from :meth:`load_data`), so this override previews the
        first and last lines instead, and skips straight to :class:`MbaE`'s
        header (bypassing :meth:`DataSet.__str__`, which would otherwise
        raise ``AttributeError`` on a list).

        :returns: Formatted string with the object header plus a line-based
            preview of :attr:`data`.
        :rtype: str
        """
        str_super = super(DataSet, self).__str__()

        if self.data is None:
            return "{}\nData:\nNone\n".format(str_super)

        n_lines = len(self.data)
        n_preview = 5

        if n_lines <= 2 * n_preview:
            str_body = "".join(self.data).rstrip("\n")
            str_out = "{}\nData ({} lines):\n{}\n".format(str_super, n_lines, str_body)
        else:
            str_head = "".join(self.data[:n_preview]).rstrip("\n")
            str_tail = "".join(self.data[-n_preview:]).rstrip("\n")
            str_out = "{}\nData ({} lines):\n{}\n ... \n{}\n".format(
                str_super, n_lines, str_head, str_tail
            )

        return str_out

    def load_data(self, file_data):
        # overwrite relative path input
        # --------------------------------------------------
        self.file_data = Path(file_data).absolute()

        # Open and extract lines (assuming utf-8 encoding for standard TeX)
        with open(self.file_data, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # load all the text by a readlines method. self.data is a list.
        self.data = lines

        # update
        # --------------------------------------------------
        self.update()

    def new(self, folder, name=None, template_overlay=None, files_overlay=None):
        """
        Create a new document folder by materializing template files into a target location.

        This method creates a folder named ``name`` inside ``folder`` and populates it
        by merging up to three template layers in the following priority order:

        .. code-block:: text

            BASE_TEMPLATE  ←  VARIANT_TEMPLATE  ←  template_overlay

        Each layer wins over the one to its left. Layers that are ``None`` are
        skipped transparently. The caller is responsible for ensuring the target
        path does not already exist; if it does, a :exc:`FileExistsError` is
        raised immediately and no files are written.

        **Single-layer mode** (only ``BASE_TEMPLATE``, both ``VARIANT_TEMPLATE``
        and ``template_overlay`` are ``None``):

        The entire :attr:`BASE_TEMPLATE` directory tree is copied as-is into the
        target folder, preserving all subdirectories and files.

        **Multi-layer mode** (one or both of ``VARIANT_TEMPLATE``,
        ``template_overlay`` are provided):

        All active layers are scanned recursively and merged into the target.

        - Files present in only one layer are copied from that layer.
        - Files present in multiple layers are resolved in favour of the
          highest-priority layer (right-most in the chain).

        .. dropdown:: Merge example — three active layers
            :icon: file-directory
            :open:

            .. code-block:: text

                BASE_TEMPLATE/      VARIANT_TEMPLATE/     template_overlay/
                ├── main.tex        ├── main.tex           └── cover.tex
                ├── preamble.tex    └── cover.tex
                └── refs.bib

                # Resolution:
                # main.tex     → VARIANT_TEMPLATE  (highest priority)
                # cover.tex    → template_overlay  (highest priority)
                # preamble.tex → BASE_TEMPLATE     (only source)
                # refs.bib     → BASE_TEMPLATE     (only source)

                # Result in target:
                folder/name/
                ├── main.tex        # from VARIANT_TEMPLATE
                ├── cover.tex       # from template_overlay
                ├── preamble.tex    # from BASE_TEMPLATE
                └── refs.bib        # from BASE_TEMPLATE

        :param name: Name of the new document folder to be created inside ``folder``.
        :type name: str
        :param folder: Parent directory under which the new document folder is created.
            Must already exist as a directory on the filesystem.
        :type folder: str or pathlib.Path
        :param template_overlay: Optional user-supplied directory whose files take
            priority over both :attr:`BASE_TEMPLATE` and :attr:`VARIANT_TEMPLATE`.
            Intended for private or client-specific files (logos, confidential covers,
            etc.). When ``None`` (default), only the class-level templates are used.
            When provided, must be a valid existing directory; otherwise
            :exc:`NotADirectoryError` is raised before any files are written.
        :type template_overlay: str, pathlib.Path, or None
        :param files_overlay: Optional file-level overlay applied after all template
            layers. Can be a ``dict`` mapping destination-relative paths to source file
            paths, or a path to a ``.json``, ``.yaml``/``.yml``, or ``.toml`` config
            file with the same structure. Keys are paths relative to the document root
            (e.g. ``"definitions/party_b.tex"``); values are the source files to copy
            from (the destination filename is taken from the key, not the source).
            All source files are validated before any copying begins.
        :type files_overlay: dict, str, pathlib.Path, or None

        :raises FileExistsError: If the target folder ``folder/name`` already exists.
            No files are created or modified in this case.
        :raises NotADirectoryError: If ``template_overlay`` is provided but does not
            point to a valid directory. Validated before any files are written.
        :raises FileNotFoundError: If a source path in ``files_overlay`` does not exist
            or is not a file. Also raised if the merged template does not contain exactly
            one top-level ``main.*`` file to load as the document's entry point.

        :returns: None. Acts in place: locates the merged tree's top-level
            ``main.*`` file and calls :meth:`load_data` on it, which updates
            :attr:`file_data`, :attr:`data`, and (for subclasses such as
            :class:`DocumentTeX`) :attr:`is_main` to reflect the newly created
            document.
        :rtype: None

        .. dropdown:: Usage example
            :icon: code-square
            :open:

            .. code-block:: python

                # Single-layer: base template only (Document base class)
                doc = Document(name="MyDoc", alias="D")
                doc.new("my_doc", "/home/user/documents")
                # doc.file_data now points at the new document's main file

                # Two-layer: base + variant (subclass sets VARIANT_TEMPLATE)
                report = Report(name="AnnualReport", alias="AR")
                report.new("annual_report", "/home/user/documents")

                # Three-layer: base + variant + private user overlay
                report.new(
                    "client_report",
                    "/home/user/documents",
                    template_overlay="/home/user/private/client_x",
                )
        """

        if name is None:
            name = self.name

        # Resolve files_overlay from config file if a path is given
        # --------------------------------------------------
        if isinstance(files_overlay, (str, Path)):
            files_overlay = _load_files_overlay(files_overlay)

        # Resolve paths
        # --------------------------------------------------
        folder = Path(folder).absolute()
        target = folder / name

        # Guard: target must not already exist
        # --------------------------------------------------
        if target.exists():
            raise FileExistsError(
                f"Target folder already exists: '{target}'. "
                "Please provide a new document name or a different folder."
            )

        # Validate template_overlay early, before doing any work
        # --------------------------------------------------
        if template_overlay is not None:
            template_overlay = Path(template_overlay).absolute()
            if not template_overlay.is_dir():
                raise NotADirectoryError(
                    f"'template_overlay' is not a valid directory: '{template_overlay}'"
                )

        # Validate files_overlay sources before doing any work
        # --------------------------------------------------
        if files_overlay is not None:
            for dst_rel, src_path in files_overlay.items():
                src = Path(src_path).absolute()
                if not src.is_file():
                    raise FileNotFoundError(
                        f"'files_overlay' source does not exist or is not a file: '{src}'"
                    )

        # Collect relative files from a template root
        # --------------------------------------------------
        def relative_files(root: Path) -> dict:
            """Returns {relative_path: absolute_path} for every file under root."""
            return {f.relative_to(root): f for f in root.rglob("*") if f.is_file()}

        # Walk the class's MRO base-to-derived, collecting every distinct
        # VARIANT_TEMPLATE set directly on each ancestor (via __dict__, not
        # inherited attribute resolution). Plain attribute lookup on
        # self.VARIANT_TEMPLATE would only ever see the single value set by
        # the most-derived class -- e.g. ProposalCommercial(Professional)
        # would silently shadow Professional's own VARIANT_TEMPLATE instead
        # of layering on top of it, breaking the base -> variant -> variant
        # inheritance chain this method is meant to support.
        # --------------------------------------------------
        variant_templates = []
        seen = set()
        for klass in reversed(type(self).__mro__):
            variant = klass.__dict__.get("VARIANT_TEMPLATE")
            if variant is not None and variant not in seen:
                variant_templates.append(variant)
                seen.add(variant)

        # Build each active layer; higher layers overwrite lower ones
        # --------------------------------------------------
        merged = {}

        merged.update(relative_files(self.BASE_TEMPLATE))

        for variant_template in variant_templates:
            merged.update(relative_files(variant_template))

        if template_overlay is not None:
            merged.update(relative_files(template_overlay))

        # Copy every resolved file to the target, preserving structure
        # --------------------------------------------------
        for rel_path, src in merged.items():
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

        # Apply file-level overlays last; can overwrite any template file
        # --------------------------------------------------
        if files_overlay is not None:
            for dst_rel, src_path in files_overlay.items():
                dest = target / dst_rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(Path(src_path).absolute(), dest)

        # Locate the merged tree's entry file and load it in place
        # --------------------------------------------------
        main_candidates = [
            rel_path
            for rel_path in merged
            if len(rel_path.parts) == 1 and rel_path.stem == "main"
        ]

        if len(main_candidates) != 1:
            raise FileNotFoundError(
                "Expected exactly one top-level 'main.*' file in the merged "
                f"template, found {len(main_candidates)}: {main_candidates}. "
                "Cannot determine which file to load."
            )

        self.load_data(target / main_candidates[0])

        return None

    def apply_config(self, config):
        """
        Apply document configuration. No-op in the base class.

        Subclasses such as :class:`Invoice` and :class:`Receipt` override
        this to rewrite their services table partial from ``config``.

        :param config: Configuration dict. Subclasses interpret the contents.
        :type config: dict or None
        :returns: None
        :rtype: None
        """
        return None


# CLASSES -- Module-level
# =======================================================================


class LatexCompileError(RuntimeError):
    """
    Raised when ``latexmk`` fails or cannot be found on ``PATH``.

    :param message: Human-readable error description.
    :type message: str
    :param source: Path to the ``.tex`` file being compiled, or ``None``.
    :type source: pathlib.Path or None
    :param returncode: Exit code returned by ``latexmk``. ``-1`` when
        ``latexmk`` was not found.
    :type returncode: int
    :param log_path: Path to the ``.log`` file produced by the failed run,
        or ``None`` if unavailable.
    :type log_path: pathlib.Path or None
    """

    def __init__(self, message, source=None, returncode=-1, log_path=None):
        super().__init__(message)
        self.source = source
        self.returncode = returncode
        self.log_path = log_path


class DocumentTeX(Document):
    """
    Base class for all TeX-based document types.

    Extends :class:`Document` with TeX-specific behaviour: main-file
    detection, PDF compilation via ``latexmk``, and document flattening.
    Subclasses set :attr:`VARIANT_TEMPLATE` to select their template layer.
    """

    BASE_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/base"
    VARIANT_TEMPLATE = None

    def __init__(self, name="MyDocTeX", alias="TeX"):
        super().__init__(name=name, alias=alias)
        self.is_main = True

    def load_data(self, file_data):
        """
        Load data from a TeX file and detect whether it is a main document.

        A file is considered a main document if it contains a
        ``\\documentclass`` declaration. Partial files (chapters, sections)
        intended to be ``\\input``-ted by a main file will have
        :attr:`is_main` set to ``False``.

        :param file_data: Path to the ``.tex`` file to load.
        :type file_data: str or pathlib.Path
        :returns: None
        :rtype: None
        """
        super().load_data(file_data)

        # Check if it is a main tex file (not a part)
        # Using '\documentclass' as the standard marker for a main LaTeX file
        # --------------------------------------------------
        self.is_main = any(r"\documentclass" in line for line in self.data)

        # update
        # --------------------------------------------------
        self.update()

        return None

    def to_pdf(self, file_output=None, cleanup=True, command="pdf"):
        """
        Compile the TeX document into a PDF using ``latexmk``.

        Only executes when :attr:`is_main` is ``True``; partial files are
        silently skipped.

        The method temporarily switches the working directory to the source
        file's parent folder before invoking ``latexmk``, ensuring that all
        relative paths in the document (``\\input``, ``\\include``, figures,
        etc.) resolve correctly regardless of where the Python process was
        launched from. The original working directory is always restored,
        even if compilation raises an exception.

        A project-local ``latexmkrc`` file is expected at the root of the
        document folder. It is passed explicitly via ``-r latexmkrc`` so
        that glossaries and nomenclature are built correctly on all platforms
        without requiring a global ``latexmkrc`` installation.

        :param file_output: Desired output path for the compiled PDF. When
            ``None`` (default), the PDF is left next to the source ``.tex``
            file.
        :type file_output: str or pathlib.Path or None
        :param cleanup: If ``True`` (default), removes auxiliary files
            produced by ``latexmk`` after a successful compilation
            (equivalent to ``latexmk -c``).
        :type cleanup: bool
        :param command: ``latexmk`` engine flag controlling the PDF backend.
            Common values: ``"pdf"`` (pdflatex), ``"pdflua"`` (lualatex),
            ``"pdfxe"`` (xelatex).
        :type command: str
        :raises LatexCompileError: If ``latexmk`` exits with a non-zero
            return code or is not found on ``PATH``. The exception carries
            ``source``, ``returncode``, and ``log_path`` attributes.
        :returns: None
        :rtype: None
        """
        if not self.is_main:
            return None

        import subprocess

        source = self.file_data.absolute()
        source_dir = source.parent
        latexmkrc = source_dir / "latexmkrc"
        original_dir = Path(os.getcwd())

        os.chdir(source_dir)

        try:
            # Compile
            # --------------------------------------------------
            compile_cmd = ["latexmk", f"-{command}"]

            # Use project-local latexmkrc if present
            if latexmkrc.exists():
                compile_cmd += ["-r", "latexmkrc"]

            compile_cmd += [source.name]

            try:
                subprocess.run(compile_cmd, check=True)
            except subprocess.CalledProcessError as exc:
                log = source.with_suffix(".log")
                raise LatexCompileError(
                    f"latexmk failed (exit {exc.returncode}): '{source}'",
                    source=source,
                    returncode=exc.returncode,
                    log_path=log if log.exists() else None,
                ) from exc
            except FileNotFoundError:
                raise LatexCompileError(
                    "latexmk not found — is a LaTeX distribution installed?",
                    source=source,
                    returncode=-1,
                    log_path=None,
                ) from None

            # Handle output destination
            # --------------------------------------------------
            default_pdf = source.with_suffix(".pdf")

            if file_output is not None:
                target_path = Path(file_output).absolute()
                shutil.copy2(default_pdf, target_path)
                default_pdf.unlink()

            # Cleanup auxiliary files — intentionally only reachable after a
            # successful compile so that .log and aux files survive on failure.
            # --------------------------------------------------
            if cleanup:
                self.clean()

        finally:
            os.chdir(original_dir)

        return None

    def clean(self):
        """
        Remove auxiliary files left by a previous ``latexmk`` run.

        Runs ``latexmk -c`` and then sweeps for extra suffixes that
        ``latexmk -c`` does not track. The working directory is temporarily
        switched to the source file's parent folder (matching :meth:`to_pdf`)
        and is always restored in a ``finally`` block.

        Only executes when :attr:`is_main` is ``True``; partial files are
        silently skipped.

        :returns: None
        :rtype: None
        """
        if not self.is_main:
            return None

        import subprocess

        source = self.file_data.absolute()
        source_dir = source.parent
        latexmkrc = source_dir / "latexmkrc"
        original_dir = Path(os.getcwd())

        os.chdir(source_dir)

        try:
            cleanup_cmd = ["latexmk", "-c"]
            if latexmkrc.exists():
                cleanup_cmd += ["-r", "latexmkrc"]
            cleanup_cmd += [source.name]
            subprocess.run(cleanup_cmd, check=True)

            # Manual sweep for files latexmk -c never tracks
            _extra_suffixes = {
                ".bbl",
                ".bcf",
                ".run.xml",
                ".glo",
                ".gls",
                ".glg",
                ".acn",
                ".acr",
                ".alg",
                ".nlo",
                ".nls",
                ".nlg",
                ".ist",
                ".maf",
                ".mtc",
                ".mtc0",
                ".lol",
                ".lob",
            }
            stem = source.stem
            for suffix in _extra_suffixes:
                leftover = source_dir / (stem + suffix)
                if leftover.exists():
                    leftover.unlink()

        finally:
            os.chdir(original_dir)

        return None

    def to_flat(self, file_output=None, compile_first=False, command="pdf"):
        """
        Flatten the TeX document by recursively resolving ``\\input`` /
        ``\\include`` directives and embedding the compiled bibliography.

        Delegates the flattening work to :meth:`make_flat`. Only executes
        when :attr:`is_main` is ``True``; partial files return ``None``
        silently.

        :param file_output: Desired output path for the flattened ``.tex``
            file. When ``None``, the source file is overwritten in-place.
        :type file_output: str or pathlib.Path or None
        :param compile_first: If ``True`` (default), compiles the document
            before flattening so that the ``.bbl`` file reflects the current
            bibliography state. The intermediate PDF and ``.bbl`` are removed
            after flattening.
        :type compile_first: bool
        :param command: ``latexmk`` engine flag passed to :meth:`to_pdf` when
            ``compile_first=True``.
        :type command: str
        :returns: ``None``
        :rtype: str or None
        """
        if not self.is_main:
            return None

        if compile_first:
            self.to_pdf(file_output=None, command=command, cleanup=True)

        output_tex = (
            Path(file_output).absolute() if file_output is not None else self.file_data
        )

        DocumentTeX.make_flat(self.file_data, output_tex=output_tex)

        if compile_first:
            for suffix in (".bbl", ".pdf"):
                p = self.file_data.with_suffix(suffix)
                if p.exists():
                    p.unlink()

        return None

    def export(self, folder_root, name, flatten=False, split=False, zip_export=False):
        """
        Export the TeX document to a self-contained folder.

        Creates ``folder_root/name/`` and writes the document into it
        according to the chosen mode:

        - **Plain** (``flatten=False``, ``split=False``): the source file is
          copied as-is, retaining its original filename.
        - **Flatten** (``flatten=True``, ``split=False``): ``\\input`` /
          ``\\include`` directives are resolved recursively and the result is
          written as a single file named ``<name>.tex``. Every image
          (``\\includegraphics``) and bibliography resource
          (``\\addbibresource``) referenced anywhere in the document tree
          is also copied alongside, preserving its path relative to the
          original project root so the (unmodified) references in the
          flattened text keep resolving correctly.
        - **Split** (``split=True``): implies flattening, with the same
          image/bibliography-resource copying described above. The
          document is first flattened into a temporary file, then split
          into ``preamble.tex`` and ``main.tex``. The intermediate flat
          file is removed after splitting.

        :param folder_root: Parent directory under which the export folder
            is created.
        :type folder_root: str or pathlib.Path
        :param name: Name of the export folder and, in flatten mode, stem
            of the output ``.tex`` file.
        :type name: str
        :param flatten: If ``True``, resolve all ``\\input`` / ``\\include``
            directives into a single file before exporting. Ignored when
            ``split=True`` (flattening is always performed in that case).
        :type flatten: bool
        :param split: If ``True``, flatten the document and split the result
            into ``preamble.tex`` and ``main.tex``. Takes precedence over
            ``flatten``.
        :type split: bool
        :param zip_export: If ``True``, additionally packages the export
            folder's contents into a ``.zip`` archive at
            ``folder_root/<name>.zip``. Files are placed at the archive's
            root -- not nested inside a ``<name>/`` folder -- so the zip
            can be dropped directly into Overleaf's "Upload Project" (or
            any other single-archive project import) without any manual
            restructuring first. The uncompressed export folder is left
            in place alongside it either way.
        :type zip_export: bool
        :returns: Path to the created export folder. When ``zip_export``
            is ``True``, the archive sits alongside it at
            ``folder_root/<name>.zip``.
        :rtype: pathlib.Path
        :raises RuntimeError: If the document is not a main file (i.e.
            ``\\documentclass`` is absent). The ``is_main`` attribute is
            re-evaluated from ``file_data`` before the check so stale state
            does not produce a false negative.
        :raises FileExistsError: If ``folder_root/name`` already exists.
        """
        # Re-evaluate is_main from file_data to avoid stale state
        # --------------------------------------------------
        self.is_main = any(r"\documentclass" in line for line in self.data)

        if not self.is_main:
            raise RuntimeError(
                f"Cannot export '{self.file_data.name}': file has no "
                f"\\documentclass declaration and is not a main TeX document."
            )

        # Resolve and guard the export folder
        # --------------------------------------------------
        folder_root = Path(folder_root).absolute()
        export_dir = folder_root / name

        if export_dir.exists():
            raise FileExistsError(
                f"Export folder already exists: '{export_dir}'. "
                f"Provide a different name or remove the existing folder."
            )

        export_dir.mkdir(parents=True)

        # Export modes
        # --------------------------------------------------
        if split:
            # Flatten to a temp file inside the export folder, then split
            # and remove the intermediate flat file
            flat_file = export_dir / f"_{name}_flat.tex"
            assets = set()
            DocumentTeX.make_flat(self.file_data, output_tex=flat_file, assets=assets)
            DocumentTeX.split_preamble(flat_file, output_folder=export_dir)
            flat_file.unlink()
            DocumentTeX._copy_assets(assets, self.file_data.parent, export_dir)

        elif flatten:
            # Single merged file named after the export folder
            output_tex = export_dir / f"{name}.tex"
            assets = set()
            DocumentTeX.make_flat(self.file_data, output_tex=output_tex, assets=assets)
            DocumentTeX._copy_assets(assets, self.file_data.parent, export_dir)

        else:
            # Plain copy, original filename retained
            shutil.copy2(self.file_data, export_dir / self.file_data.name)

        # Optional zip archive, contents at the archive root (no wrapping
        # folder) so it can be dropped straight into Overleaf's project
        # importer or similar. Only the zip is meant to survive here --
        # the uncompressed export folder is removed once the archive is
        # safely written, so callers never end up with both copies.
        # --------------------------------------------------
        if zip_export:
            zip_path = shutil.make_archive(
                base_name=str(folder_root / name),
                format="zip",
                root_dir=export_dir,
            )
            shutil.rmtree(export_dir)
            return Path(zip_path)

        return export_dir

    @staticmethod
    def split_preamble(
        input_tex, preamble_name="preamble", main_name="main", output_folder=None
    ):
        """
        Split a main TeX file into a preamble fragment and a stub main file.

        The preamble fragment receives everything between the
        ``\\documentclass`` line and ``\\begin{document}`` (both exclusive).
        The stub main file retains ``\\documentclass``, replaces the preamble
        block with a single ``\\input{<preamble_name>}`` line, and keeps
        everything from ``\\begin{document}`` onward intact.

        Resulting structure::

            % <main_name>.tex
            \\documentclass{...}

            \\input{preamble}

            \\begin{document}
            ...
            \\end{document}

            % <preamble_name>.tex
            \\usepackage{...}
            \\newcommand{...}
            ...

        :param input_tex: Path to the root ``.tex`` file to split. Must be a
            main document containing ``\\documentclass`` and
            ``\\begin{document}``.
        :type input_tex: str or pathlib.Path
        :param preamble_name: Stem for the preamble output file, without
            extension. Defaults to ``"preamble"``.
        :type preamble_name: str
        :param main_name: Stem for the stub main output file, without
            extension. Defaults to ``"main"``.
        :type main_name: str
        :param output_folder: Directory where both output files are written.
            When ``None`` (default), the parent directory of ``input_tex``
            is used.
        :type output_folder: str or pathlib.Path or None
        :returns: Tuple of ``(preamble_path, main_path)`` as resolved
            :class:`pathlib.Path` objects.
        :rtype: tuple[pathlib.Path, pathlib.Path]
        :raises ValueError: If ``input_tex`` does not contain a
            ``\\documentclass`` declaration (i.e. is not a main TeX file),
            if ``\\begin{document}`` is not found, or if the input file stem
            matches an output stem when both resolve to the same directory.
        """
        input_tex = Path(input_tex).absolute()
        output_folder = (
            Path(output_folder).absolute()
            if output_folder is not None
            else input_tex.parent
        )

        # Safety check: only raise if same folder AND stem collision
        # --------------------------------------------------
        if output_folder == input_tex.parent:
            for candidate in (preamble_name, main_name):
                if input_tex.stem == candidate:
                    raise ValueError(
                        f"Input file stem '{input_tex.stem}' matches output name "
                        f"'{candidate}' in the same directory '{output_folder}'. "
                        f"Provide a different output_folder or rename the output."
                    )

        preamble_path = output_folder / f"{preamble_name}.tex"
        main_path = output_folder / f"{main_name}.tex"

        # Parse the source file
        # --------------------------------------------------
        with open(input_tex, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Locate structural boundaries
        # --------------------------------------------------
        idx_documentclass = None
        idx_begin_document = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("%"):
                continue
            if idx_documentclass is None and stripped.startswith(r"\documentclass"):
                idx_documentclass = i
            if stripped.startswith(r"\begin{document}"):
                idx_begin_document = i
                break

        if idx_documentclass is None:
            raise ValueError(
                f"No \\documentclass declaration found in '{input_tex}'. "
                f"Only main TeX files can be split."
            )
        if idx_begin_document is None:
            raise ValueError(f"No \\begin{{document}} found in '{input_tex}'.")

        # Slice into regions
        # --------------------------------------------------
        before_preamble = lines[
            : idx_documentclass + 1
        ]  # \documentclass line (inclusive)
        preamble_lines = lines[idx_documentclass + 1 : idx_begin_document]
        after_preamble = lines[
            idx_begin_document:
        ]  # \begin{document} onward (inclusive)

        # Build preamble file: raw block, stripped of leading/trailing blank lines
        # --------------------------------------------------
        preamble_content = "".join(preamble_lines).strip() + "\n"

        # Build main file: documentclass + blank + \input{preamble} + blank + body
        # --------------------------------------------------
        main_content = (
            "".join(before_preamble).rstrip("\n")
            + "\n\n"
            + f"\\input{{{preamble_name}}}"
            + "\n\n"
            + "".join(after_preamble)
        )

        # Write outputs
        # --------------------------------------------------
        output_folder.mkdir(parents=True, exist_ok=True)

        preamble_path.write_text(preamble_content, encoding="utf-8")
        main_path.write_text(main_content, encoding="utf-8")

        return preamble_path, main_path

    @staticmethod
    def make_flat(input_tex, output_tex=None, assets=None):
        """
        Flatten a TeX document by recursively resolving ``\\input`` /
        ``\\include`` directives and embedding the compiled bibliography.

        This is a pure file-system operation with no dependency on any
        :class:`DocumentTeX` instance. It can be used independently whenever
        a self-contained ``.tex`` file is needed (e.g. arXiv submission).

        :param input_tex: Path to the root ``.tex`` file to flatten.
        :type input_tex: str or pathlib.Path
        :param output_tex: Destination path for the flattened file. When
            ``None`` (default), the result is written back over the source
            file in-place.
        :type output_tex: str or pathlib.Path or None
        :param assets: Optional set, populated as a side effect with the
            resolved absolute paths of every image (``\\includegraphics``)
            and bibliography resource (``\\addbibresource``) referenced
            anywhere in the document tree. Unlike ``\\bibliography``
            (see below), ``\\addbibresource`` references are left
            untouched in the flattened text -- biblatex/biber still needs
            to read the raw ``.bib`` file after flattening -- so this is
            the only way to learn which files must travel alongside the
            flattened output. When ``None`` (default), no collection is
            performed. Paths that can't be found on disk (e.g. images
            resolved via TeX's own search path rather than the project
            tree, such as the ``example-image-*`` placeholders) are never
            added.
        :type assets: set or None
        :returns: The fully flattened LaTeX source as a string.
        :rtype: str
        """
        input_tex = Path(input_tex).absolute()
        output_tex = (
            Path(output_tex).absolute() if output_tex is not None else input_tex
        )

        def _flatten_recursive(current_path):
            with open(current_path, "r", encoding="utf-8") as f:
                content = f.read()

            pattern_input = re.compile(r"\\(?:input|include)\s*\{\s*([^}]+)\s*\}")

            def replace_input(match):
                target_file = match.group(1).strip()
                if not target_file.endswith(".tex"):
                    target_file += ".tex"
                # \input/\include paths in LaTeX always resolve relative to the
                # root document's directory, regardless of nesting depth -- so
                # this must anchor on input_tex.parent, not current_path.parent.
                return _flatten_recursive(input_tex.parent / target_file)

            content = pattern_input.sub(replace_input, content)

            pattern_bib = re.compile(r"\\bibliography\s*\{\s*([^}]+)\s*\}")

            def replace_bib(match):
                bbl_path = input_tex.with_suffix(".bbl")
                if bbl_path.exists():
                    with open(bbl_path, "r", encoding="utf-8") as bbl_file:
                        return bbl_file.read()
                return match.group(0)

            content = pattern_bib.sub(replace_bib, content)

            if assets is not None:
                # \addbibresource{...} (biblatex) -- left in place in the
                # flattened text (biber still needs the raw .bib file after
                # flattening), so only the path is collected here.
                pattern_addbibresource = re.compile(
                    r"\\addbibresource\s*\{\s*([^}]+)\s*\}"
                )
                for m in pattern_addbibresource.finditer(content):
                    target = m.group(1).strip()
                    if not target.endswith(".bib"):
                        target += ".bib"
                    candidate = input_tex.parent / target
                    if candidate.exists():
                        assets.add(candidate)

                # \includegraphics[...]{...} -- the extension is frequently
                # omitted (LaTeX searches \Gin@extensions at compile time),
                # so every existing file matching that stem is collected.
                pattern_includegraphics = re.compile(
                    r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{\s*([^}]+)\s*\}"
                )
                _image_extensions = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".gif")
                for m in pattern_includegraphics.finditer(content):
                    target = m.group(1).strip()
                    candidate = input_tex.parent / target
                    if candidate.suffix:
                        if candidate.exists():
                            assets.add(candidate)
                    else:
                        for ext in _image_extensions:
                            found = input_tex.parent / (target + ext)
                            if found.exists():
                                assets.add(found)

            return content

        flat_content = _flatten_recursive(input_tex)

        with open(output_tex, "w", encoding="utf-8") as f_out:
            f_out.write(flat_content)

        return flat_content

    @staticmethod
    def _copy_assets(assets, source_root, export_dir):
        """
        Copy every resolved asset path into ``export_dir``, preserving its
        path relative to ``source_root`` so that the unmodified
        ``\\includegraphics``/``\\addbibresource`` references already
        present in the flattened output continue to resolve correctly
        without any text rewriting.

        :param assets: Absolute asset paths, as collected by
            :meth:`make_flat`.
        :type assets: set of pathlib.Path
        :param source_root: The document's original project root
            (typically ``self.file_data.parent``), used to compute each
            asset's relative destination inside ``export_dir``.
        :type source_root: pathlib.Path
        :param export_dir: The export folder assets are copied into.
        :type export_dir: pathlib.Path
        """
        for asset_path in assets:
            try:
                rel_path = asset_path.relative_to(source_root)
            except ValueError:
                rel_path = Path(asset_path.name)
            dest = export_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset_path, dest)

    @staticmethod
    def lint_paragraphs(input_tex, output_tex=None):
        """
        Join wrapped prose paragraphs in a LaTeX file into single lines.

        Reads ``input_tex``, joins each wrapped prose paragraph in the document
        body into a single source line, and writes the result to
        ``output_tex``.

        This function performs no backup of its own. When ``output_tex`` is
        ``None`` (or equal to ``input_tex``), the input file is overwritten in
        place; callers that want a safety copy should take one beforehand (see
        :func:`backup_file`).

        :param input_tex: Path to the source ``.tex`` file to read.
        :type input_tex: str or pathlib.Path
        :param output_tex: Path to write the linted result to. If ``None``
            (the default), ``input_tex`` is overwritten in place.
        :type output_tex: str or pathlib.Path or None

        :returns: The path the linted ``.tex`` was written to (equal to
            ``input_tex`` if ``output_tex`` was ``None``).
        :rtype: pathlib.Path

        :raises FileNotFoundError: If ``input_tex`` does not exist.
        :raises UnicodeDecodeError: If ``input_tex`` is not valid UTF-8.

        Algorithm
        ---------
        1. Everything up to and including ``\\begin{document}``, and everything
           from ``\\end{document}`` onward, is passed through unchanged. (The
           preamble's ``\\newcommand`` shorthand definitions are one-per-line by
           convention and must stay that way.)
        2. Within the document body, consecutive lines are grouped into
           "paragraphs": maximal runs of lines that are not blank, not
           ``\\begin{...}``/``\\end{...}``, not comment-only, and not inside a
           non-reflowable environment. Each run is joined into a single line:
           every line is stripped of leading/trailing whitespace, joined with a
           single space, and any remaining runs of spaces are collapsed to one.
        3. The following end the current paragraph and are emitted unchanged on
           their own line, without being joined to anything: blank lines;
           ``\\begin{...}``/``\\end{...}`` lines (which also push/pop an
           environment stack used to track non-reflowable regions, including
           nested ones, by scanning the *whole* line -- e.g. a ``pmatrix``
           opened and closed on the same line inside an ``equation``/``align``
           nets to zero rather than leaking a permanently elevated
           non-reflowable count); a comment-only line that appears *between*
           paragraphs; and ``\\[``/``\\]`` display-math delimiters on their own
           line (tracked like a pseudo-environment), or inline ``\\[ ... \\]``
           on one line.
        4. A ``%`` comment that appears *inside* a paragraph -- either a
           comment-only line with real content already buffered, or a trailing
           ``% ...`` after real content -- does **not** split the paragraph.
           The real content (if any) is kept in the paragraph, and the comment
           text is deferred and appended to the end of the paragraph's joined
           line once it is flushed. This avoids an editorial comment in the
           middle of a sentence cutting it into two "paragraphs", the second
           starting mid-sentence (lower-case).
        5. ``\\item`` always starts a new paragraph (flush before it), but its
           own wrapped continuation lines still join onto it -- so consecutive
           list items each end up on their own line.
        6. The following commands always stand alone on their own output line,
           never merged with the paragraph before or after them, even without a
           blank line in the source: ``\\tcblower``, ``\\newpage``,
           ``\\clearpage``, ``\\cleardoublepage``, ``\\pagebreak``, ``\\newline``,
           ``\\figplaceholder``, ``\\boxfigplaceholder``,
           ``\\boxbiofigplaceholder``, and ``\\chapter``/``\\section``/
           ``\\subsection``/``\\subsubsection`` (starred or not).
        7. Non-reflowable environments (passed through verbatim, line-by-line,
           including any blank lines inside them): ``equation``, ``align``,
           ``gather``, ``multline``, ``eqnarray``, ``alignat`` and their starred
           forms; ``array``, ``cases``, ``matrix``/``pmatrix``/``bmatrix``/
           ``vmatrix``/``Vmatrix``; ``tabular``, ``tabular*``, ``tabularx``,
           ``longtable``; ``verbatim``, ``lstlisting``, ``minted``, ``Verbatim``;
           and ``\\[ ... \\]`` display math.

        .. note::
           Only line breaks and runs of whitespace within a joined paragraph
           are changed; no other characters are altered, so the rendered PDF
           is unaffected.

        Example
        -------
        .. code-block:: python

            from pathlib import Path
            lint_paragraphs(Path("chapter07_T12.tex"))  # overwrite in place
            lint_paragraphs("chapter07_T12.tex", "chapter07_T12_linted.tex")
        """
        import re

        NO_REFLOW_ENVS = {
            "equation",
            "equation*",
            "align",
            "align*",
            "alignat",
            "alignat*",
            "gather",
            "gather*",
            "multline",
            "multline*",
            "eqnarray",
            "eqnarray*",
            "array",
            "matrix",
            "pmatrix",
            "bmatrix",
            "vmatrix",
            "Vmatrix",
            "cases",
            "tabular",
            "tabular*",
            "tabularx",
            "longtable",
            "verbatim",
            "verbatim*",
            "lstlisting",
            "minted",
            "Verbatim",
            "$$displaymath$$",  # pseudo-name for \[ ... \]
        }

        BEGIN_RE = re.compile(r"^\s*\\begin\{([^}]+)\}")
        END_RE = re.compile(r"^\s*\\end\{([^}]+)\}")
        TOKEN_RE = re.compile(r"\\(begin|end)\{([^}]+)\}")
        DISPLAY_OPEN_RE = re.compile(r"^\s*\\\[\s*$")
        DISPLAY_CLOSE_RE = re.compile(r"^\s*\\\]\s*$")
        DISPLAY_INLINE_RE = re.compile(r"^\s*\\\[.*\\\]\s*$")

        # Commands that always stand alone on their own output line -- never
        # merged with the paragraph before or after them, even without a blank
        # line in the source. These are one-shot structural commands
        # (placeholders, page breaks, pure headings) rather than prose.
        STANDALONE_RE = re.compile(
            r"^\s*\\(tcblower|newpage|clearpage|cleardoublepage|pagebreak|newline"
            r"|figplaceholder|boxfigplaceholder|boxbiofigplaceholder"
            r"|chapter\*?|section\*?|subsection\*?|subsubsection\*?)\b"
        )

        # \item always starts a new paragraph (flush before it), but its own
        # wrapped continuation lines still join onto it.
        ITEM_RE = re.compile(r"^\s*\\item\b")

        def find_comment_pos(line):
            """Return the index of the first un-escaped '%' in line, or -1."""
            i = 0
            while True:
                idx = line.find("%", i)
                if idx == -1:
                    return -1
                j = idx - 1
                nbs = 0
                while j >= 0 and line[j] == "\\":
                    nbs += 1
                    j -= 1
                if nbs % 2 == 0:
                    return idx
                i = idx + 1

        def process_tokens(line, env_stack, no_reflow):
            """
            Scan the (non-comment part of the) line for every
            \\begin{name}/\\end{name} token, in order, and update env_stack /
            no_reflow for each. A \\begin{X}...\\end{X} pair on the same line
            (e.g. a pmatrix inside an equation) therefore nets to zero, instead
            of leaking a permanently elevated no_reflow count. Returns the
            updated no_reflow.
            """
            pos = find_comment_pos(line)
            scan_part = line if pos == -1 else line[:pos]
            for m in TOKEN_RE.finditer(scan_part):
                kind, env = m.group(1), m.group(2)
                if kind == "begin":
                    env_stack.append(env)
                    if env in NO_REFLOW_ENVS:
                        no_reflow += 1
                else:
                    if env_stack and env_stack[-1] == env:
                        env_stack.pop()
                    if env in NO_REFLOW_ENVS:
                        no_reflow -= 1
            return no_reflow

        def join_paragraphs(text):
            """Join wrapped prose lines into one line per paragraph. Returns new text."""
            lines = text.split("\n")
            out = []
            buf = []
            env_stack = []
            no_reflow = 0
            seen_begin_document = False
            seen_end_document = False
            pending_comments = []

            def flush():
                if buf or pending_comments:
                    joined = " ".join(s.strip() for s in buf)
                    joined = re.sub(r" {2,}", " ", joined).strip()
                    if pending_comments:
                        extra = " ".join(c.strip() for c in pending_comments)
                        joined = f"{joined} {extra}".strip()
                    out.append(joined)
                    buf.clear()
                    pending_comments.clear()

            for line in lines:
                if not seen_begin_document or seen_end_document:
                    out.append(line)
                    m = BEGIN_RE.match(line)
                    if m and m.group(1) == "document":
                        seen_begin_document = True
                    continue

                stripped = line.strip()
                in_noreflow = no_reflow > 0

                m_begin = BEGIN_RE.match(line)
                m_end = END_RE.match(line)

                if in_noreflow:
                    out.append(line.rstrip())
                    no_reflow = process_tokens(line, env_stack, no_reflow)
                    if DISPLAY_CLOSE_RE.match(line):
                        if env_stack and env_stack[-1] == "$$displaymath$$":
                            env_stack.pop()
                            no_reflow -= 1
                    continue

                # not currently inside a non-reflowable environment
                if stripped == "":
                    flush()
                    out.append("")
                    continue

                if m_end:
                    env = m_end.group(1)
                    flush()
                    out.append(line.rstrip())
                    no_reflow = process_tokens(line, env_stack, no_reflow)
                    if env == "document":
                        seen_end_document = True
                    continue

                if m_begin:
                    flush()
                    out.append(line.rstrip())
                    no_reflow = process_tokens(line, env_stack, no_reflow)
                    continue

                if DISPLAY_INLINE_RE.match(line):
                    flush()
                    out.append(line.rstrip())
                    continue

                if DISPLAY_OPEN_RE.match(line):
                    flush()
                    out.append(line.rstrip())
                    env_stack.append("$$displaymath$$")
                    no_reflow += 1
                    continue

                if STANDALONE_RE.match(line):
                    flush()
                    out.append(line.rstrip())
                    continue

                if ITEM_RE.match(line):
                    flush()
                    # fall through: this line (and its wrapped continuation
                    # lines) form their own paragraph

                comment_pos = find_comment_pos(line)
                if comment_pos != -1:
                    before = line[:comment_pos]
                    if before.strip() == "":
                        if buf:
                            # comment-only line in the middle of a paragraph:
                            # defer it to the end of this paragraph's joined
                            # line rather than splitting the paragraph here
                            pending_comments.append(line.strip())
                        else:
                            # comment-only line between paragraphs: stands alone
                            flush()
                            out.append(line.rstrip())
                        continue
                    else:
                        # real content with a trailing comment: keep the
                        # content in the paragraph, defer the comment to the
                        # end of the joined line
                        buf.append(before)
                        pending_comments.append(line[comment_pos:].strip())
                        continue

                buf.append(line)

            flush()
            return "\n".join(out)

        input_tex = Path(input_tex)
        output_tex = Path(output_tex) if output_tex is not None else input_tex

        text = input_tex.read_text(encoding="utf-8")
        new_text = join_paragraphs(text)

        output_tex.write_text(new_text, encoding="utf-8")
        return output_tex

    @staticmethod
    def lint_decorations_remove(
        input_tex, output_tex=None, document_only=False, except_chars=None
    ):
        """
        Remove decoration comments/rulers (no letter characters after ``%``) from a
        LaTeX file.

        Reads ``input_tex``, strips every decorative comment (comment-only lines
        and trailing comment suffixes on prose lines whose comment text contains
        no ASCII letter), and writes the result to ``output_tex``.

        This function performs no backup of its own. When ``output_tex`` is
        ``None`` (or equal to ``input_tex``), the input file is overwritten in
        place; callers that want a safety copy should take one beforehand (see
        :func:`backup_file`).

        :param input_tex: Path to the source ``.tex`` file to read.
        :type input_tex: str or pathlib.Path
        :param output_tex: Path to write the purged result to. If ``None``
            (the default), ``input_tex`` is overwritten in place.
        :type output_tex: str or pathlib.Path or None
        :param document_only: If ``False`` (the default), the purge runs over
            the entire file -- preamble, body, and postamble alike.  If ``True``,
            only the lines between ``\\begin{document}`` and ``\\end{document}``
            are processed; the preamble and postamble are passed through unchanged.
        :type document_only: bool
        :param except_chars: Optional list of single characters. A decoration
            comment (one whose text after ``%`` contains no ASCII letter) is
            nonetheless **kept** if its text contains at least one character from
            this list. Use this to preserve specific ruler styles, e.g.
            ``except_chars=['#']`` keeps ``% ####`` lines.  ``None`` (the
            default) means no exceptions -- all decoration comments are removed.
        :type except_chars: list[str] or None

        :returns: The path the purged ``.tex`` was written to (equal to
            ``input_tex`` if ``output_tex`` was ``None``).
        :rtype: pathlib.Path

        :raises FileNotFoundError: If ``input_tex`` does not exist.
        :raises UnicodeDecodeError: If ``input_tex`` is not valid UTF-8.

        Algorithm
        ---------
        1. When ``document_only=True``, everything up to and including
           ``\\begin{document}``, and everything from ``\\end{document}`` onward,
           is passed through unchanged.  When ``document_only=False`` (default),
           all lines -- including the preamble -- are processed uniformly.
        2. Within the processed region each line is classified as one of:

           a. **Blank** – passed through unchanged.
           b. **Comment-only decoration** – the entire line's non-whitespace
              content is a ``%`` whose following text (stripped) contains no
              ASCII letter and no ``except_chars`` character.  The line is
              *dropped*; if the previous output line was blank, that blank is
              also removed (blank-line collapse).
           c. **Comment-only kept** – comment-only but preserved because the
              text contains a letter or an ``except_chars`` character.  Passed
              through unchanged.
           d. **Prose with trailing decoration comment** – the ``%`` suffix
              qualifies as decoration.  The suffix (and any whitespace before
              it) is stripped; the prose remainder is kept.
           e. **Prose with trailing real comment** – kept verbatim.
           f. **Prose without any comment** – kept verbatim.

        3. The ``%`` position is found via ``_find_comment_pos``, which
           correctly handles escaped percent signs (``\\%``).
        4. Non-reflowable environments (``equation``, ``align``, ``tabular``,
           ``verbatim``, etc.) receive no special treatment here: comment lines
           inside math or table environments are still subject to the same rule.

        .. note::
           Only comment text is removed; no other characters are altered, so
           the rendered PDF is unaffected.

        """
        import re

        BEGIN_DOCUMENT_RE = re.compile(r"^\s*\\begin\{document\}")
        END_DOCUMENT_RE = re.compile(r"^\s*\\end\{document\}")

        def _find_comment_pos(line):
            """Return the index of the first un-escaped '%' in *line*, or -1."""
            i = 0
            while True:
                idx = line.find("%", i)
                if idx == -1:
                    return -1
                # count immediately preceding backslashes
                j = idx - 1
                nbs = 0
                while j >= 0 and line[j] == "\\":
                    nbs += 1
                    j -= 1
                if nbs % 2 == 0:  # even number of backslashes -> real %
                    return idx
                i = idx + 1

        def _is_decoration(comment_text):
            """True when *comment_text* (text after the leading '%') should be removed.

            A comment qualifies as decoration when it contains no ASCII letter AND
            none of the characters in *except_chars* (captured from the outer
            scope).
            """
            if re.search(r"[A-Za-z]", comment_text):
                return False
            if except_chars and any(ch in comment_text for ch in except_chars):
                return False
            return True

        def _process_body(lines):
            """Apply decoration-comment purge to *lines*. Returns list of lines."""
            out = []

            for line in lines:
                # preserve blank lines as-is
                if line.strip() == "":
                    out.append(line)
                    continue

                comment_pos = _find_comment_pos(line)

                if comment_pos == -1:
                    # no comment at all
                    out.append(line)
                    continue

                before = line[:comment_pos]  # prose part (may be empty)
                comment_text = line[comment_pos + 1 :]  # everything after the %

                if before.strip() == "":
                    # ---- comment-only line ----
                    if _is_decoration(comment_text):
                        # drop this line; also collapse the preceding blank if present
                        if out and out[-1].strip() == "":
                            out.pop()
                        # do NOT append anything
                    else:
                        out.append(line)
                else:
                    # ---- prose line with a trailing comment ----
                    if _is_decoration(comment_text):
                        # strip the comment suffix; rstrip any whitespace before %
                        out.append(before.rstrip())
                    else:
                        out.append(line)

            return out

        # ------------------------------------------------------------------ #
        # Main entry: split into preamble / body / postamble, process body    #
        # ------------------------------------------------------------------ #
        input_tex = Path(input_tex)
        output_tex = Path(output_tex) if output_tex is not None else input_tex

        raw = input_tex.read_text(encoding="utf-8")
        lines = raw.split("\n")

        if not document_only:
            # Process the entire file uniformly -- no preamble/postamble split.
            result = "\n".join(_process_body(lines))
        else:
            # Restrict processing to the body between \begin{document} and
            # \end{document}; preamble and postamble pass through unchanged.
            preamble = []
            body_raw = []
            postamble = []

            seen_begin = False
            seen_end = False

            for line in lines:
                if not seen_begin:
                    preamble.append(line)
                    if BEGIN_DOCUMENT_RE.match(line):
                        seen_begin = True
                elif seen_end:
                    postamble.append(line)
                else:
                    if END_DOCUMENT_RE.match(line):
                        seen_end = True
                        postamble.append(line)
                    else:
                        body_raw.append(line)

            body_clean = _process_body(body_raw)
            result = "\n".join(preamble + body_clean + postamble)

        output_tex.write_text(result, encoding="utf-8")
        return output_tex

    @staticmethod
    def lint_decorations_add(
        input_tex, output_tex=None, ruler_chars=None, ruler_len=60
    ):
        """
        Inject decoration rulers above section headings in a LaTeX file.

        Reads ``input_tex``, inserts a comment ruler (``% `` + N repetitions of
        a level-specific character) on the line immediately before every
        ``\\chapter``, ``\\section``, ``\\subsection``, and ``\\subsubsection``
        command found inside the document body, then writes the result to
        ``output_tex``.

        The preamble (everything up to and including ``\\begin{document}``) and
        the postamble (``\\end{document}`` and everything after) are passed
        through unchanged.

        If a ruler with the correct character already exists on the line
        immediately before a heading, it is **replaced** rather than duplicated,
        making the function safe to call multiple times on the same file
        (idempotent with respect to ruler content; ruler length is always
        normalised to the current ``ruler_len``).

        This function performs no backup of its own. When ``output_tex`` is
        ``None`` (or equal to ``input_tex``), the input file is overwritten in
        place; callers that want a safety copy should take one beforehand (see
        :func:`backup_file`).

        :param input_tex: Path to the source ``.tex`` file to read.
        :type input_tex: str or pathlib.Path
        :param output_tex: Path to write the result to.  If ``None`` (the
            default), ``input_tex`` is overwritten in place.
        :type output_tex: str or pathlib.Path or None
        :param ruler_chars: Sequence of up to four characters, one per heading
            level (chapter, section, subsection, subsubsection).  Missing
            positions fall back to the defaults ``('#', '*', '=', '-')``.
            May be a string (each character is used positionally) or any
            sequence of single characters.  ``None`` uses all defaults.
        :type ruler_chars: str or list[str] or None
        :param ruler_len: Number of times the ruler character is repeated after
            the ``% `` prefix.  Defaults to ``60``.
        :type ruler_len: int

        :returns: The path the result was written to.
        :rtype: pathlib.Path

        :raises FileNotFoundError: If ``input_tex`` does not exist.
        :raises UnicodeDecodeError: If ``input_tex`` is not valid UTF-8.
        :raises ValueError: If ``ruler_len`` is less than 1.

        Algorithm
        ---------
        1. Split the file into preamble, body lines, and postamble at
           ``\\begin{document}`` / ``\\end{document}``.  Only the body is
           processed.
        2. Resolve the four ruler strings from ``ruler_chars`` and ``ruler_len``.
        3. Walk body lines.  When a line matches a heading command, look at the
           previous output line:

           - If it is already a ruler whose dominant character matches the
             current level's character, **replace** it with the freshly built
             ruler (normalises length on re-runs).
           - Otherwise **insert** the ruler as a new line before the heading.

        4. Reassemble preamble + processed body + postamble and write.

        .. note::
           A "ruler line" for replacement detection is defined as a line whose
           stripped content matches ``% <char><char>...`` with at least one
           repetition of *char* -- the same format this function produces.
           Any other comment line is left untouched even if it precedes a
           heading.

        """
        if ruler_len < 1:
            raise ValueError(f"ruler_len must be >= 1, got {ruler_len!r}")

        DEFAULTS = ("#", "*", "=", "-")
        LEVELS = ("chapter", "section", "subsection", "subsubsection")

        # Resolve ruler characters: positional override, fall back to defaults.
        resolved_chars = list(DEFAULTS)
        if ruler_chars is not None:
            for i, ch in enumerate(ruler_chars):
                if i >= 4:
                    break
                resolved_chars[i] = ch

        # Build the four ruler strings and their detection regexes.
        rulers = {}  # level_name -> ruler string
        ruler_res = (
            {}
        )  # level_name -> compiled regex that matches any ruler for that level
        for level, ch in zip(LEVELS, resolved_chars):
            rulers[level] = f"% {ch * ruler_len}"
            escaped = re.escape(ch)
            ruler_res[level] = re.compile(rf"^\s*%\s*{escaped}+\s*$")

        # Heading detection: \chapter, \section, \subsection, \subsubsection
        # (starred or unstarred), optionally followed by [] optional arg or {}.
        HEADING_RE = re.compile(
            r"^\s*\\(chapter|section|subsection|subsubsection)\*?\s*[\[{]"
        )

        BEGIN_DOCUMENT_RE = re.compile(r"^\s*\\begin\{document\}")
        END_DOCUMENT_RE = re.compile(r"^\s*\\end\{document\}")

        def _level_of(line):
            """Return the heading level name if *line* is a heading, else None."""
            m = HEADING_RE.match(line)
            return m.group(1) if m else None

        def _process_body(lines):
            """Inject rulers above headings. Returns new list of lines."""
            out = []
            for line in lines:
                level = _level_of(line)
                if level is None:
                    out.append(line)
                    continue

                ruler = rulers[level]
                ruler_re = ruler_res[level]

                # Check whether the previous output line is already a ruler for
                # this level; if so, replace it (idempotent).
                if out and ruler_re.match(out[-1]):
                    out[-1] = ruler
                else:
                    out.append(ruler)

                out.append(line)

            return out

        # ------------------------------------------------------------------ #
        # Split, process body, reassemble                                      #
        # ------------------------------------------------------------------ #
        input_tex = Path(input_tex)
        output_tex = Path(output_tex) if output_tex is not None else input_tex

        raw = input_tex.read_text(encoding="utf-8")
        lines = raw.split("\n")

        preamble = []
        body_raw = []
        postamble = []

        seen_begin = False
        seen_end = False

        for line in lines:
            if not seen_begin:
                preamble.append(line)
                if BEGIN_DOCUMENT_RE.match(line):
                    seen_begin = True
            elif seen_end:
                postamble.append(line)
            else:
                if END_DOCUMENT_RE.match(line):
                    seen_end = True
                    postamble.append(line)
                else:
                    body_raw.append(line)

        body_clean = _process_body(body_raw)

        result = "\n".join(preamble + body_clean + postamble)
        output_tex.write_text(result, encoding="utf-8")
        return output_tex

    @staticmethod
    def lint_blank_lines(input_tex, output_tex=None):
        """
        Normalize blank-line spacing in a LaTeX file.

        Reads ``input_tex`` and enforces two rules throughout the document body:

        * **Paragraph separation** -- any run of two or more consecutive blank
          lines in prose is collapsed to exactly one blank line.
        * **Environment padding** -- every ``\\begin{...}`` is preceded by
          exactly two blank lines, and every ``\\end{...}`` is followed by
          exactly two blank lines. The interior of every environment (everything
          between its ``\\begin`` and ``\\end``) is left completely untouched.

        Schematically, the target layout is::

            <prose>

            <blank>
            <blank>
            \\begin{equation}
              ...            <- interior: never touched
            \\end{equation}
            <blank>
            <blank>
            <prose>

        Nested environments produce nested padding::

            <blank>
            <blank>
            \\begin{subequations}

              <blank>
              <blank>
              \\begin{align}
                ...
              \\end{align}
              <blank>
              <blank>

            \\end{subequations}
            <blank>
            <blank>

        The preamble (everything up to and including ``\\begin{document}``) and
        the document environment boundary itself are exempt from padding.

        This function performs no backup of its own. When ``output_tex`` is
        ``None`` (or equal to ``input_tex``), the input file is overwritten in
        place; callers that want a safety copy should take one beforehand.

        :param input_tex: Path to the source ``.tex`` file to read.
        :type input_tex: str or pathlib.Path
        :param output_tex: Path to write the result to. If ``None`` (the
            default), ``input_tex`` is overwritten in place.
        :type output_tex: str or pathlib.Path or None

        :returns: ``(output_path, stats)`` where ``stats`` is a dict with keys
            ``collapsed`` (excess blank lines removed) and ``padded`` (blank
            lines inserted).
        :rtype: tuple[pathlib.Path, dict]

        :raises FileNotFoundError: If ``input_tex`` does not exist.
        :raises UnicodeDecodeError: If ``input_tex`` is not valid UTF-8.

        Algorithm
        ---------
        A single forward pass over the lines maintains:

        * ``env_depth`` -- nesting depth of padded environments (0 = prose).
        * ``pending_pad`` -- number of blank lines still to be emitted after
          an ``\\end{...}`` before the next non-blank content.

        When a ``\\begin{...}`` is encountered (outside the preamble and outside
        the document environment): any trailing blank lines in the output buffer
        are stripped, exactly two blank lines are inserted, and then the
        ``\\begin`` line itself is emitted. ``env_depth`` is incremented, and
        all subsequent lines (including blank ones) are passed through verbatim
        until the matching ``\\end{...}`` is reached. On ``\\end{...}``:
        ``env_depth`` is decremented, the ``\\end`` line is emitted, and
        ``pending_pad`` is set to 2. The next non-blank line flushes those two
        blank lines first. Any blank lines in the source between ``\\end`` and
        the next content are discarded (replaced by the controlled padding).


        """
        import re

        PAD = 2  # blank lines required before \begin and after \end

        # Environments exempt from padding (structural wrappers)
        NO_PAD_ENVS = {"document"}

        BEGIN_RE = re.compile(r"^\s*\\begin\{([^}]+)\}")
        END_RE = re.compile(r"^\s*\\end\{([^}]+)\}")

        def is_blank(line):
            return line.strip() == ""

        def strip_trailing_blanks(lst):
            """Remove trailing blank lines from lst; return count removed."""
            n = 0
            while lst and is_blank(lst[-1]):
                lst.pop()
                n += 1
            return n

        # ------------------------------------------------------------------
        input_tex = Path(input_tex)
        output_tex = Path(output_tex) if output_tex is not None else input_tex

        lines = input_tex.read_text(encoding="utf-8").split("\n")

        out = []
        n_collapsed = 0
        n_padded = 0

        seen_begin_doc = False
        seen_end_doc = False

        # env_depth > 0 means we are inside a padded environment: pass verbatim
        env_depth = 0
        # env_stack tracks names so nested \end matches correctly
        env_stack = []
        # pending_pad: blank lines to emit before the next non-blank content
        # (set after \end so we control the post-environment spacing)
        pending_pad = 0
        # consecutive blank lines in prose (for collapsing)
        prose_blanks = 0

        for line in lines:

            # ----------------------------------------------------------------
            # Preamble and post-document: verbatim
            # ----------------------------------------------------------------
            if not seen_begin_doc or seen_end_doc:
                out.append(line)
                m = BEGIN_RE.match(line)
                if m and m.group(1) == "document":
                    seen_begin_doc = True
                continue

            # ----------------------------------------------------------------
            # Inside a padded environment: pass everything verbatim
            # ----------------------------------------------------------------
            if env_depth > 0:
                m_end = END_RE.match(line)
                if m_end and env_stack and env_stack[-1] == m_end.group(1):
                    env_name = env_stack.pop()
                    env_depth -= 1
                    out.append(line)
                    if env_name not in NO_PAD_ENVS:
                        # Consume any source blank lines after \end
                        # (we will emit our own controlled padding instead)
                        pending_pad = PAD
                        prose_blanks = 0
                    if env_name == "document":
                        seen_end_doc = True
                else:
                    # Check for nested \begin inside the environment
                    m_begin = BEGIN_RE.match(line)
                    if m_begin:
                        env_stack.append(m_begin.group(1))
                        env_depth += 1
                    out.append(line)
                continue

            # ----------------------------------------------------------------
            # Prose region
            # ----------------------------------------------------------------
            m_begin = BEGIN_RE.match(line)
            m_end = END_RE.match(line)  # should not normally occur here

            if m_begin:
                env_name = m_begin.group(1)
                if env_name in NO_PAD_ENVS:
                    # document begin: no padding, just track
                    out.append(line)
                    env_stack.append(env_name)
                    env_depth += 1
                    seen_begin_doc = True
                else:
                    # Enforce PAD blank lines before \begin
                    n_removed = strip_trailing_blanks(out)
                    n_collapsed += max(0, n_removed - PAD)  # excess that were there
                    out.extend([""] * PAD)
                    n_padded += PAD
                    out.append(line)
                    env_stack.append(env_name)
                    env_depth += 1
                    prose_blanks = 0
                    pending_pad = 0
                continue

            # Blank line in prose
            if is_blank(line):
                if pending_pad > 0:
                    # Discard source blanks after \end; we control the padding
                    pass
                else:
                    prose_blanks += 1
                    if prose_blanks <= 1:
                        out.append(line)
                    else:
                        n_collapsed += 1
                continue

            # Non-blank, non-begin line in prose
            if pending_pad > 0:
                # Emit the controlled post-\end padding then this line
                out.extend([""] * pending_pad)
                n_padded += pending_pad
                pending_pad = 0
            prose_blanks = 0
            out.append(line)

        output_tex.write_text("\n".join(out), encoding="utf-8")
        return output_tex, {"collapsed": n_collapsed, "padded": n_padded}


class Essay(DocumentTeX):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/essay"


class Academic(Essay):
    # ------------
    # Academic documents are not provided by tecnical team
    # They diverge from professional documents first by the metadata
    # They can be a project but is a research project
    # They hold a list of authors (one or more)
    # Each author has attributes, including affiliation
    # the document hold a provider institution
    # other specificies can be develop downstream
    # Examples : article, thesis, grant proposals, research report

    # todo develop actual template
    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/academic/base"


class Article(Academic):
    # todo develop actual template
    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/academic/article"


class Preprint(Article):
    # todo develop actual template
    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/academic/preprint"


class PrintArticle(Article):
    # todo develop actual template
    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/academic/base"


class Professional(Essay):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/base"


class Report(Professional):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/report"


class Invoice(Professional):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/invoice"

    @staticmethod
    def _build_services_tex(config, paid=False):
        """
        Build the LaTeX services table string from a config dict.

        :param config: Dict with a ``services`` list (each entry has
            ``description``, ``quantity``, ``unit_price``) and an optional
            ``invoice`` sub-dict (``currency_symbol``, ``tax_rate``).
        :type config: dict
        :param paid: Append a ``PAID`` row when ``True`` (used by receipts).
        :type paid: bool
        :returns: Complete LaTeX fragment for the services table.
        :rtype: str
        """
        services = config.get("services", [])
        invoice_cfg = config.get("invoice", {})
        currency = invoice_cfg.get("currency_symbol", r"\texteuro\;")
        tax_rate = float(invoice_cfg.get("tax_rate", 0.0))

        def fmt_currency(value):
            return currency + f"{value:,.2f}"

        service_rows = []
        subtotal = 0.0
        for svc in services:
            desc = str(svc.get("description", ""))
            desc = desc.replace("&", r"\&")
            desc = escape_percent_latex(desc)
            qty = float(svc.get("quantity", 1.0))
            unit_price = float(svc.get("unit_price", 0.0))
            row_total = qty * unit_price
            subtotal += row_total
            service_rows.append(
                "    "
                + desc
                + " & "
                + f"{qty:.1f}"
                + " & "
                + fmt_currency(unit_price)
                + " & "
                + fmt_currency(row_total)
                + " \\\\ [1mm]"
            )

        tax = subtotal * tax_rate
        grand_total = subtotal + tax

        lines = [
            r"\noindent {\sf\textbf{Services}}",
            "",
            r"\noindent The provided services are listed below:",
            "",
            "",
            r"% start the table",
            r"\begin{table}[h!]",
            r"\centering",
            r"\footnotesize % table font size",
            r"\sffamily % table font style",
            r"\label{tbl:services}",
            r"\begin{tabular}{",
            r">{\raggedright\arraybackslash}p{7cm}",
            r">{\raggedright\arraybackslash}p{2cm}",
            r">{\raggedright\arraybackslash}p{2cm}",
            r">{\raggedright\arraybackslash}p{2cm}",
            r"}",
            r"    \toprule",
            r"    \textbf{Description} & \textbf{Quantity} & \textbf{Unit price} & \textbf{Total} \\ [1mm]",
            r"    \midrule",
        ]
        lines.extend(service_rows)
        lines += [
            r"    & & & \\ [1mm]",
            r"    \midrule",
            "    & & Subtotal & " + fmt_currency(subtotal) + " \\\\ [1mm]",
            "    & & Tax & " + fmt_currency(tax) + " \\\\ [1mm]",
            "    & & \\textbf{Total} & \\textbf{"
            + fmt_currency(grand_total)
            + "} \\\\ [1mm]",
        ]

        if paid:
            lines.append(r"    & & & \textcolor{OliveGreen}{\textbf{PAID}} \\ [1mm]")

        lines.append(r"    \end{tabular}")
        lines.append(r"\end{table}")

        return "\n".join(lines)

    def apply_config(self, config):
        """
        Rewrite ``partials/services-invoice.tex`` from a config dict.

        :param config: Dict with a ``services`` list and optional ``invoice``
            settings. Keys:

            - ``services``: list of dicts with ``description`` (str),
              ``quantity`` (float), and ``unit_price`` (float).
            - ``invoice.currency_symbol``: LaTeX currency prefix
              (default ``r"\\texteuro\\;"``).
            - ``invoice.tax_rate``: fraction applied to the subtotal
              (default ``0.0``).

        :type config: dict or None
        :returns: None
        :rtype: None
        """
        if config is None:
            return None
        content = Invoice._build_services_tex(config=config, paid=False)
        out_file = self.file_data.parent / "partials" / "services-invoice.tex"
        out_file.write_text(content, encoding="utf-8")
        return None


class Receipt(Invoice):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/receipt"

    def apply_config(self, config):
        """
        Rewrite ``partials/services-receipt.tex`` from a config dict.

        Identical structure to :meth:`Invoice.apply_config`, but appends
        a ``PAID`` row to the table.

        :param config: Same structure as :meth:`Invoice.apply_config`.
        :type config: dict or None
        :returns: None
        :rtype: None
        """
        if config is None:
            return None
        content = Invoice._build_services_tex(config=config, paid=True)
        out_file = self.file_data.parent / "partials" / "services-receipt.tex"
        out_file.write_text(content, encoding="utf-8")
        return None


class Proposal(Invoice):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/proposal"


class Agreement(Proposal):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/agreement"


class Contract(Agreement):

    VARIANT_TEMPLATE = FOLDER_TEMPLATES_DOCUMENTS / "tex/professional/contract"


# CONSTANTS -- Module-level
# =======================================================================
# Registry of document type keys consumed by Project.add_document(). Add
# new DocumentTeX subclasses here to make them available through that
# string-based interface.
DOCUMENT_TYPES = {
    "essay": Essay,
    "professional": Professional,
    "report": Report,
    "proposal": Proposal,
    "invoice": Invoice,
    "receipt": Receipt,
    "agreement": Agreement,
    "contract": Contract,
}

# ***********************************************************************
# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    print("Hello world!")
    # ... {develop}
