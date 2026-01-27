# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import re

# ... {develop}

# External imports
# =======================================================================
# import {module}
# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.root import MbaE

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
        self.field_file_note = "file_note"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.field_file_note: self.file_note,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def load_metadata(self):
        self.metadata = Note.parse_metadata(self.file_note)

    def load_data(self):
        self.data = Note.parse_note(self.file_note)

    def load(self):
        self.load_metadata()
        self.load_data()

    def save(self):
        self.to_file(file_path=self.file_note)

    def to_file(self, file_path, cleanup=True):
        """
        Export Note to markdown

        :param file_path: path to file
        :type file_path: str
        :return:
        :rtype:
        """
        ls_metadata = Note.metadata_to_list(self.metadata)
        # clear "None" values
        for i in range(len(ls_metadata)):
            ls_metadata[i] = ls_metadata[i].replace("None", "")

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

    @staticmethod
    def remove_excessive_blank_lines(file_path):
        # todo docstring
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
        # todo docstring
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
        # todo docstring
        ls_out = []
        for level in data_dict:
            ls_out = ls_out + data_dict[level][:]
            ls_out.append("")
            ls_out.append("---")
            ls_out.append("")
        return ls_out

    @staticmethod
    def parse_note(file_path):
        # todo docstring
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
