# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Reference management utilities for bibliographic metadata.

This module defines a schema-driven ``Reference`` base class and a registry
of entry-type subclasses (e.g., article, book, thesis). It provides tools for
loading, standardizing, formatting, and exporting references, including
BibTeX parsing, citation generation, and metadata templates.

Quick start
===========

This section demonstrates a few common operations with the reference system.

Load a reference from a BibTeX file

.. code-block:: python

    from losalamos.references import Reference

    ref = Reference.get_by_entry("article")
    ref.load_data("path/to/file.bib")

    print(ref.data)


Generate an in-text citation

.. code-block:: python

    citation = Reference.cite_line(ref.data)

    print(citation)
    # Example: "Smith et al. (2022)"


Generate a formatted bibliography entry

.. code-block:: python

    bibli = Reference.cite_bibli(
        ref.data,
        style="apa",
        text_format="plain",
    )

    print(bibli)


Export a BibTeX entry

.. code-block:: python

    ref.save()  # saves to the same file path used in load_data


Create a new reference manually

.. code-block:: python

    from losalamos.references import RefArticle

    ref = RefArticle()

    ref.setup_data({
        "name": "smith2022",
        "author": "Smith, John and Doe, Jane",
        "title": "Example Article",
        "year": "2022",
        "journal": "Journal of Examples",
        "volume": "10",
        "issue": "2",
        "pages": "100-110",
        "doi": "10.1000/example"
    })

    print(ref.get_str_bib())


Generate a BibTeX template

.. code-block:: python

    from losalamos.references import RefArticle

    ref = RefArticle()
    ref.export_template("path/to/file.bib")

"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
from pathlib import Path
import pprint, re

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import DataSet


# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}


# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================
# ... {develop}


# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************


# CLASSES -- Project-level
# =======================================================================


