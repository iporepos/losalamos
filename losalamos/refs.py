"""
Classes for parsing, handling and managing references

Description:
    The ``refs`` module provides classes for parsing, handling and managing references

License:
    This software is released under the GNU General Public License v3.0 (GPL-3.0).
    For details, see: https://www.gnu.org/licenses/gpl-3.0.html

Author:
    Iporã Possantti

Contact:
    possantti@gmail.com


Overview
--------

todo
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis.
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Class aptent taciti sociosqu ad litora torquent per
conubia nostra, per inceptos himenaeos. Nulla facilisi. Mauris eget nisl
eu eros euismod sodales. Cras pulvinar tincidunt enim nec semper.


Examples
--------

todo
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Nulla mollis tincidunt erat eget iaculis.
Mauris gravida ex quam, in porttitor lacus lobortis vitae.
In a lacinia nisl. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas.

Class aptent taciti sociosqu ad litora torquent per
conubia nostra, per inceptos himenaeos. Nulla facilisi. Mauris eget nisl
eu eros euismod sodales. Cras pulvinar tincidunt enim nec semper.

"""

import os
import re
import shutil
from losalamos.root import MbaE, Collection


class Ref(MbaE):
    """
    The core reference object for managing documents and citations.

    **Examples:**

    Here's how to use the ``Ref`` class:

    Import Ref

    .. code-block:: python

        # Import Ref
        from losalamos.refs import Ref

    Parse Bib Files

    .. code-block:: python

        # Use built-in static method for parsing `bib` files:
        lst_bibs = Ref.parse_bibtex(file_note="./refs.bib")
        for bib_dict in lst_bibs:
            print("-------")
            # use method for standardize authors
            bib_dict["author"] = Ref.standard_author(bib_dict=bib_dict)

            # built-in static method for getting in-text citation
            c = Ref.cite_intext(
                bib_dict=bib_dict,
                text_format='md' # markup format
            )
            print(c)
            # built-in static method for getting full citations
            c = Ref.cite_full(
                bib_dict=bib_dict,
                style="apa", # APA format
                text_format='tex',  # markup format
                entry_type=bib_dict["entry_type"]
            )
            print(c)


    Instantiate a Reference

    .. code-block:: python

        # Instantiante a reference
        r = Ref(
            entry_type="book",
            title="The Origin of Species",
            author="Charles Darwin",
            year="1859",
            citation_key="darwin1859"
        )

    Set Reference by Incoming Dict

    .. code-block:: python

        # (Re)Set reference by incoming dict:
        r.set(
            dict_setter={
                "entry_type": "article",
                "title": "Views of Nature"
                "author": "Alexander von Humboldt",
                "year": "1794",
                "citation_key": "humboldt1793",
            }
        )

    Load Reference from BibTeX File

    .. code-block:: python

        # Load reference from `bib` file:
        # set order=0 for the first reference
        r.load_bib(file_note="./beven1989.bib", order=0)

    Search/Update bib info via CrossRef API

    .. code-block:: python

        r.bib_dict = Ref.search_info(
            bib_dict=r.bib_dict, # bib entry
            update=True, # default False
            fields=["doi", "journal", "url", "publisher"],  # Selected fields
            search_query="Beven 1989 changing ideas" # Default is the full-citation
        )

    """

    def __init__(
        self,
        entry_type="book",
        title="The Origin of Species",
        author="Darwin, C",
        year="1859",
        citation_key=None,
    ):
        """Initialize the `Ref` object

        :param entry_type: reference entry_type in BibTeX convetion (e.g., article, book, etc)
        :entry_type entry_type: str
        :param title: main title of the reference
        :entry_type title: str
        :param author: author(s) filename(s)
        :entry_type author: str
        :param year: year of publication
        :entry_type year: str
        :param citation_key: citation key of the reference
        :entry_type citation_key: str
        :param file_note: path to BibTeX file
        :entry_type file_note: str
        :param file_note: path to markdown note
        :entry_type file_note: str
        :param file_doc: path to pdf document
        :entry_type file_doc: str
        """
        # set basic attributes
        self.entry_type = entry_type
        self.citation_key = citation_key
        self.title = title
        self.author = author
        self.year = year
        # file paths
        self.file_bib = None
        self.file_note = None
        self.file_doc = None
        self.lib_folder = None
        # bib dict
        self.bib_dict = None
        # note class
        self.note = None

        self.note_comments = None
        self.note_tags = None
        self.note_related = None
        self.references_list = None

        # filename and alias setup
        _name = Ref.cite_intext(
            bib_dict={"author": self.author, "year": self.year}, text_format="plain"
        )
        if self.citation_key is not None:
            _alias = self.citation_key
        else:
            _alias = "MRef"

        super().__init__(name=_name, alias=_alias)
        # ... continues in downstream objects ... #

    def _set_fields(self):
        """Set fields names"""
        super()._set_fields()
        # Attribute fields
        self.citation_key_field = "citation_key"
        self.type_field = "entry_type"
        self.title_field = "title"
        self.author_field = "author"
        self.year_field = "year"
        self.file_bib_field = "file_bib"
        self.file_note_field = "file_note"
        self.file_doc_field = "file_doc"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """Get a dictionary with object metadata.
        Expected to increment superior methods.

        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.type_field: self.entry_type,
            self.citation_key_field: self.citation_key,
            self.title_field: self.title,
            self.author_field: self.author,
            self.year_field: self.year,
            self.file_bib_field: self.file_bib,
            self.file_note_field: self.file_note,
            self.file_doc_field: self.file_doc,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def set(self, dict_setter):
        """Set selected attributes based on an incoming dictionary

        :param dict_setter: incoming dictionary with attribute values
        :entry_type dict_setter: dict
        """
        # handle potentially missing fields
        list_dict_keys = list(dict_setter.keys())

        # this is because of a very weird bug in the parsing process
        dict_setter_stripped = {}
        for k in list_dict_keys:
            dict_setter_stripped[k] = dict_setter[k].strip()
        dict_setter = dict_setter_stripped.copy()

        # filename
        if self.name_field not in list_dict_keys:
            # set as citation in-text
            dict_setter[self.name_field] = Ref.cite_intext(
                bib_dict={
                    "author": dict_setter[self.author_field],
                    "year": dict_setter[self.year_field],
                },
                text_format="plain",
            )

        # alias
        if self.alias_field not in list_dict_keys:
            # set as citation key
            dict_setter[self.alias_field] = dict_setter[self.citation_key_field]
        # file_note
        if self.file_bib_field not in list_dict_keys:
            # set as none
            dict_setter[self.file_bib_field] = None
        # file_note
        if self.file_note_field not in list_dict_keys:
            # set as none
            dict_setter[self.file_note_field] = None
        # file_doc
        if self.file_doc_field not in list_dict_keys:
            # set as none
            dict_setter[self.file_doc_field] = None

        # ---------- set basic attributes --------- #
        super().set(dict_setter=dict_setter)
        self.entry_type = dict_setter[self.type_field]
        self.citation_key = dict_setter[self.citation_key_field]
        self.title = dict_setter[self.title_field]
        self.author = dict_setter[self.author_field]
        self.year = dict_setter[self.year_field]
        self.file_note = dict_setter[self.file_note_field]
        # ... continues in downstream objects ... #

    def load_bib(self, order=0, search_doi=True):
        """Load reference from ``bib`` file.

        :param order: order number in the ``bib`` file (first = 0)
        :entry_type order: int
        :return: None
        :rtype: None
        """
        list_refs = self.parse_bibtex(file_bib=self.file_bib)
        self.bib_dict = list_refs[order]
        self.set(dict_setter=list_refs[order])
        return None

    def load_note(self):
        """
        # todo docstring
        """
        self.note = Note(name=self.name, alias=self.alias)
        self.note.file_note = self.file_note
        self.note.load()

    def standardize(self):
        """Standardize citation key, author formatting

        :return: None
        :rtype: None
        """
        conflict_list = None
        if self.lib_folder:
            if os.path.isdir(self.lib_folder):
                conflict_list = Ref.get_citation_keys(lib_folder=self.lib_folder)

        # set standard author
        self.author = Ref.standard_author(bib_dict=self.bib_dict)
        self.bib_dict[self.author_field] = self.author

        # set standard citation key
        self.citation_key = Ref.standard_key(
            bib_dict=self.bib_dict, conflict_list=conflict_list
        )
        self.bib_dict[self.citation_key_field] = self.citation_key

        # Name and Alias
        self.name = Ref.cite_intext(bib_dict=self.bib_dict, text_format="plain")
        self.alias = self.citation_key

    def export(self, output_dir, create_note=True):
        """Export all files to a directory with the same name (citation key)

        :param output_dir: path to output directory
        :entry_type output_dir: str
        :return: None
        :rtype: None
        """
        # export all files with the citation key name
        export_name = self.citation_key

        # bib file
        self.to_bib(
            output_dir=output_dir,
            filename=export_name
        )

        # note file
        if create_note:
            self.to_note(
                output_dir=output_dir,
                filename=export_name,
                comments=self.note_comments,
                tags=self.note_tags,
                related=self.note_related,
                references=self.references_list
            )
        else:
            shutil.copy(
                src=os.path.abspath(self.file_note),
                dst=os.path.join(output_dir, export_name + ".md"),
            )

        # pdf file
        if self.file_doc:
            shutil.copy(
                src=os.path.abspath(self.file_doc),
                dst=os.path.join(output_dir, export_name + ".pdf"),
            )

        return None

    def save_bib(self, output_dir=None, filename=None):
        """Save bibliography to bib file (default to bib_file attribute).
        Ref is expected to hold the bib_dict

        :param output_dir: the directory where the ``bib`` file will be saved.
        :entry_type output_dir: str
        :param filename: the name of the .bib file (without extension).
        :entry_type filename: str
        :return: None
        :rtype: None
        """
        # handle output
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(self.file_bib))
        if filename is None:
            filename = os.path.splitext(
                os.path.basename(os.path.abspath(self.file_bib))
            )[0]
        # Export
        file_path = Ref.to_bib(
            bib_dict=self.bib_dict, output_dir=output_dir, filename=filename
        )
        self.file_bib = file_path
        return None

    def to_note(self, output_dir, filename, comments=None, tags=None, related=None, references=None):
        """
        # todo docstring
        """
        from datetime import datetime

        # Function to replace placeholders in a string using a dictionary
        # todo evaluate move to editor class
        def replace_placeholders(string, replacements):
            for placeholder, replacement in replacements.items():
                string = string.replace(placeholder, replacement)
            return string

        # Get the current timestamp
        now = datetime.now()
        # Format the timestamp
        timestamp_str = now.strftime("%Y-%m-%d %H:%M")

        # setup
        citation_in = Ref.cite_intext(bib_dict=self.bib_dict, text_format="plain")
        citation_in_md = Ref.cite_intext(bib_dict=self.bib_dict, text_format="md")
        citation_full_plain = Ref.cite_full(self.bib_dict, text_format="plain")
        title = f"**{self.bib_dict[self.title_field]}** by {citation_in}"

        # handle DOI
        doi_link = "{{doi}}"
        if "doi" in self.bib_dict:
            doi_link = self.bib_dict["doi"]

        # handle keywords
        keywords_str = "{{keywords}}"
        if "keywords" in self.bib_dict:
            keywords_str = self.bib_dict["keywords"]

        # Handle Abstract
        abstract_str = "{{abstract}}"
        if "abstract" in self.bib_dict:
            abstract_str = self.bib_dict["abstract"]

        # Note
        nt_dict = Note.get_template(kind="bib", head_name=citation_in_md)

        # handle comments
        if comments:
            nt_dict["Comments"]["Content"] = comments[:] + ["\n---"]
        # handle tags
        if tags is None:
            tags = ""
        if related is None:
            related = ""

        # handle references
        references_str = ""
        if references:
            lst_refs = [f" - {ref}" for ref in references]
            references_str = "\n".join(lst_refs)


        # edit contents
        replacements = {
            "{{LIBRARY ITEM}}": self.bib_dict[self.type_field].upper(),
            "{{Title}}": f"**{self.bib_dict[self.title_field]}** by {citation_in_md}",
            "{{tags}}": " ".join([tag for tag in tags]),
            "{{related}}": " ".join([rel for rel in related]),
            "{{timestamp}}": timestamp_str,
            "{{abstract}}": abstract_str,
            "{{doi}}": doi_link,
            "{{keywords}}": keywords_str,
            "{{In-text citation}}": citation_in,
            "{{Full citation}}": citation_full_plain,
            "{{BibTeX}}": Ref.bib_to_str(bib_dict=self.bib_dict),
            "{{references}}": references_str
        }

        for sec in nt_dict:
            template_strings = nt_dict[sec]["Content"][:]
            # Update the list of strings
            updated_strings = [
                replace_placeholders(string, replacements)
                for string in template_strings
            ]
            nt_dict[sec]["Content"] = updated_strings[:]

        # export note
        output_file = Note.to_md(
            md_dict=nt_dict, output_dir=output_dir, filename=filename
        )
        return output_file

    def to_bib(self, output_dir, filename):
        """
        # todo docstring
        """
        bibtex_content = f"@{self.bib_dict[self.type_field]}{{{self.bib_dict[self.citation_key_field]},\n"
        for key, value in self.bib_dict.items():
            if key not in [self.type_field, self.citation_key_field]:
                bibtex_content += f"  {key} = {{{value}}},\n"
        bibtex_content = bibtex_content.rstrip(",\n") + "\n}\n"
        # write file
        file_path = os.path.join(output_dir, f"{filename}.bib")
        with open(file_path, "w", encoding="utf-8") as bib_file:
            bib_file.write(bibtex_content)
        return file_path

    @staticmethod
    def get_citation_keys(lib_folder):
        """Get the list of citations key from a library folder.
        The folder is expected to hold references in bib files named by
        the respective citations keys.
        The "_" is considered a flag for bib files not related to the reference.

        :param lib_folder: path to library directory
        :type lib_folder: str
        :return: list of names of citation keys
        :rtype: list
        """
        # List to hold the filtered filenames
        filtered_files = []

        # Iterate through all files in the directory
        for filename in os.listdir(lib_folder):
            # Check if the file has a ".bib" extension and does not contain the "_" character
            if filename.endswith(".bib") and "_" not in filename:
                filtered_files.append(filename[:-4])

        return filtered_files

    @staticmethod
    def parse_bibtex(file_bib):
        """Parse a ``bib`` file and return a list of references as dictionaries.

        :param file_bib: Path to the ``bib`` file.
        :return: A list of dictionaries, each representing a BibTeX bib_dict.
        """
        entries = []
        entry = None
        key = None

        with open(file_bib, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                # Ignore empty lines and comments
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
                    entry["citation_key"] = citation_key.rstrip(",").strip()
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
    def cite_intext(bib_dict, text_format="plain", embed_link=False):
        """Format a dictionary of bibliometric parameters into an in-text citation string with optional DOI or URL links.

        :param bib_dict: dict
            A dictionary containing bibliometric parameters from a reference.
            Expected keys include 'author', 'year', 'doi', and 'url'.
        :param text_format: str
            The text format for styling (e.g., 'plain', 'html', 'md', 'tex').
        :param embed_link: bool
            Whether to embed a DOI or URL link in the citation (default is False).
        :return: str
            The formatted in-text citation string.
        """
        # Normalize authors first
        bib_dict["author"] = Ref.standard_author(bib_dict)

        author = bib_dict.get("author", "Unknown Author").strip()
        year = bib_dict.get("year", "n.d.").strip()
        doi = bib_dict.get("doi", "").strip()
        url = bib_dict.get("url", "").strip()

        # Split and prepare author names for in-text citation
        author_list = author.split(" and ")
        first_author_lastname = author_list[0].split(",")[0].strip()
        if len(author_list) > 2:
            formatted_authors = f"{first_author_lastname} et al."
        elif len(author_list) == 2:
            second_author_lastname = author_list[1].split(",")[0].strip()
            formatted_authors = f"{first_author_lastname} & {second_author_lastname}"
        else:
            formatted_authors = first_author_lastname

        # Apply text formatting
        def apply_format(text, text_format):
            # todo evaluate move this to an editor class
            formatted = text[:]
            if text_format == "plain":
                pass
            elif text_format == "html":
                formatted = text.replace("et al.", "<i>et al.</i>")
            elif text_format == "md":
                formatted = text.replace("et al.", "*et al.*")
            elif text_format == "tex":
                formatted = text.replace("et al.", r"\textit{et al.}")
                formatted = formatted.replace("&", r"\&")
            return formatted

        formatted_authors = apply_format(formatted_authors, text_format)

        # Embed link if applicable
        def embed_link_func(text, text_format, link):
            # todo evaluate move this to an editor class
            if text_format == "html":
                return f'<a href="{link}">{text}</a>'
            elif text_format == "md":
                return f"[{text}]({link})"
            elif text_format == "tex":
                return f"\\href{{{link}}}{{{text}}}"
            return text

        # Format the in-text citation
        in_text_citation = f"{formatted_authors} ({year})"

        if embed_link:
            if doi:
                link = f"https://doi.org/{doi}"
            else:
                link = url
            if link and text_format in ["html", "md", "tex"]:
                in_text_citation = embed_link_func(in_text_citation, text_format, link)

        return in_text_citation

    @staticmethod
    def cite_full(bib_dict, style="apa", text_format="plain", entry_type="article"):
        """Format a dictionary of bibliometric parameters into a specified citation text_format string and text format.

        :param bib_dict: dict
            A dictionary containing bibliometric parameters from a reference.
            Expected keys vary depending on the bib_dict entry_type.
        :param style: str
            The citation text_format to format (e.g., 'apa', 'mla', 'chicago', 'harvard', 'vancouver', 'abnt').
        :param text_format: str
            The text format for styling (e.g., 'plain', 'html', 'md', 'tex').
        :param entry_type: str
            The entry_type of the BibTeX bib_dict (e.g., 'article', 'book', 'inbook', 'incollection', 'proceedings', 'inproceedings', 'conference', 'phdthesis', 'mastersthesis', 'techreport', 'manual', 'unpublished', 'misc').
        :return: str
            The formatted citation string.
        """
        author = bib_dict.get("author", "Unknown Author").strip()
        year = bib_dict.get("year", "n.d.").strip()
        title = bib_dict.get("title", "Untitled").strip()
        journal = bib_dict.get("journal", "").strip()
        volume = bib_dict.get("volume", "").strip()
        issue = bib_dict.get("issue", "").strip()
        pages = bib_dict.get("pages", "").strip()
        doi = bib_dict.get("doi", "").strip()
        booktitle = bib_dict.get("booktitle", "").strip()
        publisher = bib_dict.get("publisher", "").strip()
        address = bib_dict.get("address", "").strip()
        school = bib_dict.get("school", "").strip()
        institution = bib_dict.get("institution", "").strip()
        note = bib_dict.get("note", "").strip()

        # Formatting authors for different styles
        author_list = author.split(" and ")
        formatted_authors = (
            ", ".join(author_list[:-1]) + ", and " + author_list[-1]
            if len(author_list) > 1
            else author_list[0]
        )

        # Apply text formatting
        def apply_format(text, format_type):
            if text_format == "plain":
                return text
            elif text_format == "html":
                if format_type == "title":
                    return f"<i>{text}</i>"
                elif format_type == "journal":
                    return f"<b>{text}</b>"
            elif text_format == "md":
                if format_type == "title":
                    return f"*{text}*"
                elif format_type == "journal":
                    return f"**{text}**"
            elif text_format == "tex":
                if format_type == "title":
                    return f"\\textit{{{text}}}"
                elif format_type == "journal":
                    return f"\\textbf{{{text}}}"
            return text

        title = apply_format(title, "title")
        journal = apply_format(journal, "journal")

        # Determine citation format based on bib_dict entry_type and text_format
        if entry_type == "article":
            volume_issue = f"{volume}({issue})" if issue else volume
            pages_str = f", {pages}" if pages else ""
            doi_str = f" https://doi.org/{doi}" if doi else ""
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}.{doi_str}"
            elif style == "mla":
                citation = f'{formatted_authors}. "{title}." {journal} {volume}.{issue} ({year}): {pages}. {doi_str}'
            elif style == "chicago":
                citation = f'{formatted_authors}. "{title}." {journal} {volume}, no. {issue} ({year}): {pages}.{doi_str}'
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) '{title}', {journal}, vol. {volume}, no. {issue}, pp. {pages}.{doi_str}"
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {journal}. {year};{volume}({issue}):{pages}.{doi_str}"
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {journal}, {volume}.({issue}), p. {pages}, {year}.{doi_str}"
            else:
                citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}.{doi_str}"
        elif entry_type == "book":
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. {publisher}."
            elif style == "mla":
                citation = f"{formatted_authors}. {title}. {publisher}, {year}."
            elif style == "chicago":
                citation = (
                    f"{formatted_authors}. {title}. {address}: {publisher}, {year}."
                )
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) {title}, {publisher}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {publisher}; {year}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {publisher}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. {publisher}."
        elif entry_type == "inbook" or entry_type == "incollection":
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
            elif style == "mla":
                citation = f'{formatted_authors}. "{title}." {booktitle}, edited by {editor}, {publisher}, {year}, pp. {pages}.'
            elif style == "chicago":
                citation = f'{formatted_authors}. "{title}." In {booktitle}, edited by {editor}, {pages}. {address}: {publisher}, {year}.'
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) '{title}', in {editor} (ed.), {booktitle}, {publisher}, pp. {pages}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. In: {editor}, editor. {booktitle}. {publisher}; {year}. p. {pages}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. In: {editor} (Ed.). {booktitle}. {publisher}, {year}. p. {pages}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
        elif (
            entry_type == "proceedings"
            or entry_type == "inproceedings"
            or entry_type == "conference"
        ):
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
            elif style == "mla":
                citation = f'{formatted_authors}. "{title}." {booktitle}, {publisher}, {year}, pp. {pages}.'
            elif style == "chicago":
                citation = f'{formatted_authors}. "{title}." In {booktitle}, edited by {editor}, {pages}. {address}: {publisher}, {year}.'
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) '{title}', in {editor} (ed.), {booktitle}, {publisher}, pp. {pages}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. In: {editor}, editor. {booktitle}. {publisher}; {year}. p. {pages}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. In: {editor} (Ed.). {booktitle}. {publisher}, {year}. p. {pages}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
        elif entry_type == "phdthesis" or entry_type == "mastersthesis":
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title} (Unpublished {entry_type.replace('thesis', 'thesis')}). {school}."
            elif style == "mla":
                citation = f"{formatted_authors}. {title}. {entry_type.replace('thesis', 'thesis')}, {school}, {year}."
            elif style == "chicago":
                citation = f"{formatted_authors}. {title}. {entry_type.replace('thesis', 'thesis')}, {school}, {year}."
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) {title}, {entry_type.replace('thesis', 'thesis')}, {school}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {entry_type.replace('thesis', 'thesis')}. {school}; {year}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {school}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title} (Unpublished {entry_type.replace('thesis', 'thesis')}). {school}."
        elif entry_type == "techreport":
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title} (Technical Report No. {number}). {institution}."
            elif style == "mla":
                citation = f"{formatted_authors}. {title}. {institution}, {year}."
            elif style == "chicago":
                citation = f"{formatted_authors}. {title}. {institution} Technical Report no. {number}, {year}."
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) {title}, {institution}, Technical Report no. {number}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {institution} Technical Report no. {number}; {year}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {institution}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title} (Technical Report No. {number}). {institution}."
        elif entry_type == "manual":
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. {organization}."
            elif style == "mla":
                citation = f"{formatted_authors}. {title}. {organization}, {year}."
            elif style == "chicago":
                citation = f"{formatted_authors}. {title}. {organization}, {year}."
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) {title}, {organization}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {organization}; {year}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {organization}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. {organization}."
        elif entry_type == "unpublished":
            if style == "apa":
                citation = (
                    f"{formatted_authors} ({year}). {title}. Unpublished manuscript."
                )
            elif style == "mla":
                citation = (
                    f"{formatted_authors}. {title}. Unpublished manuscript, {year}."
                )
            elif style == "chicago":
                citation = (
                    f"{formatted_authors}. {title}. Unpublished manuscript, {year}."
                )
            elif style == "harvard":
                citation = (
                    f"{formatted_authors} ({year}) {title}, Unpublished manuscript."
                )
            elif style == "vancouver":
                citation = (
                    f"{formatted_authors}. {title}. Unpublished manuscript; {year}."
                )
            elif style == "abnt":
                citation = (
                    f"{formatted_authors}. {title}. Unpublished manuscript, {year}."
                )
            else:
                citation = (
                    f"{formatted_authors} ({year}). {title}. Unpublished manuscript."
                )
        elif entry_type == "misc":
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. {note}."
            elif style == "mla":
                citation = f"{formatted_authors}. {title}. {note}, {year}."
            elif style == "chicago":
                citation = f"{formatted_authors}. {title}. {note}, {year}."
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) {title}, {note}."
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {note}; {year}."
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {note}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. {note}."
        else:
            citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}.{doi_str}"

        return citation

    @staticmethod
    def bib_to_str(bib_dict, entry_field="entry_type", citation_field="citation_key"):
        # todo docstring
        citation_key = bib_dict[citation_field]
        # list available fields
        bibtex_fields = [
            f"{key} = {{{value}}}"
            for key, value in bib_dict.items()
            if key not in [entry_field, citation_field]
        ]
        # build the string
        bibtex_str = (
            f"@{bib_dict[entry_field]}{{{citation_key},\n  "
            + ",\n  ".join(bibtex_fields)
            + "\n}}"
        )
        return bibtex_str

    @staticmethod
    def standard_author(bib_dict):
        """Get the standard author names in a BibTeX bib_dict dictionary to "Last, First" format if necessary.

        :param bib_dict: dict
            A dictionary containing bibliometric parameters from a reference.
            Expected key is 'author'.
        :return: str
            The string with normalized author names.
        """

        def normalize_author_name(author_name):
            if "," in author_name:
                return author_name.strip()
            else:
                parts = author_name.split()
                if len(parts) == 1:
                    return author_name.strip()  # single filename case (e.g., initials)
                elif len(parts) == 2:
                    return f"{parts[1]}, {parts[0]}"
                else:
                    return f"{parts[-1]}, {' '.join(parts[:-1])}"

        if "author" in bib_dict:
            author_list = [
                normalize_author_name(a.strip())
                for a in bib_dict["author"].split(" and ")
            ]

            standard_authors = " and ".join(author_list)

        return standard_authors

    @staticmethod
    def standard_key(bib_dict, conflict_list=None):
        """Get the standard Citation Key in a BibTeX bib_dict dictionary to LastnameFirstAuthor + Year + x (or a, b, c ...)

        :param bib_dict: dict
            A dictionary containing bibliometric parameters from a reference.
            Expected key is 'author', 'year' and 'title'.
        :return: str
            The string with normalized citation key.
        """

        def next_available_name(base_name, conflict_names):
            # Initialize the suffix as 'a'
            suffix = "a"

            # Generate the name with the current suffix and check for conflicts
            while base_name + suffix in conflict_names:
                # Move to the next letter in the alphabet
                suffix = chr(ord(suffix) + 1)

            # Return the first available name
            return base_name + suffix

        author = Ref.standard_author(bib_dict=bib_dict)
        first_author = author.split(" and ")[0].strip()
        first_name = first_author.split(",")[0].strip().capitalize()
        # by default set suffix as 'a'
        suf = "a"
        year = bib_dict["year"]
        standard_key = f"{first_name}{year}{suf}"

        # Check out for conflicting keys
        if conflict_list:
            standard_key = next_available_name(
                base_name=standard_key[:-1], conflict_names=conflict_list
            )
        return standard_key

    @staticmethod
    def query_xref(search_query):
        def format_unstruct(citation, known_doi=None):
            # first remove doi
            has_doi = False
            lst_uns = citation.split(",")
            lst_no_doi = []
            for e in lst_uns:
                if "https://doi.org/" in e:
                    has_doi = True
                    citation_doi = e[len('https://doi.org/'):]
                    pass
                else:
                    lst_no_doi.append(e)
            citation_no_doi = ", ".join(lst_no_doi)
            if has_doi:
                citation_no_doi = citation_no_doi + f" https://doi.org/{citation_doi}"
            elif known_doi:
                citation_no_doi = citation_no_doi + f" https://doi.org/{known_doi}"
            return citation_no_doi
        def extract_bibtex_entry(data):
            #print(data.keys())
            #print(data["published"])
            bibtex_entry = {
                "entry_type": data.get("type", "article"),  # Default to "article" if not specified
                "author": " and ".join([f"{author['family']}, {author['given']}" for author in data.get("author", [])]),
                "title": data.get("title", [None])[0],
                "journal": data.get("container-title", [None])[0],
                "year": data.get("published", {}).get("date-parts", [[None]])[0][0],
                "volume": data.get("volume"),
                "number": data.get("issue"),
                "pages": data.get("page"),
                "doi": data.get("DOI"),
                "url": data.get("URL"),
                "publisher": data.get("publisher"),
                "note": data.get("note"),
                "abstract": data.get("abstract"),
                "keywords": data.get("subject", [])
            }
            # Remove None values
            #print(bibtex_entry["year"])
            bibtex_entry = {k: v for k, v in bibtex_entry.items() if v is not None}

            # set citation key and author
            bibtex_entry["author"] = Ref.standard_author(bibtex_entry)
            bibtex_entry["citation_key"] = Ref.standard_key(bibtex_entry)

            return bibtex_entry

        # Generic tool for cross ref API
        import requests
        # CrossRef API search URL
        search_url = f'https://api.crossref.org/works?query.bibliographic="{search_query}"&rows=2'
        output_data = None
        response = requests.get(search_url)

        if response.status_code == 200:
            data = response.json().get("message", {})
            # handle main bibtex:
            main_bib = extract_bibtex_entry(data=data["items"][0])
            # handle references
            lst_references = []
            for i in range(len(data["items"][0]["reference"])):
                citation = data["items"][0]["reference"][i]["unstructured"]
                if "DOI" in data["items"][0]["reference"][i]:
                    known_doi = data["items"][0]["reference"][i]["DOI"]
                else:
                    known_doi = None
                citation_formatted = format_unstruct(citation, known_doi=known_doi)
                lst_references.append(citation_formatted)
            lst_references.sort()
            output_data = {
                "Main": main_bib,
                "References": lst_references
            }
        return output_data



class Note(MbaE):

    def __init__(self, name="MyNote", alias="Nt1"):

        # attributes
        self.title = None
        self.tags_head = None
        self.tags_etc = None
        self.related_head = None
        self.related_etc = None
        self.summary = None
        self.timestamp = None

        # file paths
        self.file_note = None
        # note dict
        self.note_dict = None

        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def _set_fields(self):
        """Set fields names"""
        super()._set_fields()
        # Attribute fields
        self.title_field = "title"
        self.tags_head_field = "tags_head"
        self.tags_etc_field = "tags_etc"
        self.related_head_field = "related_head"
        self.related_etc_field = "related_etc"
        self.summary_field = "summary"
        self.timestamp_field = "timestamp"
        self.file_note_field = "file_note"

        # Metadata fields

        # ... continues in downstream objects ... #

    def get_metadata(self):
        """Get a dictionary with object metadata.
        Expected to increment superior methods.

        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        # ------------ call super ----------- #
        dict_meta = super().get_metadata()

        # customize local metadata:
        dict_meta_local = {
            self.title_field: self.title,
            self.summary_field: self.summary,
            self.timestamp_field: self.timestamp,
            self.tags_head_field: self.tags_head,
            self.tags_etc_field: self.tags_etc,
            self.related_head_field: self.related_head,
            self.related_etc_field: self.related_etc,
            self.file_note_field: self.file_note,
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def load(self):
        self.note_dict = Note.parse_note(file_path=self.file_note)
        self.update()

    def update(self):

        # get first section name
        # Warning: assume it is the first item
        self.title = next(iter(self.note_dict))

        # patterns

        # Create a copy of the original dictionary
        new_dict = self.note_dict.copy()
        # Remove the specified key from the new dictionary
        del new_dict[self.title]

        # head tags
        self.tags_head = Note.list_by_pattern(
            md_dict={self.title: self.note_dict[self.title]}, patt_type="tag"
        )
        # head related:
        self.related_head = Note.list_by_pattern(
            md_dict={self.title: self.note_dict[self.title]}, patt_type="related"
        )
        # etc tags:
        self.tags_etc = Note.list_by_pattern(md_dict=new_dict, patt_type="tag")

        self.related_etc = Note.list_by_pattern(md_dict=new_dict, patt_type="related")

        # summary
        lst_summaries = Note.list_by_intro(
            md_dict={self.title: self.note_dict[self.title]}, intro_type="summary"
        )
        self.summary = lst_summaries[0]

        # datetime
        lst_datetimes = Note.list_by_intro(
            md_dict={self.title: self.note_dict[self.title]}, intro_type="timestamp"
        )
        self.timestamp = lst_datetimes[0]

    @staticmethod
    def list_by_pattern(md_dict, patt_type="tag"):
        """Retrieve a list of patterns from the note dictionary.

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

    @staticmethod
    def list_by_intro(md_dict, intro_type="summary"):
        """List introduction contents based on the specified type.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param intro_type: Type of introduction to search for, currently supports "summary". Defaults to "summary".
        :type intro_type: str
        :return: List of found introductions or None if no introductions are found.
        :rtype: list or None
        """
        if intro_type == "summary":
            pattern = r"\*\*Summary:\*\*\s*(.*)"
        elif intro_type == "timestamp":
            pattern = r"created in:\s*(.*)"
        # develop more options

        summaries = []
        # run over all sections
        for s in md_dict:
            content = md_dict[s]["Content"]
            for line in content:
                match = re.search(pattern, line)
                if match:
                    summaries.append(match.group(1))
        if len(summaries) == 0:
            summaries = None
        return summaries

    @staticmethod
    def parse_note(file_path):
        """Parse a Markdown file into a dictionary structure.

        :param file_path: Path to the Markdown file.
        :type file_path: str
        :return: Dictionary representing the note structure.
        :rtype: dict
        """

        with open(file_path, "r") as file:
            lines = file.readlines()

        markdown_dict = {}
        current_section = None
        parent_section = None
        section_stack = []

        section_pattern = re.compile(r"^(#+)\s+(.*)")

        for line in lines:
            match = section_pattern.match(line)
            if match:
                level = len(match.group(1))
                section_title = match.group(2).strip()

                if current_section is not None:
                    markdown_dict[current_section]["Content"] = section_content

                while section_stack and section_stack[-1][1] >= level:
                    section_stack.pop()

                parent_section = section_stack[-1][0] if section_stack else None
                current_section = section_title
                section_stack.append((current_section, level))
                markdown_dict[current_section] = {
                    "Parent Section": parent_section,
                    "Content": [],
                }
                section_content = []
            else:
                section_content.append(line.strip())

        if current_section is not None:
            markdown_dict[current_section]["Content"] = section_content

        return markdown_dict

    @staticmethod
    def to_md(md_dict, output_dir, filename):
        """Convert a note dictionary to a Markdown file and save it to the specified directory.

        :param md_dict: Dictionary containing note sections.
        :type md_dict: dict
        :param output_dir: Directory where the output Markdown file will be saved.
        :type output_dir: str
        :param filename: Name of the output Markdown file (without extension).
        :type filename: str
        :return: None
        :rtype: None
        """

        def write_section(file, section, level=1):
            # Write the section header
            file.write(f"{'#' * level} {section}\n")

            # Write the section content
            for line in md_dict[section]["Content"]:
                file.write(line + "\n")

            # Find and write subsections
            subsections = [
                key for key in md_dict if md_dict[key]["Parent Section"] == section
            ]
            for subsection in subsections:
                write_section(file, subsection, level + 1)

        # Find top-level sections (sections with no parent)
        top_sections = [
            key for key in md_dict if md_dict[key]["Parent Section"] is None
        ]

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = os.path.join(output_dir, f"{filename}.md")

        with open(output_file, "w", encoding="utf-8") as file:
            for section in top_sections:
                write_section(file, section)
        return output_file

    @staticmethod
    def get_template(kind="bib", head_name=None):
        # todo continue here
        if head_name is None:
            head_name = "Header"
        templates = {
            "bib": {
                head_name: {
                    "Parent Section": None,
                    "Content": [
                        "{{LIBRARY ITEM}}\n",
                        "{{Title}}\n",
                        "**Summary:** Insert a paragraph comment here\n",
                        "tags: {{tags}}",
                        "related: {{related}}",
                        "created in: {{timestamp}}",
                        "\n---",
                    ],
                },
                "Comments": {
                    "Parent Section": None,
                    "Content": [
                        "*Start typing here*\n\n",
                        "\n---",
                    ],
                },
                "Bibliographic information": {
                    "Parent Section": None,
                    "Content": [
                        "## Abstract",
                        "**Author abstract:** {{abstract}}\n",
                        "**AI-based abstract:** {{ai_abstract}}",
                        "\n## Metadata",
                        "doi: {{doi}}",
                        "keywords: {{keywords}}",
                        "\n## Citation",
                        "In-text citation:",
                        "```",
                        "{{In-text citation}}",
                        "```",
                        "Full citation:",
                        "```",
                        "{{Full citation}}",
                        "```",
                        "BibTeX entry:",
                        "```",
                        "{{BibTeX}}",
                        "```",
                        "\n## References",
                        "{{references}}"
                    ],
                },
            }
        }

        return templates[kind]


class RefColl(Collection):  # todo docstring

    def __init__(self, name="MyRefCollection", alias="myRefCol"):  # todo docstring
        super().__init__(base_object=Ref, name=name, alias=alias)

    def load(self, file_path):  # todo docstring
        list_refs = Ref.parse_bibtex(file_path)
        for i in range(len(list_refs)):
            bib_dict = list_refs[i]
            rf = Ref(
                entry_type=bib_dict["entry_type"],
                title=bib_dict["title"],
                author=bib_dict["author"],
                year=bib_dict["year"],
                citation_key=bib_dict["citation_key"],
            )
            rf.bib_dict = bib_dict.copy()
            self.append(new_object=rf)
