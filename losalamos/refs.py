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

    def __init__(self, entry_type="book", title="The Origin of Species", author="Darwin, C", year="1859", citation_key=None, file_bib=None, file_note=None, file_doc=None):
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
        self.file_bib = file_bib
        self.file_note = file_note
        self.file_doc = file_doc
        # bib dict
        self.bib_dict = None

        # filename and alias setup
        _name = Ref.cite_intext(
            bib_dict={
                "author": self.author,
                "year": self.year
            },
            text_format="plain"
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
            self.file_doc_field: self.file_doc
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
                "year": dict_setter[self.year_field]
            },
            text_format="plain"
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

    def load_bib(self, file_bib=None, order=0):
        """Load reference from ``bib`` file.

        :param file_bib: file path to ``bib`` file
        :entry_type file_bib: str
        :param order: order number in the ``bib`` file (first = 0)
        :entry_type order: int
        :return: None
        :rtype: None
        """
        if file_bib is None:
            file_bib = self.file_bib # use local
        list_refs = self.parse_bibtex(file_bib=file_bib)
        self.bib_dict = list_refs[order]
        self.file_bib = file_bib
        self.set(dict_setter=list_refs[order])
        return None

    def load_note(self, file_note=None, order=0):
        """Load notes from ``md`` file.

        :param file_note: file path to ``bib`` file
        :entry_type file_note: str
        :param order: order number in the ``bib`` file (first = 0)
        :entry_type order: int
        :return: None
        :rtype: None
        """
        if file_note is None:
            file_note = self.file_note # use local
        # todo loading note method
        return None

    def standardize(self):
        """Standardize citation key, author formatting

        :return: None
        :rtype: None
        """
        # set standard author
        self.author = Ref.standard_author(bib_dict=self.bib_dict)
        self.bib_dict[self.author_field] = self.author

        # set standard citation key
        self.citation_key = Ref.standard_key(bib_dict=self.bib_dict)
        self.bib_dict[self.citation_key_field] = self.citation_key

        # Name and Alias
        self.name = Ref.cite_intext(
            bib_dict=self.bib_dict,
            text_format="plain"
        )
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
        Ref.export_bibtex(
            bib_dict=self.bib_dict,
            output_dir=output_dir,
            filename=export_name
        )

        # note file
        if create_note:
            self.create_note(output_dir=output_dir)
        else:
            if self.file_note:
                # todo save note changes function
                shutil.copy(
                    src=os.path.abspath(self.file_note),
                    dst=os.path.join(output_dir, export_name + ".md")
                )

        # pdf file
        if self.file_doc:
            shutil.copy(
                src=os.path.abspath(self.file_doc),
                dst=os.path.join(output_dir, export_name + ".pdf")
            )

        return None

    def create_note(self, output_dir):
        """Creates a markdown file for a BibTeX entry with a custom title, 
        comments section, and bibliometric information.

        :param output_dir: Directory where the markdown file will be saved.
        """
        bib_dict = self.bib_dict
        citation_in = Ref.cite_intext(bib_dict=self.bib_dict)
        title = f"{self.bib_dict[self.title_field]} --  by {citation_in}"
        comments = "Start here"
        # Extract citation key and create filename
        citation_key = self.bib_dict[self.citation_key_field]
        filename = f"{citation_key}.md"
        filepath = os.path.join(output_dir, filename)

        # Create the bibliometric information section
        bibtex_fields = [f"{key} = {{{value}}}" for key, value in bib_dict.items() if
                         key not in [self.type_field, self.citation_key_field]]
        bibtex_code = f"@{bib_dict[self.type_field]}{{{citation_key},\n  " + ",\n  ".join(bibtex_fields) + "\n}}"

        citation_full_plain = Ref.cite_full(self.bib_dict, text_format="plain")
        citation_full_md = Ref.cite_full(self.bib_dict, text_format="md")
        # Create the markdown content
        markdown_content = (
            f"# {title}\n\n"
            f"\n{self.entry_type.upper()}\n"
            f"\n{citation_full_md}\n"
            f"\n## Comments"
            f"\n\n{comments}\n"
            f"\n## Bibliometric information\n"
            f"\nBibTeX entry:\n```\n{bibtex_code}\n```"
        )

        # Write the content to the markdown file
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(markdown_content)

        self.file_note = filepath

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
            filename = os.path.splitext(os.path.basename(os.path.abspath(self.file_bib)))[0]
        # Export
        file_path = Ref.export_bibtex(
            bib_dict=self.bib_dict,
            output_dir=output_dir,
            filename=filename
        )
        self.file_bib = file_path
        return None

    @staticmethod
    def export_bibtex(bib_dict, output_dir, filename):
        """Export a BibTeX entry to a ``bib`` file.

        :param bib_dict: dict containing the BibTeX entry. Must include keys "entry_type" and "citation_key".
        :entry_type bib_dict: dict
        :param output_dir: the directory where the ``bib`` file will be saved.
        :entry_type output_dir: str
        :param filename: the name of the .bib file (without extension).
        :entry_type filename: str
        :return: exported file path
        :rtype: str
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        bibtex_content = f"@{bib_dict['entry_type']}{{{bib_dict['citation_key']},\n"
        for key, value in bib_dict.items():
            if key not in ["entry_type", "citation_key"]:
                bibtex_content += f"  {key} = {{{value}}},\n"
        bibtex_content = bibtex_content.rstrip(",\n") + "\n}\n"

        file_path = os.path.join(output_dir, f"{filename}.bib")
        with open(file_path, "w", encoding="utf-8") as bib_file:
            bib_file.write(bibtex_content)
        return file_path

    @staticmethod
    def parse_bibtex(file_bib):
        """Parse a ``bib`` file and return a list of references as dictionaries.

        :param file_bib: Path to the ``bib`` file.
        :return: A list of dictionaries, each representing a BibTeX bib_dict.
        """
        entries = []
        entry = None
        key = None

        with open(file_bib, 'r', encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                # Ignore empty lines and comments
                if not line or line.startswith('%'):
                    continue

                # New bib_dict starts
                if line.startswith('@'):
                    if entry is not None:
                        entries.append(entry)
                    entry = {}
                    # Extracting the entry_type and citation key
                    entry_type, citation_key = line.lstrip('@').split('{', 1)
                    entry['entry_type'] = entry_type
                    entry['citation_key'] = citation_key.rstrip(',').strip()
                elif '=' in line and entry is not None:
                    # Extracting the field key and value
                    key, value = line.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip().strip('{').strip(',').strip('}')
                    entry[key] = value
                elif entry is not None and key:
                    # Continuation of a field value in a new line
                    entry[key] += ' ' + line.strip().strip('{').strip('}').strip(',')

        # Add the last bib_dict if it exists
        if entry is not None:
            # ensure values are stripped:
            entry_new = {}
            for k in entry:
                entry_new[k] = entry[k].strip()
            entries.append(entry_new)

        stripped_data = [
            {key: value.strip() for key, value in item.items()}
            for item in entries
        ]

        return stripped_data

    @staticmethod
    def parse_note(file_note=None, bibsec="Bibliographic information"):
        """Parse a structured Markdown `md` file into a dictionary.

        The `md` file is expected to have the bibliometric section as follows:

        .. code-block:: text

                # <bibsec>

                tags: #tag1 #tag2

                BibTeX:
                ```
                bibtex citation
                ```


        :param file_note: path to `md` note
        :entry_type file_note: str
        :param bibsec: title of bibliographic section
        :entry_type bibsec: str
        :return:
        :rtype:
        """
        if file_note is None:
            # use internal attribute
            file_note = self.file_note


        # todo method
        return None

    @staticmethod
    def cite_intext(bib_dict, text_format='plain', embed_link=False):
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

        author = bib_dict.get('author', 'Unknown Author').strip()
        year = bib_dict.get('year', 'n.d.').strip()
        doi = bib_dict.get('doi', '').strip()
        url = bib_dict.get('url', '').strip()

        # Split and prepare author names for in-text citation
        author_list = author.split(' and ')
        first_author_lastname = author_list[0].split(",")[0].strip()
        if len(author_list) > 1:
            formatted_authors = f"{first_author_lastname} et al."
        else:
            formatted_authors = first_author_lastname

        # Apply text formatting
        def apply_format(text, text_format):
            if text_format == 'plain':
                return text
            elif text_format == 'html':
                return f"<i>{text}</i>"
            elif text_format == 'md':
                return f"*{text}*"
            elif text_format == 'tex':
                return f"\\textit{{{text}}}"
            return text

        formatted_authors = apply_format(formatted_authors, text_format)

        # Embed link if applicable
        def embed_link_func(text, text_format, link):
            if text_format == 'html':
                return f'<a href="{link}">{text}</a>'
            elif text_format == 'md':
                return f'[{text}]({link})'
            elif text_format == 'tex':
                return f'\\href{{{link}}}{{{text}}}'
            return text

        # Format the in-text citation
        in_text_citation = f"{formatted_authors} ({year})"

        if embed_link:
            if doi:
                link = f"https://doi.org/{doi}"
            else:
                link = url
            if link and text_format in ['html', 'md', 'tex']:
                in_text_citation = embed_link_func(in_text_citation, text_format, link)

        return in_text_citation

    @staticmethod
    def cite_full(bib_dict, style='apa', text_format='plain', entry_type='article'):
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
        author = bib_dict.get('author', 'Unknown Author').strip()
        year = bib_dict.get('year', 'n.d.').strip()
        title = bib_dict.get('title', 'Untitled').strip()
        journal = bib_dict.get('journal', '').strip()
        volume = bib_dict.get('volume', '').strip()
        issue = bib_dict.get('issue', '').strip()
        pages = bib_dict.get('pages', '').strip()
        doi = bib_dict.get('doi', '').strip()
        booktitle = bib_dict.get('booktitle', '').strip()
        publisher = bib_dict.get('publisher', '').strip()
        address = bib_dict.get('address', '').strip()
        school = bib_dict.get('school', '').strip()
        institution = bib_dict.get('institution', '').strip()
        note = bib_dict.get('note', '').strip()

        # Formatting authors for different styles
        author_list = author.split(' and ')
        formatted_authors = ', '.join(author_list[:-1]) + ', and ' + author_list[-1] if len(author_list) > 1 else \
        author_list[0]

        # Apply text formatting
        def apply_format(text, format_type):
            if text_format == 'plain':
                return text
            elif text_format == 'html':
                if format_type == 'title':
                    return f"<i>{text}</i>"
                elif format_type == 'journal':
                    return f"<b>{text}</b>"
            elif text_format == 'md':
                if format_type == 'title':
                    return f"*{text}*"
                elif format_type == 'journal':
                    return f"**{text}**"
            elif text_format == 'tex':
                if format_type == 'title':
                    return f"\\textit{{{text}}}"
                elif format_type == 'journal':
                    return f"\\textbf{{{text}}}"
            return text

        title = apply_format(title, 'title')
        journal = apply_format(journal, 'journal')

        # Determine citation format based on bib_dict entry_type and text_format
        if entry_type == 'article':
            volume_issue = f"{volume}({issue})" if issue else volume
            pages_str = f", {pages}" if pages else ""
            doi_str = f" https://doi.org/{doi}" if doi else ""
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}.{doi_str}"
            elif style == 'mla':
                citation = f"{formatted_authors}. \"{title}.\" {journal} {volume}.{issue} ({year}): {pages}. {doi_str}"
            elif style == 'chicago':
                citation = f"{formatted_authors}. \"{title}.\" {journal} {volume}, no. {issue} ({year}): {pages}.{doi_str}"
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) '{title}', {journal}, vol. {volume}, no. {issue}, pp. {pages}.{doi_str}"
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. {journal}. {year};{volume}({issue}):{pages}.{doi_str}"
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. {journal}, {volume}.({issue}), p. {pages}, {year}.{doi_str}"
            else:
                citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}.{doi_str}"
        elif entry_type == 'book':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. {publisher}."
            elif style == 'mla':
                citation = f"{formatted_authors}. {title}. {publisher}, {year}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. {title}. {address}: {publisher}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) {title}, {publisher}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. {publisher}; {year}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. {publisher}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. {publisher}."
        elif entry_type == 'inbook' or entry_type == 'incollection':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
            elif style == 'mla':
                citation = f"{formatted_authors}. \"{title}.\" {booktitle}, edited by {editor}, {publisher}, {year}, pp. {pages}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. \"{title}.\" In {booktitle}, edited by {editor}, {pages}. {address}: {publisher}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) '{title}', in {editor} (ed.), {booktitle}, {publisher}, pp. {pages}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. In: {editor}, editor. {booktitle}. {publisher}; {year}. p. {pages}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. In: {editor} (Ed.). {booktitle}. {publisher}, {year}. p. {pages}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
        elif entry_type == 'proceedings' or entry_type == 'inproceedings' or entry_type == 'conference':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
            elif style == 'mla':
                citation = f"{formatted_authors}. \"{title}.\" {booktitle}, {publisher}, {year}, pp. {pages}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. \"{title}.\" In {booktitle}, edited by {editor}, {pages}. {address}: {publisher}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) '{title}', in {editor} (ed.), {booktitle}, {publisher}, pp. {pages}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. In: {editor}, editor. {booktitle}. {publisher}; {year}. p. {pages}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. In: {editor} (Ed.). {booktitle}. {publisher}, {year}. p. {pages}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. In {editor} (Ed.), {booktitle} (pp. {pages}). {publisher}."
        elif entry_type == 'phdthesis' or entry_type == 'mastersthesis':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title} (Unpublished {entry_type.replace('thesis', 'thesis')}). {school}."
            elif style == 'mla':
                citation = f"{formatted_authors}. {title}. {entry_type.replace('thesis', 'thesis')}, {school}, {year}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. {title}. {entry_type.replace('thesis', 'thesis')}, {school}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) {title}, {entry_type.replace('thesis', 'thesis')}, {school}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. {entry_type.replace('thesis', 'thesis')}. {school}; {year}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. {school}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title} (Unpublished {entry_type.replace('thesis', 'thesis')}). {school}."
        elif entry_type == 'techreport':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title} (Technical Report No. {number}). {institution}."
            elif style == 'mla':
                citation = f"{formatted_authors}. {title}. {institution}, {year}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. {title}. {institution} Technical Report no. {number}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) {title}, {institution}, Technical Report no. {number}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. {institution} Technical Report no. {number}; {year}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. {institution}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title} (Technical Report No. {number}). {institution}."
        elif entry_type == 'manual':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. {organization}."
            elif style == 'mla':
                citation = f"{formatted_authors}. {title}. {organization}, {year}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. {title}. {organization}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) {title}, {organization}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. {organization}; {year}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. {organization}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. {organization}."
        elif entry_type == 'unpublished':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. Unpublished manuscript."
            elif style == 'mla':
                citation = f"{formatted_authors}. {title}. Unpublished manuscript, {year}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. {title}. Unpublished manuscript, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) {title}, Unpublished manuscript."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. Unpublished manuscript; {year}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. Unpublished manuscript, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. Unpublished manuscript."
        elif entry_type == 'misc':
            if style == 'apa':
                citation = f"{formatted_authors} ({year}). {title}. {note}."
            elif style == 'mla':
                citation = f"{formatted_authors}. {title}. {note}, {year}."
            elif style == 'chicago':
                citation = f"{formatted_authors}. {title}. {note}, {year}."
            elif style == 'harvard':
                citation = f"{formatted_authors} ({year}) {title}, {note}."
            elif style == 'vancouver':
                citation = f"{formatted_authors}. {title}. {note}; {year}."
            elif style == 'abnt':
                citation = f"{formatted_authors}. {title}. {note}, {year}."
            else:
                citation = f"{formatted_authors} ({year}). {title}. {note}."
        else:
            citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}.{doi_str}"

        return citation

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
            if ',' in author_name:
                return author_name.strip()
            else:
                parts = author_name.split()
                if len(parts) == 1:
                    return author_name.strip()  # single filename case (e.g., initials)
                elif len(parts) == 2:
                    return f"{parts[1]}, {parts[0]}"
                else:
                    return f"{parts[-1]}, {' '.join(parts[:-1])}"

        if 'author' in bib_dict:
            author_list = [normalize_author_name(a.strip()) for a in bib_dict['author'].split(' and ')]
            standard_authors = ' and '.join(author_list)

        return standard_authors

    @staticmethod
    def standard_key(bib_dict):
        """Get the standard Citation Key in a BibTeX bib_dict dictionary to LastnameFirstAuthor + Year + x (or a, b, c ...)

        :param bib_dict: dict
            A dictionary containing bibliometric parameters from a reference.
            Expected key is 'author', 'year' and 'title'.
        :return: str
            The string with normalized citation key.
        """
        author = Ref.standard_author(bib_dict=bib_dict)
        first_author = author.split(" and ")[0].strip()
        first_name = first_author.split(",")[0].strip().capitalize()
        # by default set suffix as x
        suf = 'x'
        year = bib_dict["year"]
        standard_key = f"{first_name}{year}{suf}"
        return standard_key

    @staticmethod
    def search_info(bib_dict, update=False, fields=None, search_query=None):
        """Update or enrich a BibTeX entry based on a search in the CrossRef API.

        :param bib_dict: A dictionary containing bibliometric parameters from a reference.
        :type bib_dict: dict
        :param update: if True, update all attributes; if False, only fill in missing attributes
        :type update: bool
        :param fields: specific fields to update; if None, operate on all fields
        :type fields: list
        :return: updated BibTeX entry
        :rtype: dict
        """
        import requests

        if search_query is None:
            search_query = bib_dict["title"]

        # CrossRef API search URL
        search_url = f'https://api.crossref.org/works?query.bibliographic="{search_query}"&rows=2'

        response = requests.get(search_url)
        if response.status_code == 200:
            data = response.json().get("message", {})
            normalized_data = {k.lower(): v for k, v in data["items"][0].items()}
            # Fields mapping from CrossRef response to BibTeX fields
            crossref_fields = {
                "title": normalized_data.get("title", [""])[0],
                "author": " and ".join([f"{author.get('family', '')}, {author.get('given', '')}" for author in
                                     normalized_data.get("author", [])]),
                "year": normalized_data.get("issued", {}).get("date-parts", [[None]])[0][0],
                "journal": normalized_data.get("container-title", [""])[0],
                "volume": normalized_data.get("volume", ""),
                "issue": normalized_data.get("issue", ""),
                "pages": normalized_data.get("page", ""),
                "doi": normalized_data.get("doi", ""),
                "url": normalized_data.get("url", ""),
            }
            # Handle the abstract field separately as it might not be present
            if "abstract" in normalized_data:
                crossref_fields["abstract"] = normalized_data["abstract"]

            # Iterate over keys in dict_b
            for key in crossref_fields:
                # If the key is not in dict_a, add it with an empty string as the value
                if key not in bib_dict:
                    bib_dict[key] = ""

            # Update only specified fields if fields is provided
            keys_to_update = fields if fields else bib_dict.keys()

            for key in keys_to_update:
                if key in ["citation_key", "entry_type"]:
                    continue
                if update or not bib_dict.get(key):
                    bib_dict[key] = crossref_fields.get(key, bib_dict.get(key))

        else:
            print(f"Failed to fetch data for citation key {search_query}. Status code: {response.status_code}")

        # Cleanup
        bib_dict = {key: value.strip() for key, value in bib_dict.items() if value != ""}
        return bib_dict


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
                citation_key=bib_dict["citation_key"]
            )
            rf.bib_dict = bib_dict.copy()
            self.append(new_object=rf)


