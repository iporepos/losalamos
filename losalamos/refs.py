"""
Classes for parsing, handling and managing references


"""
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
        lst_bibs = Ref.parse_bibtex(file_bib="./refs.bib")
        for entry in lst_bibs:
            print("-------")
            # use method for standardize authors
            entry["author"] = Ref.standardize_authors(bib_dict=entry)

            # built-in static method for getting in-text citation
            c = Ref.cite_intext(
                bib_dict=entry,
                text_format='md' # markup format
            )
            print(c)
            # built-in static method for getting full citations
            c = Ref.cite_full(
                bib_dict=entry,
                style="apa", # APA format
                text_format='tex',  # markup format
                entry_type=k["type"]
            )
            print(c)


    Instantiate a Reference

    .. code-block:: python

        # Instantiante a reference
        r = Ref(
            type="book",
            title="The Origin of Species",
            author="Charles Darwin",
            year="1859",
            citation_key="darwin1859"
        )
        print(r)

    Set Reference by Incoming Dict

    .. code-block:: python

        # (Re)Set reference by incoming dict:
        r.set(
            dict_setter={
                "type": "article",
                "title": "Views of Nature"
                "author": "Alexander von Humboldt",
                "year": "1794",
                "citation_key": "humboldt1793",
            }
        )
        print(r)

    Load Reference from Bib File

    .. code-block:: python

        # Load reference from `bib` file:
        # set order=0 for the first reference
        r.load(file_bib="./beven1989.bib", order=0)
        print(r)



    """

    def __init__(self, type, title, author, year, citation_key=None, file_note=None, file_doc=None):
        """Initialize the `Ref` object

        :param type: reference type in BibTeX convetion (e.g., article, book, etc)
        :type type: str
        :param title: main title of the reference
        :type title: str
        :param author: author(s) name(s)
        :type author: str
        :param year: year of publication
        :type year: str
        :param citation_key: citation key of the reference
        :type citation_key: str
        :param file_note: path to markdown note
        :type file_note: str
        :param file_doc: path to pdf document
        :type file_doc: str
        """
        # set basic attributes
        self.type = type
        self.citation_key = citation_key
        self.title = title
        self.author = author
        self.year = year
        self.file_note = file_note
        self.file_doc = file_doc

        # name and alias setup
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
        self.type_field = "type"
        self.title_field = "title"
        self.author_field = "author"
        self.year_field = "year"
        self.note_field = "file_note"
        self.file_field = "file_doc"

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
            self.type_field: self.type,
            self.citation_key_field: self.citation_key,
            self.title_field: self.title,
            self.author_field: self.author,
            self.year_field: self.year,
            self.note_field: self.file_note,
            self.file_field: self.file_doc
        }
        # update
        dict_meta.update(dict_meta_local)
        return dict_meta

    def set(self, dict_setter):
        """Set selected attributes based on an incoming dictionary

        :param dict_setter: incoming dictionary with attribute values
        :type dict_setter: dict
        """
        # handle potentially missing fields
        list_dict_keys = list(dict_setter.keys())

        # this is because of a very weird bug in the parsing process
        dict_setter_stripped = {}
        for k in list_dict_keys:
            dict_setter_stripped[k] = dict_setter[k].strip()
        dict_setter = dict_setter_stripped.copy()

        # name
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
        if self.note_field not in list_dict_keys:
            # set as none
            dict_setter[self.note_field] = None
        # file_doc
        if self.file_field not in list_dict_keys:
            # set as none
            dict_setter[self.file_field] = None

        # ---------- set basic attributes --------- #
        super().set(dict_setter=dict_setter)
        self.type = dict_setter[self.type_field]
        self.citation_key = dict_setter[self.citation_key_field]
        self.title = dict_setter[self.title_field]
        self.author = dict_setter[self.author_field]
        self.year = dict_setter[self.year_field]
        self.file_note = dict_setter[self.note_field]
        # ... continues in downstream objects ... #

    def load(self, file_bib, order=0):
        """Load reference from ``bib`` file.

        :param file_bib: file path to ``bib`` file
        :type file_bib: str
        :param order: order number in the ``bib`` file (first = 0)
        :type order: int
        :return: None
        :rtype: None
        """
        list_refs = self.parse_bibtex(file_bib=file_bib)
        self.set(dict_setter=list_refs[order])
        return None

    @staticmethod
    def parse_bibtex(file_bib):
        """Parse a ``bib`` file and return a list of references as dictionaries.

        :param file_bib: Path to the ``bib`` file.
        :return: A list of dictionaries, each representing a BibTeX entry.
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

                # New entry starts
                if line.startswith('@'):
                    if entry is not None:
                        entries.append(entry)
                    entry = {}
                    # Extracting the type and citation key
                    entry_type, citation_key = line.lstrip('@').split('{', 1)
                    entry['type'] = entry_type
                    entry['citation_key'] = citation_key.rstrip(',').strip()
                elif '=' in line and entry is not None:
                    # Extracting the field key and value
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('{').strip(',').strip('}')
                    entry[key] = value
                elif entry is not None and key:
                    # Continuation of a field value in a new line
                    entry[key] += ' ' + line.strip().strip('{').strip('}').strip(',')

        # Add the last entry if it exists
        if entry is not None:
            # ensure values are stripped:
            entry_new = {}
            for k in entry:
                entry_new[k] = entry[k].strip()
            entries.append(entry_new)

        return entries

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
        :type file_note: str
        :param bibsec: title of bibliographic section
        :type bibsec: str
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
        bib_dict["author"] = Ref.standardize_authors(bib_dict)

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
            Expected keys vary depending on the entry type.
        :param style: str
            The citation text_format to format (e.g., 'apa', 'mla', 'chicago', 'harvard', 'vancouver', 'abnt').
        :param text_format: str
            The text format for styling (e.g., 'plain', 'html', 'md', 'tex').
        :param entry_type: str
            The type of the BibTeX entry (e.g., 'article', 'book', 'inbook', 'incollection', 'proceedings', 'inproceedings', 'conference', 'phdthesis', 'mastersthesis', 'techreport', 'manual', 'unpublished', 'misc').
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

        # Determine citation format based on entry type and text_format
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
    def standardize_authors(bib_dict):
        """Normalize the author names in a BibTeX entry dictionary to "Last, First" format if necessary.

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
                    return author_name.strip()  # single name case (e.g., initials)
                elif len(parts) == 2:
                    return f"{parts[1]}, {parts[0]}"
                else:
                    return f"{parts[-1]}, {' '.join(parts[:-1])}"

        if 'author' in bib_dict:
            author_list = [normalize_author_name(a.strip()) for a in bib_dict['author'].split(' and ')]
            standard_authors = ' and '.join(author_list)

        return standard_authors



class RefCollection(Collection):  # todo docstring

    def __init__(self, name="MyRefCollection", alias="myRefCol"):  # todo docstring
        super().__init__(base_object=Ref, name=name, alias=alias)

    def load(self, file_path):  # todo docstring
        list_refs = Ref.parse_bibtex(file_path)
        for i in range(len(list_refs)):
            rf = Ref()
            rf.load(file_bib=f, order=i)
            self.append(new_object=rf)



if __name__ == "__main__":
    print("Hi")

