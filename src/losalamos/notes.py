# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import re
from pathlib import Path
from datetime import datetime

# ... {develop}

# External imports
# =======================================================================
import pandas as pd

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import MbaE, Collection
from losalamos.paths import FOLDER_TEMPLATES_NOTES

# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}


# list of fields that needs harmonization
HARMONIZE_TEXT_FIELDS = [
    "name",
    "title",
    "subject",
    "abstract",
    "contract",
    "client",
    "project",
    "comment",
    "caption",
    "alttext",
    "source",
]
HARMONIZE_DATE_FIELDS = [
    "timestamp",
    "date",
    "datetime",
    "date_start",
    "date_end",
]
# Subsubsection example
# -----------------------------------------------------------------------

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


class NoteCollection(Collection):

    def __init__(self, name="MyNoteColl", alias="NtCol0"):

        super().__init__(base_object=Note, name=name, alias=alias)

    def load_list(self, files_list):

        for f in files_list:
            p = Path(f)
            name = p.stem
            n = self.baseobject(name=name, alias=name)
            n.file_note = p
            n.load()

            self.append(n)


class Note(MbaE):
    # todo [docstring]

    def __init__(self, name="MyNote", alias="Nt1"):
        # set attributes
        self.file_note = None
        self.metadata = None
        self.data = None
        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def _set_fields(self):
        super()._set_fields()
        # Attribute fields
        self.field_name_note = "note_name"
        self.field_alias_note = "note_alias"
        self.field_file_note = "note_file"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """
        This method returns all objects metadata, incluiding selected
        attributes beyond the metadata of the file
        """
        # set object metadata
        dc_main = {
            self.field_name_note: self.name,
            self.field_alias_note: self.alias,
            self.field_file_note: str(self.file_note),
        }

        # include file metadata
        if self.metadata is not None:
            dc_main.update(self.metadata)

        return dc_main

    def load_metadata(self):
        dc = Note.parse_metadata(self.file_note)

        # DATE
        # ---------------------
        for k in dc:
            if k in HARMONIZE_TEXT_FIELDS:
                dc[k] = Note.harmonize_entry_text(dc[k])

        # DATE
        # ---------------------
        for k in dc:
            if k in HARMONIZE_DATE_FIELDS:
                dc[k] = Note.harmonize_entry_date(dc[k], key=k)

        self.metadata = dc.copy()

    def load_data(self):
        self.data = Note.parse_note(self.file_note)

    def load(self):
        self.load_metadata()
        self.load_data()

    def save(self):
        self.to_file(file_path=self.file_note)

    def export(self, folder, filename, export_metadata=False):
        """
        Export to a markdown file with optional metadata handling.

        :param folder: The directory path where the file will be saved.
        :type folder: str
        :param filename: The name of the file without the extension.
        :type filename: str
        :param export_metadata: Toggle to trigger the parent class metadata export. Default value = ``False``
        :type export_metadata: bool
        :return: Path to the exported file
        :rtype: Path

        .. note::

            This method constructs a file path using ``pathlib.Path`` and appends the
            ``.md`` extension. It calls the internal ``to_file`` method with ``cleanup``
            enabled to finalize the document. If ``export_metadata`` is set to ``True``,
            it invokes the ``export`` method of the superclass before proceeding.

        """
        if export_metadata:
            super().export(folder=folder, filename=filename)
        fpath = Path(folder) / f"{filename}.md"
        self.to_file(fpath, cleanup=True)
        return fpath.absolute()

    def to_file(self, file_path, cleanup=True):
        """
        Write the note object's metadata and data content to a specified file.

        :param file_path: The destination path where the note will be written.
        :type file_path: str
        :param cleanup: Toggle to remove excessive blank lines after writing. Default value = ``True``
        :type cleanup: bool
        :return: None
        :rtype: NoneType

        .. note::

            This method aggregates metadata and data by calling ``metadata_to_list`` and
            ``data_to_list``. It sanitizes the output by replacing ``None`` string
            occurrences with empty strings and ensures each entry ends with a newline
            character. If ``cleanup`` is enabled, it post-processes the file using
            ``remove_excessive_blank_lines`` to maintain consistent formatting.

        """
        # metadata
        # ------------------------------------
        ls_metadata = Note.metadata_to_list(self.metadata)

        for i in range(len(ls_metadata)):
            # clear "None" values
            ls_metadata[i] = ls_metadata[i].replace("None", "")

        # data
        # ------------------------------------
        ls_data = Note.data_to_list(self.data)
        # append to metadata list
        for l in ls_data:
            ls_metadata.append(l[:])
        ls_all = [line + "\n" for line in ls_metadata]

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(ls_all)

        # clean up excessive lines
        if cleanup:
            Note.remove_excessive_blank_lines(file_path)

        return None

    @staticmethod
    def harmonize_entry_text(entry):
        if entry is not None:
            new_entry_bulk = entry[:]
            new_entry_bulk = new_entry_bulk.replace("'", "`")
            new_entry_bulk = new_entry_bulk.replace('"', "``")

            new_entry = '"' + new_entry_bulk + '"'
            s_start = new_entry[:2].replace("`", "")
            s_end = new_entry[-2:].replace("`", "")
            s_bulk = new_entry[2:-2]

            return s_start + s_bulk + s_end
        else:
            return None

    @staticmethod
    def harmonize_entry_date(entry, key="date"):
        if entry is None:
            return None

        if "datetime" in key or "timestamp" in key:
            format_mask = "%Y-%m-%d %H:%M:%S"
        else:
            format_mask = "%Y-%m-%d"

        dt = pd.to_datetime(entry, errors="coerce")

        if pd.isna(dt):
            return None

        return dt.strftime(format_mask)

    @staticmethod
    def harmonize_entry_date_old(entry, key="date"):
        if entry is not None:

            format_mask = "%Y-%m-%d"

            if "datetime" in key:
                format_mask = "%Y-%m-%d %H:%M:%S"
            if "timestamp" in key:
                format_mask = "%Y-%m-%d %H:%M:%S"

            # Convert string back into a Python object
            dt_object = pd.to_datetime([entry])

            # return string
            return str(dt_object.strftime(format_mask).values[0])
        else:
            return None

    @staticmethod
    def remove_excessive_blank_lines(file_path):
        """
        Remove consecutive blank lines from a file to ensure only single blank lines remain.

        :param file_path: The path to the target text file to be processed.
        :type file_path: str
        :return: None
        :rtype: NoneType

        .. note::

            This method performs an in-place modification of the file. It iterates through
            the content and suppresses any sequence of empty lines that exceeds a
            single occurrence, effectively "squeezing" the vertical whitespace.

        """
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        cleaned_lines = []
        previous_line_blank = False

        for line in lines:
            if line.strip() == "":
                if not previous_line_blank:
                    cleaned_lines.append(line)
                    previous_line_blank = True
            else:
                cleaned_lines.append(line)
                previous_line_blank = False

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(cleaned_lines)

    @staticmethod
    def parse_metadata(note_file):
        """
        Extracts YAML metadata from the header of a Markdown file.

        :param note_file: str, path to the Markdown file
        :return: dict, extracted YAML metadata
        """
        with open(note_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Regular expression to match the YAML header
        yaml_header_regex = r"^---\s*\n(.*?)\n---\s*\n"

        # Search for the YAML header in the content
        match = re.search(yaml_header_regex, content, re.DOTALL)

        if match:
            yaml_content = match.group(1)
            return Note.parse_yaml(yaml_content)
        else:
            return None

    @staticmethod
    def parse_yaml(yaml_content):
        """
        Parses YAML content into a dictionary.

        :param yaml_content: str, YAML content as string
        :return: dict,  parsed YAML content
        """
        metadata = {}
        lines = yaml_content.split("\n")
        current_key = None
        current_list = None

        for line in lines:
            if line.strip() == "":
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value == "":  # start of a list
                    current_key = key
                    current_list = []
                    metadata[current_key] = current_list
                else:
                    if key == "tags":
                        metadata[key] = [
                            v.strip() for v in value.split("-") if v.strip()
                        ]
                    else:
                        metadata[key] = value
            elif current_list is not None and line.strip().startswith("-"):
                current_list.append(line.strip()[1:].strip())

        # fix empty lists
        for e in metadata:
            if len(metadata[e]) == 0:
                metadata[e] = None

        # fix text fields
        for e in metadata:
            if metadata[e]:
                size = len(metadata[e]) - 1
                if metadata[e][0] == '"' and metadata[e][size] == '"':
                    # slice it
                    metadata[e] = metadata[e][1:size]

        return metadata

    @staticmethod
    def metadata_to_list(metadata_dict):
        """
        Convert a dictionary of metadata into a formatted list of strings.

        :param metadata_dict: A dictionary containing metadata keys and values to be formatted.
        :type metadata_dict: dict
        :return: A list of strings formatted with YAML-like syntax, enclosed by dashed separators.
        :rtype: list

        .. note::

            The method processes dictionary entries into a human-readable list format. It
            handles list values by creating indented bullet points and converts ``None``
            values into empty strings. The resulting list starts and ends with a ``---``
            delimiter string.

        """
        ls_metadata = []
        ls_metadata.append("---")
        for e in metadata_dict:
            if isinstance(metadata_dict[e], list):
                ls_metadata.append("{}:".format(e))
                for i in metadata_dict[e]:
                    ls_metadata.append(" - {}".format(i))
            else:
                aux0 = metadata_dict[e]
                if aux0 is None:
                    aux0 = ""
                aux1 = "{}: {}".format(e, aux0)
                ls_metadata.append(aux1)
        ls_metadata.append("---")

        return ls_metadata

    @staticmethod
    def data_to_list(data_dict):
        """
        Flatten a dictionary of lists into a single list separated by blank lines and delimiters.

        :param data_dict: A dictionary where each key maps to a list of strings to be aggregated.
        :type data_dict: dict
        :return: A concatenated list of all values with added structural spacing and separators.
        :rtype: list

        .. note::

            This function iterates through the top-level keys of ``data_dict`` and appends
            the contents of each list to a master list. After each group of data, it
            inserts an empty string, a ``---`` separator, and another empty string to
            visually distinguish different levels or sections.

        """
        ls_out = []
        for level in data_dict:
            ls_out = ls_out + data_dict[level][:]
            if level != "Tail":
                ls_out.append("")
                ls_out.append("---")
        return ls_out

    @staticmethod
    def parse_note(file_path):
        """
        Extract and categorize note content into head, body, and tail sections based on separators.

        :param file_path: The path to the note file to be parsed.
        :type file_path: str
        :return: A dictionary containing the cleaned lines for ``Head``, ``Body``, and ``Tail``.
        :rtype: dict

        .. note::

            The function first identifies and skips an initial YAML frontmatter block if it
            starts with ``---``. It then uses the ``---`` string as a delimiter to
            segment the remaining text. If multiple separators exist, the first and last
            act as boundaries for the ``Body``, while everything before the first is
            ``Head`` and everything after the last is ``Tail``. All extracted lines
            undergo a ``strip()`` operation to remove leading/trailing whitespace.


        """
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Skip YAML header if present
        if lines[0].strip() == "---":
            yaml_end_index = lines.index("---\n", 1) + 1
            lines = lines[yaml_end_index:]

        # Find all separator positions (lines with "---")
        separator_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]

        # Default values for Head, Body, and Tail
        head, body, tail = [], [], []

        if len(separator_indices) == 0:
            # No separators, the whole content is the Body
            body = lines
        elif len(separator_indices) == 1:
            # One separator: Head is before, Body is between, Tail is after
            head = lines[: separator_indices[0]]
            body = lines[separator_indices[0] + 1 :]
        elif len(separator_indices) == 2:
            # Two separators: Head, Body, and Tail
            head = lines[: separator_indices[0]]
            body = lines[separator_indices[0] + 1 : separator_indices[1]]
            tail = lines[separator_indices[1] + 1 :]
        else:
            # More than two separators: Head is before the first, Body is between the first and last, Tail is after the last
            head = lines[: separator_indices[0]]
            body = lines[separator_indices[0] + 1 : separator_indices[-1]]
            tail = lines[separator_indices[-1] + 1 :]

        # Clean up any extra newlines from the content
        head = [line.strip() for line in head]
        body = [line.strip() for line in body]
        tail = [line.strip() for line in tail]

        return {"Head": head, "Body": body, "Tail": tail}

    @staticmethod
    def list_by_pattern(md_dict, patt_type="tag"):
        """
        Retrieve a list of patterns from the note dictionary.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param patt_type: Type of pattern to search for, either "tag" or "related". Defaults to "tag".
        :type patt_type: str
        :return: List of found patterns or None if no patterns are found.
        :rtype: list or None
        """

        if patt_type == "tag":
            pattern = re.compile(r"#\w+")
        elif patt_type == "related":
            pattern = re.compile(r"\[\[.*?\]\]")
        else:
            pattern = re.compile(r"#\w+")

        patts = []
        # run over all sections
        for s in md_dict:
            content = md_dict[s]["Content"]
            for line in content:
                patts.extend(pattern.findall(line))

        if len(patts) == 0:
            patts = None

        return patts