class Reference(DataSet):

    ENTRY_TYPE = None
    _REGISTRY = {}

    CORE_FIELDS = {
        "entry_type": None,
        "name": None,
        "author": None,
        "title": None,
        "year": None,
        "doi": None,
        "url": None,
        "abstract": None,
        "pdf": None,
    }

    SPECIFIC_FIELDS = None

    TAIL_ENTRIES = ["abstract", "pdf"]

    # ---------------------------------------------------------
    # Text formatting rules (role-based styling)
    # ---------------------------------------------------------
    FORMAT_RULES = {
        "plain": {
            "title": "{text}",
            "journal": "{text}",
        },
        "html": {
            "title": "<i>{text}</i>",
            "journal": "<b>{text}</b>",
        },
        "md": {
            "title": "*{text}*",
            "journal": "**{text}**",
        },
        "tex": {
            "title": r"\textit{{{text}}}",
            "journal": r"\textbf{{{text}}}",
        },
    }

    # ---------------------------------------------------------
    # Citation templates
    # ---------------------------------------------------------
    CITATION_TEMPLATES = {
        "apa": "{authors} ({year}). {title}.",
        "mla": "{authors}. {title}. {year}.",
        "chicago": "{authors}. {title}. {year}.",
        "harvard": "{authors} ({year}) {title}.",
        "vancouver": "{authors}. {title}. {year}.",
        "abnt": "{authors}. {title}. {year}.",
    }

    def __init__(self, name="MyReference", alias="Ref"):

        super().__init__(name=name, alias=alias)

        self.loading_order = 0
        self.entry_type_field = "entry_type"
        self.citation_key_field = "name"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Only register concrete subclasses with ENTRY_TYPE defined
        if cls.ENTRY_TYPE:
            key = cls.ENTRY_TYPE.lower()
            if key in cls._REGISTRY:
                raise ValueError(f"Duplicate ENTRY_TYPE detected: {key}")
            cls._REGISTRY[key] = cls

    @classmethod
    def get_by_entry(cls, entry_type: str, **kwargs):
        """
        Instantiates and returns a reference object based on the provided entry type from the registry.

        :param entry_type: The key representing the type of entry to retrieve.
        :type entry_type: str
        :return: An instance of the requested entry class, or a ``RefMisc`` instance if the type is not found.
        :rtype: :class:`Reference`
        """
        if entry_type not in cls._REGISTRY:
            # print(f"Warning: Entry type {entry_type} not found, falling back to 'misc'")
            entry_type = None

        return cls._REGISTRY.get(entry_type, RefMisc)(**kwargs)

    def __str__(self):
        str_type = str(type(self))
        str_df_metadata = self.get_metadata_df().to_string(index=False)
        str_super = "[{} ({})]\n{} ({}):\t{}\n{}".format(
            self.name,
            self.alias,
            self.object_name,
            self.object_alias,
            str_type,
            str_df_metadata,
        )

        if self.data is None:
            str_data = "None"
        else:
            str_data = pprint.pformat(self.data)

        str_out = "{}\nData:\n{}\n".format(str_super, str_data)
        return str_out

    def load_data(self, file_data):
        """
        Loads and parses bibliography data from a specified file path into the instance.

        :param file_data: The file path or name containing the data to be loaded.
        :type file_data: str | :class:`pathlib.Path`
        :return: No value is returned.
        :rtype: None
        """
        self.file_data = Path(file_data).absolute()

        # set up a parser system
        dc_parsers = {
            "bib": Reference.parse_bib,
        }
        # parse as a list
        extension = self.file_data.suffix[1:]
        ls = dc_parsers[extension](file_parse=self.file_data)
        self.setup_data(data=ls[self.loading_order].copy())
        return None

    def setup_data(self, data):
        """
        Initializes the instance data by creating a copy of the input and applying standardization.

        :param data: The raw dictionary or object containing reference metadata.
        :type data: dict | :class:`pandas.Series`
        :return: No value is returned.
        :rtype: None
        """
        self.data = data.copy()
        self.standardize()
        return None

    def save(self):
        """
        Saves the current reference data to the file path defined in ``file_data`` using the appropriate format.

        :return: No value is returned.
        :rtype: None
        """
        dc_saver = {"bib": Reference.to_bib}

        extension = self.file_data.suffix[1:]

        dc_saver[extension](self, output=self.file_data)
        return None

    def to_bib(self, output):
        """
        Generates a ``bib`` file from the current item's data
        and saves it to the specified output.

        :param output: file Path to output
        :type output: str or Path
        :return: The path to the saved ``bib`` file.
        :rtype: Path
        """

        dc_out = self.get_clean_data()

        bibtex_content = (
            f"@{dc_out[self.entry_type_field]}{{{dc_out[self.citation_key_field]},\n"
        )
        for key, value in dc_out.items():
            if key not in [self.entry_type_field, self.citation_key_field]:
                bibtex_content += f"  {key} = {{{value}}},\n"
        bibtex_content = bibtex_content.rstrip(",\n") + "\n}\n"

        # write file
        file_path = Path(output)

        with open(file_path, "w", encoding="utf-8") as bib_file:
            bib_file.write(bibtex_content)

        return file_path

    def get_clean_data(self):
        """
        Returns a copy of the internal data dictionary excluding all keys with ``None`` values.

        :return: A filtered dictionary containing only non-null reference data.
        :rtype: dict
        """
        dc = {}
        for k in self.data:
            if self.data[k] is not None:
                dc[k] = self.data[k]
        return dc.copy()

    def _increment_suffix(self, suffix: str) -> str:
        """
        Increment an alphabetic suffix using base-26 'odometer' logic.
        Examples: 'a' -> 'b', 'z' -> 'aa', 'az' -> 'ba', 'zz' -> 'aaa'
        """
        chars = list(suffix)
        carry = True
        for i in reversed(range(len(chars))):
            if carry:
                if chars[i] == "z":
                    chars[i] = "a"
                else:
                    chars[i] = chr(ord(chars[i]) + 1)
                    carry = False
        if carry:
            chars.insert(0, "a")
        return "".join(chars)

    def define_file_name(self, library_folder=None, extension="md", root_only=False):
        """
        Generate a unique filename based on author, year, and an incrementing
        alphabetic suffix to avoid collisions.

        The filename follows the pattern ``{author}_{year}_{suffix}``, where
        ``suffix`` starts at ``"a"`` and increments through ``"b"``, ``"c"``,
        ..., ``"z"``, ``"aa"``, ``"ab"``, and so on — supporting an unlimited
        number of collisions via variable-length base-26 suffixes.

        If ``library_folder`` is provided and exists, the directory is scanned
        for files matching ``{author}_{year}_*.{extension}``. By default the
        scan is **recursive** (all subfolders included); set ``root_only=True``
        to restrict the search to the top-level folder only. The highest
        existing suffix (ordered by length first, then alphabetically) is
        identified and incremented to produce the next unique name. If no
        matching files are found, the suffix defaults to ``"a"``.

        The table below illustrates the filename suffix sequence:

        .. list-table::
           :header-rows: 1
           :widths: auto

           * - Filename
             - Entry index
           * - ``Smith_2020_a``
             - 1st
           * - ``Smith_2020_b``
             - 2nd
           * - ``Smith_2020_z``
             - 26th
           * - ``Smith_2020_aa``
             - 27th
           * - ``Smith_2020_az``
             - 52nd
           * - ``Smith_2020_ba``
             - 53rd
           * - ``Smith_2020_aaa``
             - 703rd

        :param library_folder: Directory to scan for existing files when
            determining the next suffix. If ``None`` or the path does not
            exist, the suffix defaults to ``"a"``.
        :type library_folder: str or :class:`pathlib.Path`, optional
        :param extension: File extension used when globbing for existing
            filename collisions. Defaults to ``"md"``.
        :type extension: str
        :param root_only: If ``True``, restricts the search to the top-level
            of ``library_folder``, ignoring subfolders. Defaults to ``False``
            (recursive scan).
        :type root_only: bool
        :return: The generated filename string in the format
            ``{author}_{year}_{suffix}``, without a file extension.
        :rtype: str
        """

        # -------------------------------------------------------
        # 1. Build the base key (author + year)
        # -------------------------------------------------------

        entry_type = self.data.get("entry_type").strip()

        cite = self.cite_line(self.data, text_format="plain", embed_link=False)

        if entry_type in ["article", "book"]:
            author = cite.split(" ")[0]
        else:
            author = "".join(cite.split(" ")[:-1])

        year = str(self.data["year"])

        suffix = "a"

        # -------------------------------------------------------
        # 2. If a library folder is provided, inspect it
        # -------------------------------------------------------

        if library_folder:
            import string

            dst_folder = Path(library_folder)

            if dst_folder.is_dir():

                # -------------------------------------------------------
                # 3. Search for existing files matching the pattern
                #
                # Example pattern: Smith_2020_*.md
                # -------------------------------------------------------

                pattern = f"{author}_{year}_*.{extension}"
                glob_fn = dst_folder.glob if root_only else dst_folder.rglob
                existing_files = list(glob_fn(pattern))

                # -------------------------------------------------------
                # 4. Extract suffix letters from existing filenames
                # -------------------------------------------------------

                suffixes = []

                for f in existing_files:
                    name = f.stem
                    parts = name.split("_")

                    # Expected structure: [author, year, suffix]
                    if len(parts) >= 3:
                        candidate_suffix = parts[-1]

                        # Accept any non-empty all-lowercase suffix (a, z, aa, ab, ...)
                        if candidate_suffix and all(
                            c in string.ascii_lowercase for c in candidate_suffix
                        ):
                            suffixes.append(candidate_suffix)

                # -------------------------------------------------------
                # 5. Determine the next suffix in the sequence
                #
                # Sort by (length, value) so that 'z' < 'aa' — plain
                # lexicographic max() would incorrectly rank 'b' > 'aa'.
                # -------------------------------------------------------

                if suffixes:
                    last_suffix = max(suffixes, key=lambda s: (len(s), s))
                    suffix = self._increment_suffix(last_suffix)

        # -------------------------------------------------------
        # 6. Build and return the final filename
        # -------------------------------------------------------

        return f"{author}_{year}_{suffix}"

    def get_str_bib(self):
        """
        Converts the dictionary representation of a BibTeX entry into a string.

        :return: The BibTeX entry as a formatted string.
        :rtype: str
        """
        dc_out = self.get_clean_data()
        #
        citation_key = dc_out[self.citation_key_field]

        # list available fields
        bibtex_fields = [
            f"{key} = {{{value}}}"
            for key, value in dc_out.items()
            if key not in [self.entry_type_field, self.citation_key_field]
        ]

        # build the string
        bibtex_str = (
            f"@{dc_out[self.entry_type_field]}{{{citation_key},\n  "
            + ",\n  ".join(bibtex_fields)
            + "\n}"
        )
        return bibtex_str

    def standardize(self):
        """
        Standardizes the internal data dictionary by enforcing schema fields, ordering, and formatting rules.

        .. note::

             This method reconstructs the ``data`` attribute by merging ``CORE_FIELDS`` and ``SPECIFIC_FIELDS``.
             It ensures all expected keys exist (defaulting to ``None``), reorders specific metadata to the
             end of the dictionary based on ``TAIL_ENTRIES``, and applies specific formatting logic
             to the abstract and author fields via ``harmonize_abstract`` and ``standardize_author``.

        :return: No value is returned.
        :rtype: None
        """
        new_data = {}

        ls_keys = list(self.CORE_FIELDS.keys())

        if self.SPECIFIC_FIELDS is not None:
            ls_keys = ls_keys + list(self.SPECIFIC_FIELDS.keys())

        # Fill empty keys
        # -----------------------------
        for k in ls_keys:
            if k in list(self.data.keys()):
                new_data[k] = self.data[k]
            else:
                new_data[k] = None

        # Send abstract and file to the end
        for k in self.TAIL_ENTRIES:
            new_data[k] = new_data.pop(k)

        if self.ENTRY_TYPE is not None:
            new_data[self.entry_type_field] = self.ENTRY_TYPE

        self.data = new_data.copy()

        self.harmonize_abstract()

        if self.data["author"] is not None:
            self.data["author"] = Reference.standardize_author(self.data)

        return None

    def harmonize_abstract(self):
        """
        Ensures the abstract field is properly formatted by escaping LaTeX-specific percent symbols.

        :return: No value is returned.
        :rtype: None
        """
        if self.data["abstract"] is not None:
            from losalamos.documents import escape_percent_latex

            text = self.data["abstract"][:]
            self.data["abstract"] = escape_percent_latex(text)

    def export_template(self, output):
        """
        Generates an empty metadata template file based on the current class schema and exports it.

        .. note::

             This method temporarily replaces the instance data with a skeleton derived from ``CORE_FIELDS``
             and ``SPECIFIC_FIELDS``. It runs the ``standardize`` routine to ensure correct field ordering,
             clears all values except the entry type, and calls ``to_bib`` to write the template to the
             specified output path before restoring the original data state.

        :param output: The file path or buffer where the template should be saved.
        :type output: str | :class:`pathlib.Path` | file-like object
        :return: No value is returned.
        :rtype: None
        """
        current_data = None
        if self.data is not None:
            current_data = self.data.copy()

        self.data = self.CORE_FIELDS.copy()
        if self.SPECIFIC_FIELDS is not None:
            self.data.update(self.SPECIFIC_FIELDS.copy())

        self.standardize()

        for k in list(self.data.keys()):
            if k == self.entry_type_field:
                pass
            else:
                self.data[k] = ""
        self.to_bib(output=output)

        self.data = current_data
        return None

    @staticmethod
    def parse_bib(file_parse):
        """
        Parse a ``bib`` file and return a list of references as dictionaries.

        :param file_parse: Path to the ``bib`` file.
        :return: A list of dictionaries, each representing a BibTeX bib_dict.
        """
        entries = []
        entry = None
        key = None

        with open(file_parse, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                # Ignore empty lines and body
                if not line or line.startswith("%"):
                    continue

                # New bib_dict starts
                if line.startswith("@"):
                    if entry is not None:
                        entries.append(entry)
                    entry = {}
                    # Extracting the entry_type and citation key
                    entry_type, citation_key = line.lstrip("@").split("{", 1)
                    entry["entry_type"] = entry_type
                    entry["name"] = citation_key.rstrip(",").strip()
                elif "=" in line and entry is not None:
                    # Extracting the field key and value
                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip().strip("{").strip(",").strip("}")
                    entry[key] = value
                elif entry is not None and key:
                    # Continuation of a field value in a new line
                    entry[key] += " " + line.strip().strip("{").strip("}").strip(",")

        # Add the last bib_dict if it exists
        if entry is not None:
            # ensure values are stripped:
            entry_new = {}
            for k in entry:
                entry_new[k] = entry[k].strip()
            entries.append(entry_new)

        stripped_data = [
            {key: value.strip() for key, value in item.items()} for item in entries
        ]

        return stripped_data

    @staticmethod
    def cite_line(bib_dict, text_format="plain", embed_link=False):
        """
        Format a dictionary of bibliometric parameters into an in-line
        citation string with optional DOI or URL links.
        """

        # ---------------------------------------------------------
        # Helper: Apply formatting rules depending on output format
        # ---------------------------------------------------------
        def apply_format(text, text_format):
            # Create a shallow copy of the string (strings are immutable,
            # so this is mostly stylistic rather than necessary)
            formatted = text[:]

            # No transformation for plain text
            if text_format == "plain":
                pass

            # HTML formatting
            # Replace "et al." with italic version
            elif text_format == "html":
                formatted = text.replace("et al.", "<i>et al.</i>")

            # Markdown formatting
            # Replace "et al." with Markdown italics
            elif text_format == "md":
                formatted = text.replace("et al.", "*et al.*")

            # LaTeX formatting
            # - Italicize "et al."
            # - Escape ampersand (special character in TeX)
            elif text_format == "tex":
                formatted = text.replace("et al.", r"\textit{et al.}")
                formatted = formatted.replace("&", r"\&")

            return formatted

        # ---------------------------------------------------------
        # Helper: Wrap the citation string in a hyperlink
        # depending on output format
        # ---------------------------------------------------------
        def embed_link(text, text_format, link):

            # HTML anchor tag
            if text_format == "html":
                return f'<a href="{link}">{text}</a>'

            # Markdown link syntax
            elif text_format == "md":
                return f"[{text}]({link})"

            # LaTeX hyperlink (requires hyperref package)
            elif text_format == "tex":
                return f"\\href{{{link}}}{{{text}}}"

            # If format does not support linking, return unchanged
            return text

        def get_author_alias(author):
            # handle first author
            if "," in author:
                return author.split(",")[0].strip()
            elif "(" in author and ")" in author:
                return author.split("(")[1].split(")")[0].strip()
            else:
                return author

        # ---------------------------------------------------------
        # Defensive normalization:
        # Replace None values with empty strings
        # This prevents .strip() from failing later.
        # ---------------------------------------------------------
        bib_dict = {
            key: (value if value is not None else "") for key, value in bib_dict.items()
        }

        # ---------------------------------------------------------
        # Extract relevant bibliographic fields
        # Provide fallback defaults when missing
        # ---------------------------------------------------------
        author = bib_dict.get("author", "Unknown Author").strip()
        year = str(bib_dict.get("year", "n.d.")).strip()
        doi = bib_dict.get("doi", "").strip()
        url = bib_dict.get("url", "").strip()
        entry_type = bib_dict.get("entry_type", "misc").strip()

        # ---------------------------------------------------------
        # Build author string for in-text citation
        #
        # Assumes authors are already normalized as:
        # "Last, First and Last, First"
        # ---------------------------------------------------------
        if "(" not in author:
            author_list = author.split(" and ")

            # More than two authors:
            # Use "FirstAuthor et al."
            if len(author_list) > 2:
                first_author_alias = get_author_alias(author_list[0])
                formatted_authors = f"{first_author_alias} et al."

            # Exactly two authors:
            # Use "FirstAuthor & SecondAuthor"
            elif len(author_list) == 2:
                first_author_alias = get_author_alias(author_list[0])
                second_author_alias = get_author_alias(author_list[1])
                formatted_authors = f"{first_author_alias} & {second_author_alias}"

            # Single author:
            # If there is only one author in the author_list
            else:
                first_author_alias = get_author_alias(author)
                formatted_authors = first_author_alias
        else:
            first_author_alias = get_author_alias(author)
            formatted_authors = first_author_alias

        # Apply format-specific styling (italics, escaping, etc.)
        formatted_authors = apply_format(formatted_authors, text_format)

        # ---------------------------------------------------------
        # Construct final in-text citation
        # Example: "Einstein (1905)"
        # ---------------------------------------------------------
        in_text_citation = f"{formatted_authors} ({year})"

        # ---------------------------------------------------------
        # Optionally embed hyperlink (DOI preferred over URL)
        # ---------------------------------------------------------
        if embed_link:

            # Prefer DOI if available
            if doi:
                link = doi

                # Normalize DOI to full HTTPS form if needed
                if not doi.startswith("https://doi.org/"):
                    link = f"https://doi.org/{doi}"
            else:
                link = url

            # Only embed link for supported formats
            if link and text_format in ["html", "md", "tex"]:
                in_text_citation = embed_link(in_text_citation, text_format, link)

        # Return formatted citation string
        return in_text_citation

    @staticmethod
    def cite_bibli(bib_dict, style="apa", text_format="plain"):
        """
        Generate a formatted bibliographic citation string based on a dictionary
        of metadata and a specified style.

        :param bib_dict: Dictionary containing bibliographic fields such as ``author``, ``year``, ``title``, and ``entry_type``.
        :type bib_dict: dict
        :param style: The citation style to use (e.g., ``apa``). Default value = ``apa``
        :type style: str
        :param text_format: The markup format for the output string (e.g., ``plain``, ``html``, or ``latex``). Default value = ``plain``
        :type text_format: str
        :return: A cleaned, single-line citation string.
        :rtype: str

        .. note:: Processing Logic

            The function normalizes input dictionary values, handles author list formatting (splitting by ``and``),
            and applies text formatting rules (e.g., italics or bold) based on the ``text_format``.
            It then maps to a specific template defined in ``self.CITATION_TEMPLATES``.

        .. warning::

             If the provided ``entry_type`` or ``style`` is not found in the internal templates,
             it defaults to the ``article`` type in ``apa`` style.

        """
        entry_type = bib_dict["entry_type"]

        # 1) Normalize None values
        bib = {k: (v if v is not None else "") for k, v in bib_dict.items()}

        # 2) Extract and clean fields
        author = bib.get("author", "Unknown Author").strip()
        year = str(bib.get("year", "n.d.")).strip()
        title_raw = bib.get("title", "Untitled").strip().strip('"')
        journal_raw = bib.get("journal", "").strip().strip('"')
        volume = bib.get("volume", "").strip()
        issue = bib.get("issue", "").strip()
        pages = bib.get("pages", "").strip()
        doi = bib.get("doi", "").strip()
        publisher = bib.get("publisher", "").strip().strip('"')
        organization = bib.get("organization", "").strip().strip('"')
        address = bib.get("location", "").strip()
        note = bib.get("note", "").strip()
        url = bib.get("url", "").strip()
        version = bib.get("version", "V1").strip().strip('"')

        # 3) Format authors (simple join logic preserved)
        if author.startswith("{") and author.endswith("}"):
            formatted_authors = author
        else:
            author_list = author.split(" and ")
            if len(author_list) > 1:
                formatted_authors = "; ".join(author_list[:])
            else:
                formatted_authors = author_list[0]

        # 4) Apply role-based text formatting
        format_rules = Reference.FORMAT_RULES.get(
            text_format, Reference.FORMAT_RULES["plain"]
        )

        def apply_role(text, role):
            template = format_rules.get(role, "{text}")
            return template.format(text=text)

        title = apply_role(title_raw, "title")
        journal = apply_role(journal_raw, "journal")

        # 5) Precompute reusable derived fields
        volume_issue = f"{volume}({issue})" if issue else volume
        pages_str = f", {pages}" if pages else ""
        doi_str = doi if doi else ""

        # 6) Build rendering context
        context = {
            "authors": formatted_authors,
            "year": year,
            "title": title,
            "raw_title": title_raw,
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "volume_issue": volume_issue,
            "pages_str": pages_str,
            "doi": doi_str,
            "publisher": publisher,
            "address": address,
            "note": note,
            "url": url,
            "organization": organization,
            "version": version,
        }

        # 7) Resolve template
        ref_class = Reference._REGISTRY.get(entry_type, RefMisc)
        template = ref_class.CITATION_TEMPLATES.get(style)

        # 8) Render citation
        citation = template.format(**context)

        # 9) Cleanup excessive whitespace
        citation = " ".join(citation.split())
        citation = citation.replace(" .", ".")
        citation = citation.replace("..", ".")
        citation = citation.strip('"')

        return citation

    @staticmethod
    def standardize_author(bib_dict):
        """
        Standardizes the ``author`` field in a BibTeX entry.

        :param bib_dict: The dictionary containing the BibTeX entry data, expected to have an ``author`` field.
        :type bib_dict: dict
        :return: A formatted string of standardized author names.
        :rtype: str
        """

        # ---------------------------------------------------------
        # Internal helper function to normalize a single author name
        # ---------------------------------------------------------
        def normalize_author_name(author_name):
            # Case 1: If the name already contains a comma,
            # we assume it is already in "Last, First" format.
            # Example: "Einstein, Albert"
            if "," in author_name:
                return author_name.strip()

            # Case 2: Name does NOT contain a comma.
            # Likely in "First Last" format.
            else:
                parts = author_name.split()  # Split by whitespace

                # Subcase 2.1: Only one part (e.g., "Plato" or initials)
                # Nothing to reorder.
                if len(parts) == 1:
                    return author_name.strip()

                # Subcase 2.2: Two parts (e.g., "Albert Einstein")
                # Convert to "Einstein, Albert"
                elif len(parts) == 2:
                    return f"{parts[1]}, {parts[0]}"

                # Subcase 2.3: More than two parts
                # Assume last token is the surname.
                # Example: "John Ronald Reuel Tolkien"
                # -> "Tolkien, John Ronald Reuel"
                else:
                    return f"{parts[-1]}, {' '.join(parts[:-1])}"

        # This will store the final formatted author string
        standard_authors = ""

        # ---------------------------------------------------------
        # Main logic

        # If the author string contains:
        # - a comma (meaning at least one name may already be formatted), OR
        # - " and " (BibTeX separator for multiple authors)
        #
        # Then we process it more carefully.
        if "," in bib_dict["author"] or " and " in bib_dict["author"]:

            # Split authors using BibTeX standard separator " and "
            # Example:
            # "Albert Einstein and Niels Bohr"
            # -> ["Albert Einstein", "Niels Bohr"]
            author_list = [
                normalize_author_name(a.strip())
                for a in bib_dict["author"].split(" and ")
            ]

            # Rejoin authors in BibTeX format using " and "
            # Example:
            # ["Einstein, Albert", "Bohr, Niels"]
            # -> "Einstein, Albert and Bohr, Niels"
            standard_authors = " and ".join(author_list)

        # If there is no comma and no " and ",
        else:
            # ... but if is article or thesis
            entry_type = bib_dict["entry_type"]
            if entry_type == "article" or entry_type == "thesis":
                # ... then it is formatted as Last, First
                standard_authors = normalize_author_name(bib_dict["author"])
            # Else assumes single authorship by institution name, etc
            else:
                standard_authors = bib_dict["author"]

        # Return the standardized author string
        return standard_authors


class RefArticle(Reference):

    ENTRY_TYPE = "article"

    SPECIFIC_FIELDS = {
        "issn": None,
        "journal": None,
        "issue": None,
        "volume": None,
        "number": None,
        "pages": None,
        "month": None,
    }

    CITATION_TEMPLATES = {
        "apa": "{authors} ({year}). {title}. {journal}, {volume_issue}{pages}. {doi}",
        "mla": "{authors}. {raw_title}. {journal} {volume}. {issue} ({year}): {pages}. {doi}",
        "chicago": "{authors}. {raw_title}. {journal} {volume}, no. {issue} ({year}): {pages}. {doi}",
        "harvard": "{authors} ({year}) {raw_title}, {journal}, vol. {volume}, no. {issue}, pp. {pages}. {doi}",
        "vancouver": "{authors}. {title}. {journal}. {year}; {volume} ({issue}):{pages}. {doi}",
        "abnt": "{authors}. {title}. {journal}, {volume} ({issue}), p. {pages}, {year}. {doi}",
    }

    def load_data(self, file_data):
        super().load_data(file_data=file_data)
        self.harmonize_issue()

    def harmonize_issue(self):
        if self.data["issue"] is None:
            self.data["issue"] = "1"


class RefBook(Reference):

    ENTRY_TYPE = "book"

    SPECIFIC_FIELDS = {
        "isbn": None,
        "publisher": None,
        "subtitle": None,
        "edition": None,
    }

    CITATION_TEMPLATES = {
        "apa": "{authors} ({year}). {title}. {publisher}.",
        "mla": "{authors}. {title}. {publisher}, {year}.",
        "chicago": "{authors}. {title}. {location}: {publisher}, {year}.",
        "harvard": "{authors} ({year}) {title}, {publisher}.",
        "vancouver": "{authors}. {title}. {publisher}; {year}.",
        "abnt": "{authors}. {title}. {publisher}, {year}.",
    }


class RefTechreport(Reference):

    ENTRY_TYPE = "techreport"

    SPECIFIC_FIELDS = {
        "subtitle": None,
        "institution": None,
        "language": None,
        "version": None,
        "location": None,
        "note": None,
    }


class RefThesis(Reference):
    ENTRY_TYPE = "thesis"
    SPECIFIC_FIELDS = {
        "type": None,
        "institution": None,
        "language": None,
        "location": None,
        "note": None,
    }


class RefDataset(Reference):
    ENTRY_TYPE = "dataset"
    SPECIFIC_FIELDS = {
        "organization": None,
        "version": None,
        "note": None,
    }
    CITATION_TEMPLATES = {
        "apa": "{authors} ({year}). {title}. {organization}. {version} [Data Set] {url}.",
        "mla": "{authors}. {title}. {year}. {organization}. {version} [Data Set] {url}.",
        "chicago": "{authors}. {title}. {year}. {organization}. {version} [Data Set] {url}.",
        "harvard": "{authors} ({year}) {title}. {organization}. {version} [Data Set] {url}.",
        "vancouver": "{authors}. {title}. {year}.  {organization}. {version} [Data Set] {url}.",
        "abnt": "{authors}. {title}. {year}. {organization}. {version} [Data Set] {url}.",
    }


class RefInproceedings(Reference):
    ENTRY_TYPE = "inproceedings"
    SPECIFIC_FIELDS = {
        "isbn": None,
        "booktitle:": None,
        "location": None,
        "organization": None,
    }


class RefInbook(Reference):
    ENTRY_TYPE = "inbook"
    SPECIFIC_FIELDS = {
        "isbn": None,
        "publisher": None,
        "subtitle": None,
        "chapter": None,
        "edition": None,
        "booktitle:": None,
    }
    CITATION_TEMPLATES = {
        "apa": "{authors} ({year}). {title}. {note}. {url}.",
        "mla": "{authors}. {title}. {note}, {year}.",
        "chicago": "{authors}. {title}. {note}, {year}.",
        "harvard": "{authors} ({year}) {title}, {note}.",
        "vancouver": "{authors}. {title}. {note}; {year}.",
        "abnt": "{authors}. {title}. {note}, {year}.",
    }


class RefMisc(Reference):

    ENTRY_TYPE = "misc"
    SPECIFIC_FIELDS = {"organization": None, "note": None, "howpublished": None}


class RefOnline(Reference):

    ENTRY_TYPE = "online"
    SPECIFIC_FIELDS = RefMisc.SPECIFIC_FIELDS


class RefSoftware(Reference):

    ENTRY_TYPE = "software"
    SPECIFIC_FIELDS = RefMisc.SPECIFIC_FIELDS


class RefLegislation(Reference):

    ENTRY_TYPE = "legislation"
    SPECIFIC_FIELDS = RefMisc.SPECIFIC_FIELDS


# CLASSES -- Module-level
# =======================================================================
# ... {develop}


REFERENCE_DISPATCHER = {
    "article": RefArticle,
    "book": RefBook,
    "techreport": RefTechreport,
    "thesis": RefThesis,
    "inproceedings": RefInproceedings,
    # ... continue
}

# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    from losalamos.paths import FOLDER_TEMPLATES
    from tests.conftest import OUTPUT_DIR

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    ls = [
        RefArticle,
        RefBook,
        RefTechreport,
        RefThesis,
        RefInproceedings,
    ]

    for r in ls:
        a = r()
        o = OUTPUT_DIR / f"bibtex/{a.ENTRY_TYPE}.bib"
        a.export_template(output=o)
