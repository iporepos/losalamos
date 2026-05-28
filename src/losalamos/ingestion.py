# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Automated ingestion utilities for bibliographic files.

This module provides tools for processing incoming collections of PDF and
BibTeX files and converting them into standardized reference notes. The
ingestion pipeline detects PDF–BibTeX pairs, extracts and normalizes metadata,
generates unique filenames, creates Markdown reference notes, and copies the
associated PDFs into a managed library structure.

Quick start
===========

The ingestion system converts incoming PDF and BibTeX files into standardized
reference notes and library assets.

Run the ingestion pipeline

.. code-block:: python

    from losalamos.ingestion import Ingester

    ing = Ingester(
        src="path/to/incoming/article",
        dst="path/to/library/papers"
    )

    ing.run()

This command will:

- explode multi-entry ``.bib`` files if needed
- pair PDF files with their corresponding BibTeX metadata
- generate standardized filenames
- create Markdown reference notes
- copy PDFs into the destination library

"""
import os
import shutil

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
from tqdm import tqdm

# ... {develop}

# Project-level imports
# =======================================================================
from losalamos.references import Reference


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


class Ingester:

    def __init__(self, src, dst):
        self.src_folder = Path(src)
        self.dst_folder = Path(dst)

    def run(self, cleanup=True):
        """
        Executes the processing pipeline to convert incoming PDF and BibTeX files into standardized note references.

        .. note::

             This method orchestrates the full ingestiong workflow: it explodes multi-entry BibTeX files, identifies
             pairs of PDF and ``.bib`` files, and generates unique filenames. For each valid pair, it
             instantiates a ``NoteReference``, populates it with standardized metadata (including
             subject tagging), saves the resulting Markdown file, and copies the PDF to the destination
             library. If ``cleanup`` is enabled, the original source files are deleted after successful
             processing.

        :param cleanup: Determines whether to delete the source BibTeX and PDF files after processing. Default value = ``True``
        :type cleanup: bool
        :return: No value is returned.
        :rtype: None
        """
        from losalamos.notes import NoteReference

        # Explode bib files
        # ------------------------------------------------
        self.explode_bib_files()

        # Get available files
        # ------------------------------------------------
        ref = self.get_reference_object()
        df = self.get_incoming_files()

        records = df.to_dict(orient="records")

        for row_dict in tqdm(records, desc="Ingesting refs", unit="file"):

            file_pdf = row_dict["file"]
            subject = row_dict["subject"]

            # get data from BIB file
            file_bib = Path(file_pdf).parent / f"{Path(file_pdf).stem}.bib"

            if file_bib.is_file():
                # create reference
                ref.load_data(file_data=file_bib)
                name = ref.define_file_name(
                    library_folder=self.dst_folder, extension="md"
                )

                # create the note
                note = NoteReference()
                file_note = self.dst_folder / f"{name}.md"
                note.load_new(file_note=file_note, metadata=ref.data)

                # include subject
                note.metadata["subject"] = f'"[[{subject}]]"'
                note.save()

                # copy the PDF
                file_pdf_new = self.dst_folder / f"{name}.pdf"
                shutil.copy(src=file_pdf, dst=file_pdf_new)

                # cleanup
                if cleanup:
                    os.remove(file_bib)
                    os.remove(file_pdf)

        # todo develop
        #  include a system for querying data from CrossRef
        #  evaluate an enrichment system

        return None

    def explode_bib_files(self):
        """
        Splits multi-entry BibTeX files into individual ``.bib`` files named after each reference.

        :return: No value is returned.
        :rtype: None
        """
        ls = self.list_bibs()

        for f in ls:
            print(f)
            p = Path(f)
            ls_bibs = Reference.parse_bib(file_parse=f)
            # explode file into subfiles
            if len(ls_bibs) > 1:
                for b in ls_bibs:
                    ref = Reference.get_by_entry(entry_type=b["entry_type"])
                    ref.setup_data(data=b)
                    name = ref.data["name"]
                    fo = p.parent / f"{name}.bib"
                    ref.to_bib(output=fo)
                os.remove(p)
        return None

    def get_incoming_files(self):
        """
        Retrieves a DataFrame mapping all PDF files in the source folder to their respective subjects.

        :return: A DataFrame with columns ``file`` and ``subject``.
        :rtype: :class:`pandas.DataFrame`
        """
        ls_pdfs = self.list_pdfs()
        ls_subs = self.list_subjects(list_paths=ls_pdfs)
        df = pd.DataFrame({"file": ls_pdfs, "subject": ls_subs})

        return df

    def get_reference_object(self):
        """
        Identifies the entry type from the source folder name and returns the corresponding reference class instance.

        :return: An instance of the reference class associated with the folder's name.
        :rtype: :class:`Reference`
        """
        entry = Path(self.src_folder).stem
        return Reference.get_by_entry(entry_type=entry)

    def list_files(self, extension="*"):
        """
        Lists all files within the source directory and subdirectories that match a specific extension.

        :param extension: The file extension to filter by. Default value = ``*``
        :type extension: str
        :return: A list of paths to the discovered files.
        :rtype: list[:class:`pathlib.Path`]
        """
        root = Path(self.src_folder)
        return [p for p in root.rglob(f"*.{extension}") if p.is_file()]

    def list_bibs(self):
        """
        Recursively lists all BibTeX (``.bib``) files found within the source directory.

        :return: A list of paths to the discovered BibTeX files.
        :rtype: list[:class:`pathlib.Path`]
        """
        return self.list_files(extension="bib")

    def list_pdfs(self):
        """
        Recursively lists all PDF files found within the source directory.

        :return: A list of paths to the discovered PDF files.
        :rtype: list[:class:`pathlib.Path`]
        """
        return self.list_files(extension="pdf")

    def list_subjects(self, list_paths):
        """
        Extracts the parent directory names for a list of file paths to serve as subject labels.

        :param list_paths: A list of file paths to analyze for subject extraction.
        :type list_paths: list[:class:`pathlib.Path`]
        :return: A list of strings containing the stem of each file's parent directory.
        :rtype: list[str]
        """
        root_name = Path(self.src_folder).stem
        ls = []
        for p in list_paths:
            subject = Path(p).parent.stem
            if subject == root_name:
                subject = ""
            ls.append(subject[:])
        return ls

    @staticmethod
    def parse_pdf_metadata(file_parse):
        """
        Extracts standard metadata fields from a PDF file using the ``pymupdf`` library.

        :param file_parse: The path to the PDF file to be processed.
        :type file_parse: str | :class:`pathlib.Path`
        :return: A dictionary containing extracted metadata such as DOI, title, author, and dates.
        :rtype: dict
        """
        import pymupdf

        pdf_path = Path(file_parse)

        metadata = {
            "doi": None,
            "url": None,
            "title": None,
            "author": None,
            "subject": None,
            "keywords": None,
            "creator": None,
            "producer": None,
            "creation_date": None,
            "modification_date": None,
            "source": "pdf_metadata",
        }

        try:
            with pymupdf.open(pdf_path) as doc:
                info = doc.metadata
                metadata["doi"] = info.get("doi")
                metadata["url"] = info.get("url")
                metadata["title"] = info.get("title")
                metadata["author"] = info.get("author")
                metadata["subject"] = info.get("subject")
                metadata["keywords"] = info.get("keywords")
                metadata["creator"] = info.get("creator")
                metadata["producer"] = info.get("producer")
                metadata["creation_date"] = info.get("creationDate")
                metadata["modification_date"] = info.get("modDate")

        except Exception as e:
            metadata["error"] = str(e)

        return metadata

    @staticmethod
    def parse_pdf_pages(file_parse: str, n_pages: int = 3) -> str:
        """
        Reads and concatenates text content from the first few pages of a PDF document.

        :param file_parse: The path to the PDF file to be read.
        :type file_parse: str
        :param n_pages: The maximum number of initial pages to extract text from. Default value = ``3``
        :type n_pages: int
        :return: A single string containing the combined text of the extracted pages.
        :rtype: str
        """
        import pymupdf

        file_parse = Path(file_parse)
        text_chunks = []

        with pymupdf.open(file_parse) as doc:
            pages_to_read = min(n_pages, doc.page_count)

            for i in range(pages_to_read):
                page = doc.load_page(i)
                text_chunks.append(page.get_text())

        return "\n".join(text_chunks)

    @staticmethod
    def parse_bib(file_parse):
        """
        Parses a BibTeX file and returns the metadata of the first entry found.

        :param file_parse: The path to the BibTeX file to be parsed.
        :type file_parse: str | :class:`pathlib.Path`
        :return: A dictionary representing the first bibliographic entry in the file.
        :rtype: dict
        """
        ls = Reference.parse_bib(file_parse=file_parse)
        dc = ls[0]  # always the first item
        return dc


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    from tests.conftest import DATA_DIR, OUTPUT_DIR

    print("Hello World!")

    inp = DATA_DIR / "incoming/article"
    out = OUTPUT_DIR / "library/papers"

    ingester = Ingester(src=inp, dst=out)
    ingester.run()
