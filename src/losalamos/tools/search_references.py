# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Batch-extract bibliographic references from PDFs using a Gemini model.

This tool scans a folder of PDF files, builds a prompt from the first N pages,
and queries a generative model to produce BibTeX entries. Results are saved
as `.bib` files and the corresponding PDFs are renamed accordingly.

Usage
-----

Module execution (recommended):

Shell (bash/zsh):
```shell
python -m losalamos.tools.search_references \
    --file specs.json
```

PowerShell (ps1):
```shell
$SPEC="C:\\path\\to\\specs.json"

python -m losalamos.tools.search_references `
    --file $SPEC
```

Specification (JSON)
--------------------

The input file must define:
```json
{
    "folder": "/path/to/pdf_dir",
    "api": "YOUR_API_KEY",
    "model": "gemini-3-flash-preview",
    "pages": 2,
    "prompt": "path/to/prompt.txt or inline string"
}
```
Side effects
------------

- Creates `.bib` files alongside each PDF
- Renames PDFs based on the generated BibTeX key
- Skips files that already have a corresponding `.bib`

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
        fbib = pdf.parent / f"{nm}.bib"
        if fbib.is_file():
            print(get_message("File already searched (bib found)"))
        elif pdf.parent.name == "bkp":
            print(get_message("Backup folder detected"))
        else:

            heading_subsection(msg="Asking Gemini ...")
            sleep(1)

            # --------------------------------------------
            # Get pages
            pages = Ingester.parse_pdf_pages(file_parse=pdf, n_pages=n_pages)

            # --------------------------------------------
            # Built context
            filename = pdf.name
            context_data = f"\n\n>>>>> Context \nFile name: {filename}\n\nFirst {n_pages} pages content:\n\n\n{pages}"

            prompt = f"{prompt_head} {context_data}"
            print(filename)

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
