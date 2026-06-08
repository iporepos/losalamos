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
            ├── Preprint            (preprint / arXiv-style)
            ├── Report              (standard report)
            ├── ReportLarge         (multi-chapter report)
            └── Memo                (short internal memo)

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
import shutil
from pathlib import Path

# External imports
# =======================================================================
# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import DataSet
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
# ... {develop}


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

    def new(self, name, folder, template_overlay=None):
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

        :raises FileExistsError: If the target folder ``folder/name`` already exists.
            No files are created or modified in this case.
        :raises NotADirectoryError: If ``template_overlay`` is provided but does not
            point to a valid directory. Validated before any files are written.

        :returns: Absolute path to the newly created document folder.
        :rtype: pathlib.Path

        .. dropdown:: Usage example
            :icon: code-square
            :open:

            .. code-block:: python

                # Single-layer: base template only (Document base class)
                doc = Document(name="MyDoc", alias="D")
                target = doc.new("my_doc", "/home/user/documents")

                # Two-layer: base + variant (subclass sets VARIANT_TEMPLATE)
                report = Report(name="AnnualReport", alias="AR")
                target = report.new("annual_report", "/home/user/documents")

                # Three-layer: base + variant + private user overlay
                target = report.new(
                    "client_report",
                    "/home/user/documents",
                    template_overlay="/home/user/private/client_x",
                )
        """

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

        # Collect relative files from a template root
        # --------------------------------------------------
        def relative_files(root: Path) -> dict:
            """Returns {relative_path: absolute_path} for every file under root."""
            return {f.relative_to(root): f for f in root.rglob("*") if f.is_file()}

        # Build each active layer; higher layers overwrite lower ones
        # --------------------------------------------------
        merged = {}

        merged.update(relative_files(self.BASE_TEMPLATE))

        if self.VARIANT_TEMPLATE is not None:
            merged.update(relative_files(self.VARIANT_TEMPLATE))

        if template_overlay is not None:
            merged.update(relative_files(template_overlay))

        # Copy every resolved file to the target, preserving structure
        # --------------------------------------------------
        for rel_path, src in merged.items():
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

        return target


# CLASSES -- Module-level
# =======================================================================


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
            # 1. Compile
            # --------------------------------------------------
            compile_cmd = ["latexmk", f"-{command}"]

            # Use project-local latexmkrc if present
            if latexmkrc.exists():
                compile_cmd += ["-r", "latexmkrc"]

            compile_cmd += [source.name]

            subprocess.run(compile_cmd, check=True)

            # 2. Handle output destination
            # --------------------------------------------------
            default_pdf = source.with_suffix(".pdf")

            if file_output is not None:
                target_path = Path(file_output).absolute()
                shutil.copy2(default_pdf, target_path)
                default_pdf.unlink()

            # 3. Cleanup auxiliary files
            # --------------------------------------------------
            if cleanup:
                cleanup_cmd = ["latexmk", "-c"]
                if latexmkrc.exists():
                    cleanup_cmd += ["-r", "latexmkrc"]
                cleanup_cmd += [source.name]
                subprocess.run(cleanup_cmd, check=True)

        finally:
            os.chdir(original_dir)

        return None

    def to_flat(self, file_output=None, compile_first=True, command="pdf"):
        """
        Flatten the TeX document by recursively resolving ``\\input`` /
        ``\\include`` directives and embedding the compiled bibliography.

        The flattened output is a single self-contained ``.tex`` file
        suitable for journal submission (e.g. arXiv, Elsevier Editorial
        Manager). Only executes when :attr:`is_main` is ``True``; partial
        files return ``None`` silently.

        :param file_output: Desired output path for the flattened ``.tex``
            file. When ``None``, the result is returned as a string but not
            written to disk.
        :type file_output: str or pathlib.Path or None
        :param compile_first: If ``True`` (default), compiles the document
            before flattening so that the ``.bbl`` file reflects the current
            bibliography state. The intermediate PDF and ``.bbl`` are removed
            after flattening.
        :type compile_first: bool
        :param command: ``latexmk`` engine flag passed to :meth:`to_pdf` when
            ``compile_first=True``.
        :type command: str
        :returns: The fully flattened LaTeX document as a string, or ``None``
            if :attr:`is_main` is ``False``.
        :rtype: str or None
        """
        if not self.is_main:
            return None

        # 1. Compile to generate up-to-date .bbl
        # --------------------------------------------------
        if compile_first:
            self.to_pdf(file_output=None, command=command, cleanup=True)

        def _flatten_recursive(current_path):
            with open(current_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Flatten \input{} and \include{} commands
            # --------------------------------------------------
            pattern_input = re.compile(r"\\(?:input|include)\s*\{\s*([^}]+)\s*\}")

            def replace_input(match):
                target_file = match.group(1).strip()
                if not target_file.endswith(".tex"):
                    target_file += ".tex"
                return _flatten_recursive(current_path.parent / target_file)

            content = pattern_input.sub(replace_input, content)

            # Embed bibliography (.bbl)
            # --------------------------------------------------
            pattern_bib = re.compile(r"\\bibliography\s*\{\s*([^}]+)\s*\}")

            def replace_bib(match):
                bbl_path = self.file_data.with_suffix(".bbl")
                if bbl_path.exists():
                    with open(bbl_path, "r", encoding="utf-8") as bbl_file:
                        return bbl_file.read()
                return match.group(0)

            content = pattern_bib.sub(replace_bib, content)

            return content

        flat_content = _flatten_recursive(self.file_data)

        # 2. Aggressive cleanup of intermediate files
        # --------------------------------------------------
        if compile_first:
            for suffix in (".bbl", ".pdf"):
                p = self.file_data.with_suffix(suffix)
                if p.exists():
                    p.unlink()

        # 3. Export to file
        # --------------------------------------------------
        if file_output is not None:
            output_path = Path(file_output).absolute()
            with open(output_path, "w", encoding="utf-8") as f_out:
                f_out.write(flat_content)

        return flat_content


# ***********************************************************************
# SCRIPT
# ***********************************************************************
if __name__ == "__main__":
    print("Hello world!")
    # ... {develop}
