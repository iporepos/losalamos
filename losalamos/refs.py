"""
Classes for parsing, handling and managing references


"""
from losalamos.root import MbaE, Collection


class Ref(MbaE):

    def __init__(self, type=None, citation_key=None, title=None, author=None, year=None, note=None, file=None):
        # set basic attributes
        self.type = type
        self.citation_key = citation_key
        self.title = title
        self.author = author
        self.year = year
        self.note = note
        self.file = file

        # name and alias setup
        if self.author is not None and self.year is not None:
            _name = self.cite_intext()
        else:
            _name = "MyReference"
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
        self.note_field = "note"
        self.file_field = "file"

        # Metadata fields

        # ... continues in downstream objects ... #

    @staticmethod
    def parse_bibfile(file_path):
        """
        Parse a .bib file and return a list of references as dictionaries.

        :param file_path: Path to the .bib file.
        :return: A list of dictionaries, each representing a BibTeX entry.
        """
        entries = []
        entry = None
        key = None

        with open(file_path, 'r', encoding="utf-8") as file:
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
    def parse_note(note):
        """
        Parse a structured note into a dictionary.

        :param note: A string containing the structured note.
        :return: A dictionary with the parsed key-value pairs.
        """
        note_dict = {}
        # Removing leading and trailing braces and splitting by semicolon
        entries = note.strip('{}').split(';')

        for entry in entries:
            # Splitting each entry into key and value
            parts = entry.split('=', 1)
            if len(parts) == 2:
                key, value = parts
                # Cleaning up key and value
                key = key.strip().strip("<br/>").replace('\\', '')
                value = value.strip().replace('\\', '').strip('{}')
                note_dict[key] = value

        return note_dict

    @staticmethod
    def cite_intext(authors=None, year=None):
        """Format a string of authors for in-text citation.
        """
        if authors is None:
            authors = self.author
        author_list = [author.strip() for author in authors.split('and')]
        num_authors = len(author_list)

        if year is None:
            year = self.year
        str_year = " ({})".format(year)

        if num_authors == 1:
            # Return the surname of the single author
            return author_list[0].split()[-1] + str_year
        elif num_authors == 2:
            # Return "Surname A and Surname B"
            return ' and '.join(author.split()[-1] for author in author_list)  + str_year
        else:
            # Return "First Author's Surname et al."
            return author_list[0].split()[-1] + ' et al.'  + str_year



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
            #self.title_field: self.title,
            self.author_field: self.author,
            self.year_field: self.year,
            #self.note_field: self.note,
            #self.file_field: self.file
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
                authors=dict_setter[self.author_field],
                year=dict_setter[self.year_field]
            )
        # alias
        if self.alias_field not in list_dict_keys:
            # set as citation key
            dict_setter[self.alias_field] = dict_setter[self.citation_key_field]
        # note
        if self.note_field not in list_dict_keys:
            # set as none
            dict_setter[self.note_field] = None
        # file
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
        self.note = dict_setter[self.note_field]
        # ... continues in downstream objects ... #

    def load(self, file_path, order=0):
        """Load reference from Bib file.

        :param file_path: file path to bib file
        :type file_path: str
        :param order: order number in the bib file (first = 0)
        :type order: int
        :return: None
        :rtype: None
        """
        list_refs = self.parse_bibfile(file_path=file_path)
        self.set(dict_setter=list_refs[order])
        return None

    def export_note(self):
        if self.note is not None:
            dict_note = self.parse_note(note=self.note)
            dict_note[self.type_field] = self.type
            dict_note[self.citation_key_field] = self.citation_key
            dict_note[self.name_field] = self.name
            dict_note[self.year_field] = self.year
            return dict_note
        else:
            return None


class RefCollection(Collection):  # todo docstring

    def __init__(self, name="MyRefCollection", alias="myRefCol"):  # todo docstring
        super().__init__(base_object=Ref, name=name, alias=alias)

    def load(self, file_path):  # todo docstring
        list_refs = Ref.parse_bibfile(file_path)
        for i in range(len(list_refs)):
            rf = Ref()
            rf.load(file_path=f, order=i)
            self.append(new_object=rf)

    def get_notes(self):   # todo docstring
        list_notes = []
        for ref in self.collection:
            d = self.collection[ref].export_note()
            if d is None:
                pass
            else:
                list_notes.append(d)
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(list_notes)

        # dummy ref
        rf = Ref()
        # Columns to move to the beginning
        cols_to_move = [
            rf.type_field,
            rf.citation_key_field,
            rf.name_field,
            "main"
        ]
        # Remaining columns
        remaining_cols = [col for col in df.columns if col not in cols_to_move]
        # New column order
        new_order = cols_to_move + remaining_cols
        # Reordered DataFrame
        df_reordered = df[new_order]
        return df_reordered



if __name__ == "__main__":
    import pandas as pd
    f = "./templates/paper/refs.bib"
    f = r"C:\Users\Ipo\Downloads\invest.bib"

    refcol = RefCollection(name="InVEST Habitat Quality", alias="investhq")
    refcol.load(file_path=f)


    df = refcol.get_notes()
    print(df[["Name", "Uncertainty", "Integration"]].sort_values(by="Uncertainty").to_string())
    #df.to_csv("C:/data/refs_invest.csv", sep=";", index=False)