class NoteBasic(Note):

    TEMPLATE_FILE = FOLDER_TEMPLATES_NOTES / "_basic.md"

    def __init__(self, name="MyNote", alias="Nt1"):
        super().__init__(name=name, alias=alias)
        self.file_note_template = self.get_template_file()
        self.metadata_standard = self.load_metadata_standard()
        self.data_standard = self.load_data_standard()

    @classmethod
    def get_template_file(cls):
        return Path(cls.TEMPLATE_FILE)

    def load_new(self, file_note):
        self.file_note = self.file_note_template
        self.load()
        self.file_note = Path(file_note)
        self.update()
        self.update_timestamp()

    def load_data_standard(self):
        dc = Note.parse_note(file_path=self.file_note_template)
        return dc

    def load_metadata_standard(self):
        dc = Note.parse_metadata(note_file=self.file_note_template)
        for k in dc:
            dc[k] = None
        return dc

    def load_metadata(self):
        super().load_metadata()
        # filter standard entries
        dc = {}
        for k in self.metadata_standard:
            # filter standard entry
            if k in self.metadata:
                dc[k] = self.metadata[k]
            # add standard entry
            else:
                dc[k] = None

        self.metadata = dc.copy()
        return None

    def update(self):
        self.update_name()
        self.update_abstract()

    def update_name(self):
        current_name = Path(self.file_note).stem
        self.metadata["name"] = current_name
        self.data["Head"][0] = f"# {current_name}"

    def update_abstract(self):
        if self.metadata["abstract"] is not None:
            current_abstract = self.metadata["abstract"][1:-1]
            n = 0
            for line in self.data["Head"]:
                n = n + 1
                if "[!Abstract]" in line:
                    break
            if n > 0:
                self.data["Head"][n] = f"> {current_abstract}\n"

    def update_timestamp(self):
        from datetime import datetime

        now = datetime.now()
        self.metadata["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")


class NoteProject(NoteBasic):

    TEMPLATE_FILE = FOLDER_TEMPLATES_NOTES / "_project.md"


class NoteFigure(NoteBasic):

    TEMPLATE_FILE = FOLDER_TEMPLATES_NOTES / "_figure.md"

    def load_new(self, file_note):
        super().load_new(file_note=file_note)
        self.metadata["subject"] = "'[[Scientific Illustration]]'"


# ... {develop}

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
