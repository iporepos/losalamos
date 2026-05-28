# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Handle Documents editing, managing and builds

"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import re
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
# import {module}
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
def escape_percent_latex(text: str) -> str:
    # Replace % not preceded by an odd number of backslashes
    return re.sub(r"(?<!\\)%", r"\%", text)


# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================
# ... {develop}


class DocumentTeX(DataSet):

    def __init__(self, name="MyDocTeX", alias="TeX"):

        super().__init__(name=name, alias=alias)

        self.is_main = True

    def load_data(self, file_data):
        """
        Loads data from a TeX file if it is the main document.

        :param file_data: path to the TeX file
        :type file_data: str
        :return: None
        :rtype: None
        """
        # overwrite relative path input
        # --------------------------------------------------
        self.file_data = Path(file_data).absolute()

        # Open and extract lines (assuming utf-8 encoding for standard TeX)
        with open(self.file_data, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # load all the text by a readlines method. self.data is a list.
        self.data = lines

        # check if it is a main tex file (not a part)
        # Using '\documentclass' as the standard marker for a main LaTeX file
        # --------------------------------------------------
        has_documentclass = any(r"\documentclass" in line for line in lines)

        if not has_documentclass:
            self.is_main = False
        else:
            self.is_main = True

        # update
        # --------------------------------------------------
        self.update()

        # ... continues in downstream objects ... #

        return None

    def to_pdf(self, file_output=None, cleanup=True, command="pdf"):
        """
        Compiles the TeX document into a PDF using latexmk.

        :param file_output: desired output path for the compiled PDF (optional)
        :type file_output: str
        :param cleanup: flag to remove auxiliary files after compilation
        :type cleanup: bool
        :param command: latexmk command flag (e.g., pdf, pdflua, pdfxe)
        :type command: str
        :return: None
        :rtype: None
        """
        if self.is_main:
            import subprocess
            import shutil
            from pathlib import Path

            # 1. Compile the document
            # --------------------------------------------------
            # Constructing command as a list: latexmk -{command} "{absolute path}"
            compile_cmd = ["latexmk", f"-{command}", str(self.file_data.absolute())]

            # Executing without try/except; check=True ensures a crash if latexmk fails
            subprocess.run(compile_cmd, check=True)

            # 2. Handle specific PDF output destination
            # --------------------------------------------------
            # latexmk defaults to creating the PDF next to the source .tex file
            default_pdf = self.file_data.with_suffix(".pdf")

            if file_output is not None:
                target_path = Path(file_output).absolute()

                # Copy the default PDF to the new destination, then delete the original
                shutil.copy2(default_pdf, target_path)
                default_pdf.unlink()

            # 3. Cleanup auxiliary files
            # --------------------------------------------------
            if cleanup:
                cleanup_cmd = ["latexmk", "-c", str(self.file_data)]
                subprocess.run(cleanup_cmd, check=True)

        return None

    def to_flat(self, file_output=None, compile_first=True, command="pdf"):
        """
        Flattens the TeX document by recursively resolving inputs and compiling to embed the bibliography.

        :param file_output: desired output path for the flattened TeX file
        :type file_output: str
        :param compile_first: flag to compile the document first to generate an updated .bbl file
        :type compile_first: bool
        :return: the fully flattened LaTeX document string
        :rtype: str
        """
        if self.is_main:
            import re
            import subprocess
            from pathlib import Path

            # 1. Compile to generate up-to-date .bbl
            # --------------------------------------------------
            if compile_first:
                self.to_pdf(file_output=None, command=command, cleanup=True)

            def _flatten_recursive(current_path):
                # Will crash if an inputted file path does not exist
                with open(current_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Flatten \input{} and \include{} commands
                pattern_input = re.compile(r"\\(?:input|include)\s*\{\s*([^}]+)\s*\}")

                def replace_input(match):
                    target_file = match.group(1).strip()
                    if not target_file.endswith(".tex"):
                        target_file += ".tex"

                    target_path = current_path.parent / target_file
                    return _flatten_recursive(target_path)

                content = pattern_input.sub(replace_input, content)

                # Embed references (.bbl)
                pattern_bib = re.compile(r"\\bibliography\s*\{\s*([^}]+)\s*\}")

                def replace_bib(match):
                    bbl_path = self.file_data.with_suffix(".bbl")

                    if bbl_path.exists():
                        with open(bbl_path, "r", encoding="utf-8") as bbl_file:
                            return bbl_file.read()

                    return match.group(0)

                content = pattern_bib.sub(replace_bib, content)

                return content

            # Start the recursive flattening
            flat_content = _flatten_recursive(self.file_data)

            # 2. Aggressive Cleanup
            # --------------------------------------------------
            if compile_first:
                # latexmk -c usually spares the .bbl and .pdf; we forcefully unlink them
                bbl_path = self.file_data.with_suffix(".bbl")
                pdf_path = self.file_data.with_suffix(".pdf")

                if bbl_path.exists():
                    bbl_path.unlink()
                if pdf_path.exists():
                    pdf_path.unlink()

            # 3. Export to file
            # --------------------------------------------------
            if file_output is not None:
                output_path = Path(file_output).absolute()
                with open(output_path, "w", encoding="utf-8") as f_out:
                    f_out.write(flat_content)

            return flat_content

        return None


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
