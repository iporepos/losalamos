# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Batch-extract bibliographic references from PDFs using a Gemini model.

This tool scans a folder of PDF files, builds a prompt from the first N pages,
and queries a generative model to produce BibTeX entries. Results are saved
as ``.bib`` files and the corresponding PDFs are renamed accordingly.

Usage
-----

Module execution (recommended):

Shell (bash/zsh):

.. code-block:: shell

    python -m losalamos.tools.search_references \
        --file specs.json

PowerShell (ps1):

.. code-block:: powershell

    $SPEC="C:\\path\\to\\specs.json"

    python -m losalamos.tools.search_references `
        --file $SPEC

Specification (JSON)
--------------------

The input file must define:

.. code-block:: json

    {
        "folder": "/path/to/pdf_dir",
        "api": "YOUR_API_KEY",
        "model": "gemini-3-flash-preview",
        "pages": 2,
        "prompt": "path/to/prompt.txt or inline string"
    }

Side effects
------------

- Creates ``.bib`` files alongside each PDF
- Renames PDFs based on the generated BibTeX key
- Skips files that already have a corresponding ``.bib``

"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import argparse, json
import os
import pprint
from pathlib import Path
from time import sleep
import time

# External imports
# =======================================================================
from google import genai
from google.genai.errors import ServerError

# Project-level imports
# =======================================================================
from losalamos.tools.core import *
from losalamos.ingestion import Ingester

# CONSTANTS
# ***********************************************************************
# define constants in uppercase


# FUNCTIONS
# ***********************************************************************
def get_auxiliary_context(pdf_path: Path) -> str:
    """
    Look for auxiliary ``.txt`` and ``.ris`` files alongside the PDF.

    Reads the contents of any matching auxiliary files (sharing the same stem
    as the PDF) and returns them as a formatted string to be injected into
    the LLM prompt context.

    :param pdf_path: The file path to the target PDF document.
    :type pdf_path: pathlib.Path
    :return: A formatted string containing the text from the auxiliary files,
             or an empty string if no such files exist.
    :rtype: str
    """
    aux_text = ""

    # Define the extensions to look for
    aux_extensions = [".txt", ".ris", ".md"]

    for ext in aux_extensions:
        aux_file = pdf_path.with_suffix(ext)
        if aux_file.is_file():
            try:
                with open(aux_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        aux_text += (
                            f"\n--- Metadata from {aux_file.name} ---\n{content}\n"
                        )
            except Exception as e:
                print(f"Warning: Could not read {aux_file.name}: {e}")

    return aux_text


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="search json file.")
    # keep adding if more templates arise
    args = parser.parse_args()

    return args


def next_available_path(base_path: Path) -> Path:
    """
    Return a non-colliding path by appending alphabetical suffixes.

    Example:
        file.pdf   -> file_a.pdf -> file_b.pdf -> ... -> file_aa.pdf
    """
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    def index_to_suffix(i: int) -> str:
        # 0 -> a, 1 -> b, ..., 25 -> z, 26 -> aa, ...
        s = ""
        i += 1
        while i > 0:
            i -= 1
            s = chr(97 + (i % 26)) + s
            i //= 26
        return s

    i = 0
    while True:
        candidate = parent / f"{stem}_{index_to_suffix(i)}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def ask_gemini(prompt, model, client, max_retries=5, base_delay=2):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text

        except ServerError as e:
            if "503" in str(e):
                delay = base_delay * (2**attempt)
                print(
                    get_warning(
                        f"503 UNAVAILABLE. Retry {attempt+1}/{max_retries} in {delay}s"
                    )
                )
                time.sleep(delay)
            else:
                raise  # non-retryable server error

    print(get_warning("Max retries reached. Skipping."))
    return None


def main() -> None:
    heading_section("SEARCH REFERENCES")

    args = get_arguments()
    specs_file = args.file

    with open(specs_file) as f:
        specs = json.load(f)

    folder = Path(specs["folder"])

    print(get_message(f"Folder: {folder}"))

    if not folder.is_dir():
        print(get_warning(msg="Folder not found"))
        return None

    # Initialize the client
    client = genai.Client(api_key=specs["api"])

    n_pages = specs["pages"]
    prompt_head = specs["prompt"]
    model = specs["model"]

    if Path(prompt_head).is_file():
        with open(prompt_head) as f:
            head = f.read()
        prompt_head = head

    ls_pdfs = list(folder.rglob("*.pdf"))

    for pdf in ls_pdfs:

        nm = pdf.stem
        heading_subsection(msg=f"File search: {nm}.pdf")

        fbib = pdf.parent / f"{nm}.bib"
        if fbib.is_file():
            print(get_message("File already searched (bib found)"))
        elif pdf.parent.name == "bkp":
            print(get_message("Backup folder detected"))
        else:

            print("Asking Gemini ...")
            sleep(1)

            # --------------------------------------------
            # Get pages
            pages = Ingester.parse_pdf_pages(file_parse=pdf, n_pages=n_pages)

            # --------------------------------------------
            # Get auxiliary context
            aux_context = get_auxiliary_context(pdf)

            # --------------------------------------------
            # Build context
            filename = pdf.name

            # Start building the context block
            context_data = f"\n\n>>>>> Context \nFile name: {filename}\n"

            # Inject auxiliary data if it exists
            if aux_context:
                context_data += f"\n>>>>> Auxiliary File Data:{aux_context}\n"

            # Append the PDF pages
            context_data += f"\n>>>>> First {n_pages} pages content:\n\n{pages}"

            prompt = f"{prompt_head} {context_data}"

            # --------------------------------------------
            # Ask

            answer = ask_gemini(prompt=prompt, model=model, client=client)

            answer = answer.replace("```bibtex\n", "")
            answer = answer.replace("```", "")

            print(answer)

            if answer is not None:
                heading_subsection(msg="Saving ...")
                # --------------------------------------------
                # get name
                fnm = answer.split("\n")[0].split("{")[1].split(",")[0]

                # Base paths
                bib_base = pdf.parent / f"{fnm}.bib"
                pdf_base = pdf.parent / f"{fnm}.pdf"

                # Resolve collisions
                bib_path = next_available_path(bib_base)
                pdf_path = next_available_path(pdf_base)

                # Save Bib
                with open(bib_path, "w", encoding="utf-8") as f:
                    f.write(answer)

                # Rename PDF
                os.rename(src=pdf, dst=pdf_path)
            else:
                print(get_warning("Answer None"))

    heading_done()


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    main()
    # ... {develop}
