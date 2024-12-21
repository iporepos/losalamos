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

import os, re, shutil, glob
import requests
from losalamos.root import MbaE, Collection, Note
import tkinter as tk
from tkinter import filedialog, messagebox



class RefForm(tk.Tk):
    # todo evaluate move or rebase

    def __init__(self, lib_folder, inp_folder, kind_opts, title="Add References"):
        super().__init__()
        self.title(title)
        self.geometry("550x450")
        self.folder_lib_def = lib_folder
        self.folder_inp_def = inp_folder
        self.options_def = kind_opts[:]
        self.form_data = {}
        self.create_widgets()

    def create_widgets(self):
        # Output folder
        tk.Label(self, text="Library Folder:").grid(
            row=0, column=0, padx=4, pady=4, sticky="w"
        )
        self.folder_lib = tk.Entry(self, width=50)
        self.folder_lib.grid(row=0, column=1, padx=10, pady=4)
        self.folder_lib.insert(0, self.folder_lib_def)
        tk.Button(self, text="Browse", command=self.browse_folder_lib).grid(
            row=0, column=2, padx=4, pady=4
        )

        # Input folder
        tk.Label(self, text="Input Folder:").grid(
            row=1, column=0, padx=4, pady=4, sticky="w"
        )
        self.folder_inp = tk.Entry(self, width=50)
        self.folder_inp.grid(row=1, column=1, padx=10, pady=4)
        self.folder_inp.insert(0, self.folder_inp_def)
        tk.Button(self, text="Browse", command=self.browse_folder_inp).grid(
            row=1, column=2, padx=4, pady=4
        )

        # Kind of input
        tk.Label(self, text="Entry type:").grid(
            row=2, column=0, padx=4, pady=4, sticky="w"
        )
        self.kind_var = tk.StringVar(self)
        self.kind_var.set("paper")  # default value
        kind_options = self.options_def[:]
        self.kind_menu = tk.OptionMenu(self, self.kind_var, *kind_options)
        self.kind_menu.grid(row=2, column=1, padx=10, pady=4, sticky="w")

        # Tags
        tk.Label(self, text="Tags:").grid(row=4, column=0, padx=4, pady=4, sticky="w")
        self.tags_listbox = tk.Listbox(self, selectmode=tk.SINGLE, width=50, height=6)
        self.tags_listbox.grid(row=3, column=1, padx=10, pady=4)
        self.tags_entry = tk.Entry(self, width=40)
        self.tags_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        tk.Button(self, text="Add", width=6, command=self.add_tag).grid(
            row=4, column=2, padx=2, pady=5, sticky="w"
        )
        tk.Button(self, text="Remove", width=6, command=self.remove_tag).grid(
            row=4, column=3, padx=4, pady=5, sticky="w"
        )

        # Related notes
        tk.Label(self, text="Related:").grid(
            row=6, column=0, padx=4, pady=4, sticky="w"
        )
        self.related_listbox = tk.Listbox(
            self, selectmode=tk.SINGLE, width=50, height=3
        )
        self.related_listbox.grid(row=5, column=1, padx=10, pady=4)
        self.related_entry = tk.Entry(self, width=40)
        self.related_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
        tk.Button(self, text="Add", width=6, command=self.add_related).grid(
            row=6, column=2, padx=2, pady=5, sticky="w"
        )
        tk.Button(self, text="Remove", width=6, command=self.remove_related).grid(
            row=6, column=3, padx=4, pady=5, sticky="w"
        )

        # Include BIB file
        tk.Label(self, text="Include BibTeX:").grid(
            row=7, column=0, padx=4, pady=4, sticky="w"
        )
        self.include_bib = tk.BooleanVar()
        tk.Checkbutton(self, variable=self.include_bib).grid(
            row=7, column=1, padx=10, pady=4, sticky="w"
        )

        # Submit button
        tk.Button(self, text="Submit", command=self.submit_form).grid(
            row=8, column=0, columnspan=3, pady=20
        )
        tk.Button(self, text="Cancel", command=self.cancel_form).grid(
            row=8, column=1, columnspan=3, padx=10, pady=20
        )

    def browse_folder_lib(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_lib.delete(0, tk.END)
            self.folder_lib.insert(0, folder)

    def browse_folder_inp(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_inp.delete(0, tk.END)
            self.folder_inp.insert(0, folder)

    @staticmethod
    def covert_entry_to_list(entry_str):
        # todo evaluate move
        # replace commas
        entry_str = entry_str.replace(", ", ";")
        entry_str = entry_str.replace(",", ";")
        # drop hashs
        entry_str = entry_str.replace("#", "")
        # get list
        entry_ls = entry_str.split(";")
        entry_ls = [e.strip() for e in entry_ls]
        # remove duplicates
        entry_ls = list(set(entry_ls))
        return entry_ls

    def add_tag(self):
        tag = self.tags_entry.get()
        if tag:
            tag_ls = RefForm.covert_entry_to_list(entry_str=tag)
            tag_ls = [tag.replace(" ", "-").lower() for tag in tag_ls]
            for tag in tag_ls:
                self.tags_listbox.insert(tk.END, f"#{tag}")
            self.tags_entry.delete(0, tk.END)

    def remove_tag(self):
        selected_tag_index = self.tags_listbox.curselection()
        if selected_tag_index:
            self.tags_listbox.delete(selected_tag_index)

    def add_related(self):
        related_note = self.related_entry.get()
        if related_note:
            rel_ls = RefForm.covert_entry_to_list(entry_str=related_note)
            rel_ls = [related_note.strip() for related_note in rel_ls]
            for related_note in rel_ls:
                self.related_listbox.insert(tk.END, f"[[{related_note}]]")
            self.related_entry.delete(0, tk.END)

    def remove_related(self):
        selected_related_index = self.related_listbox.curselection()
        if selected_related_index:
            self.related_listbox.delete(selected_related_index)

    def submit_form(self):
        folder_lib = self.folder_lib.get()
        folder_inp = self.folder_inp.get()
        kind = self.kind_var.get()
        tags = list(self.tags_listbox.get(0, tk.END))
        related = list(self.related_listbox.get(0, tk.END))
        include_bib = self.include_bib.get()

        self.form_data = {
            "folder_lib": folder_lib,
            "folder_inp": folder_inp,
            "kind": kind,
            "tags": tags,
            "related": related,
            "include_bib": include_bib,
        }
        self.quit()  # Close the Tkinter window

    def cancel_form(self):
        self.form_data = None
        self.quit()

    def get_form_data(self):
        return self.form_data


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
            dict_setter[self.file_bib_field] = self.file_bib
        # file_note
        if self.file_note_field not in list_dict_keys:
            # set as none
            dict_setter[self.file_note_field] = self.file_note
        # file_doc
        if self.file_doc_field not in list_dict_keys:
            # set as none
            dict_setter[self.file_doc_field] = self.file_doc

        # ---------- set basic attributes --------- #
        super().set(dict_setter=dict_setter)
        self.entry_type = dict_setter[self.type_field]
        self.citation_key = dict_setter[self.citation_key_field]
        self.title = dict_setter[self.title_field]
        self.author = dict_setter[self.author_field]
        self.year = dict_setter[self.year_field]
        self.file_note = dict_setter[self.file_note_field]
        self.file_doc = dict_setter.get(self.file_doc_field, None)

        # ... continues in downstream objects ... #

    def load_bib(self, order=0):
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
        """Loads a note and assigns it to the instance variable.

        This method initializes a RefNote object with the instance's name and alias,
        sets its file_note attribute, and then calls the load method on the RefNote object.
        """
        self.note = RefNote(name=self.name, alias=self.alias)
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

    def to_note(
        self,
        output_dir,
        note_template,
        filename=None,
        body=None,
        tags=None,
        related=None,
        references=None,
        pdf_name=None
    ):
        """Converts the current reference to a note and saves it to a file.

        :param output_dir: The directory where the note file will be saved.
        :type output_dir: str
        :param filename: The name of the note file to be created.
        :type filename: str
        :param body: Optional body of the note to include in the note.
        :type body: list or None
        :param tags: Optional tags associated with the note.
        :type tags: list or None
        :param related: Optional related references.
        :type related: list or None
        :param references: Optional references to include in the note.
        :type references: list or None
        :param pdf_name: Optional PDF file name
        :type pdf_name: str or None
        :return: The path to the saved note file.
        :rtype: str
        """
        from datetime import datetime

        # get note
        n = RefNote()
        n.file_note = note_template

        # load template data
        n.load()
        # set incoming data for the body
        if body:
            n.data["Body"] = body[:]
        # update metadata with bib
        n.metadata.update(self.bib_dict.copy())
        n._standardize_metatada()

        # handle tags
        if tags:
            n.metadata["tags"] = list(set(tags))

        # compute timestamp
        _now = datetime.now()
        n.metadata["timestamp"] = _now.strftime("%Y-%m-%d %H:%M")

        # set citation in
        citation_in = Ref.cite_intext(bib_dict=self.bib_dict.copy(), text_format="plain")
        n.metadata["citation_in"] = citation_in

        # set PDF file field
        if pdf_name is None:
            # use citation key
            pdf_name = n.metadata["citation_key"]
        n.metadata["file"] = '"[[{}.pdf]]"'.format(pdf_name)

        # handle data
        n.update_data(related_list=related)


        output_file = "{}/{}.md".format(output_dir, filename)
        n.file_note = output_file
        n.save()
        return output_file


    def _to_note(
        self,
        output_dir,
        filename=None,
        comments=None,
        tags=None,
        related=None,
        references=None,
        pdf_name=None
    ):
        """Converts the current reference to a note and saves it to a file.

        :param output_dir: The directory where the note file will be saved.
        :type output_dir: str
        :param filename: The name of the note file to be created.
        :type filename: str
        :param comments: Optional body to include in the note.
        :type comments: str or None
        :param tags: Optional tags associated with the note.
        :type tags: list or None
        :param related: Optional related references.
        :type related: list or None
        :param references: Optional references to include in the note.
        :type references: list or None
        :param pdf_name: Optional PDF file name
        :type pdf_name: str or None
        :return: The path to the saved note file.
        :rtype: str
        """
        from datetime import datetime

        # Function to replace placeholders in a string using a dictionary
        # todo evaluate move to editor class
        def replace_placeholders(string, replacements):
            for placeholder, replacement in replacements.items():
                string = string.replace(placeholder, replacement)
            return string

        # basic

        # get note
        n = RefNote()
        n.metadata = self.bib_dict.copy()
        n.data = n.get_template(kind="bib")

        # standard metadata
        n.standardize_metatada()

        # handle tags
        if tags:
            n.metadata["tags"] = tags

        # compute timestamp
        _now = datetime.now()
        n.metadata["timestamp"] = _now.strftime("%Y-%m-%d %H:%M")

        # set file
        if pdf_name is None:
            # use citation key
            pdf_name = n.metadata["citation_key"]
        n.metadata["file"] = '"[[{}.pdf]]"'.format(pdf_name)

        # HANDLE CONTENTs

        # setup
        citation_in = Ref.cite_intext(bib_dict=self.bib_dict, text_format="plain")
        citation_in_md = Ref.cite_intext(bib_dict=self.bib_dict, text_format="md")
        citation_full_plain = Ref.cite_full(self.bib_dict, text_format="plain")
        title = f"**{self.bib_dict[self.title_field]}** by {citation_in}"

        # citation parameter:
        n.metadata["citation_in"] = citation_in[:]

        # Note
        nt_dict = RefNote.get_template(kind="bib", head_name=citation_in_md)

        if related:
            related_str = " ".join([f"[[{rel}]]" for rel in related])
        else:
            related_str = ""

        if "abstract" in n.metadata:
            if n.metadata["abstract"]:
                abs_str = n.metadata["abstract"]
            else:
                abs_str = ""
        else:
            abs_str = ""

            # edit contents
        replacements = {
            "{{LIBRARY ITEM}}": self.bib_dict[self.type_field].upper(),
            "{{Title}}": f"**{self.bib_dict[self.title_field]}** by {citation_in_md}",
            "{{related}}": related_str,
            "{{file_link}}": pdf_name + ".pdf",
            "{{abstract}}": abs_str,
            "{{In-text citation}}": citation_in,
            "{{Full citation}}": citation_full_plain,
            "{{BibTeX}}": Ref.bib_to_str(bib_dict=self.bib_dict),
            "{{references}}": "",  # this is missing
        }

        for sec in nt_dict:
            template_strings = nt_dict[sec]["Content"][:]
            # Update the list of strings
            updated_strings = [
                replace_placeholders(string, replacements)
                for string in template_strings
            ]
            nt_dict[sec]["Content"] = updated_strings[:]

        n.data = nt_dict.copy()

        # export note to file
        if filename is None:
            filename = n.metadata["citation_key"]

        output_file = "{}/{}.md".format(output_dir, filename)
        n.to_file(file_path=output_file)
        return output_file

    def add_to_lib(self, lib_folder, note_template, tags=None, related=None, comments=None, pdf_name=None, note_name=None):
        """Adds the current item to the specified library folder.

        :param lib_folder: The path to the library folder where the item will be added.
        :type lib_folder: str
        :param tags: Optional tags associated with the item.
        :type tags: list or None
        :param related: Optional related items.
        :type related: list or None
        :param comments: Optional body about the item.
        :type comments: str or None
        :param pdf_name: Optional PDF file name
        :type pdf_name: str or None
        :param note_name: Optional note file name
        :type note_name: str or None
        :return: None
        :rtype: None
        """
        # update lib folder
        self.lib_folder = lib_folder
        self.standardize()

        # export pdf
        if self.file_doc:
            if pdf_name is None:
                if self.bib_dict["entry_type"] == "article":
                    pdf_name = self.bib_dict["citation_key"]
                elif self.bib_dict["entry_type"] == "book":
                    pdf_name = self.bib_dict["title"]
            shutil.copy(
                src=self.file_doc,
                dst="{}/{}.pdf".format(self.lib_folder, pdf_name),
            )

        if note_name is None:
            if self.bib_dict["entry_type"] == "article":
                note_name = self.bib_dict["citation_key"]
            elif self.bib_dict["entry_type"] == "book":
                note_name = self.bib_dict["title"]

        # get note now
        o = self.to_note(
            output_dir=self.lib_folder,
            note_template=note_template,
            filename=note_name,
            tags=tags,
            related=related,
            body=comments,
            pdf_name=pdf_name
        )
        print(f"--- Added: {o}")

    def to_bib(self, output_dir, filename):
        """Generates a .bib file from the current item's data and saves it to the specified directory.

        :param output_dir: The directory where the .bib file will be saved.
        :type output_dir: str
        :param filename: The name of the .bib file to be created.
        :type filename: str
        :return: The path to the saved .bib file.
        :rtype: str
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
        print(file_path)
        return file_path

    @staticmethod
    def get_citation_keys(lib_folder):
        """Get the list of citations key from a library folder.
        The folder is expected to hold references in md files named by
        the respective citations keys.
        The "_" is considered a flag for md files not related to the reference.

        :param lib_folder: path to library directory
        :type lib_folder: str
        :return: list of names of citation keys
        :rtype: list
        """
        # List to hold the filtered filenames
        filtered_files = []

        # Iterate through all files in the directory
        for filename in os.listdir(lib_folder):
            # Check if the file has a ".md" extension and does not contain the "_" character
            if filename.endswith(".md") and "_" not in filename:
                filtered_files.append(filename[:-3])

        return filtered_files

    @staticmethod
    def bibstr_to_dict(bibtex_str):
        """Converts a BibTeX string into a dictionary representation.

        :param bibtex_str: The BibTeX string to convert.
        :type bibtex_str: str
        :return: A dictionary with the BibTeX entry's type, citation key, and fields.
        :rtype: dict
        """
        # Regular expression patterns
        entry_pattern = re.compile(r"@\w+\{")
        key_pattern = re.compile(r"@\w+\{(.+?),")
        field_pattern = re.compile(r'(\w+)\s*=\s*[{"](.*?)[}"],?', re.DOTALL)

        # Extract entry type and citation key
        entry_type_match = entry_pattern.search(bibtex_str)
        key_match = key_pattern.search(bibtex_str)

        if not entry_type_match or not key_match:
            raise ValueError("Invalid BibTeX entry format")

        entry_type = entry_type_match.group()[1:-1]
        citation_key = key_match.group(1)

        # Create the dictionary with initial keys
        bib_dict = {"entry_type": entry_type, "citation_key": citation_key}

        # Extract fields
        fields = field_pattern.findall(bibtex_str)
        for field in fields:
            key, value = field
            bib_dict[key.strip()] = value.strip()

        return bib_dict

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

                # Ignore empty lines and body
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

        # Using dictionary comprehension
        bib_dict = {key: (value if value is not None else "") for key, value in bib_dict.items()}

        author = bib_dict.get("author", "Unknown Author").strip()
        year = str(bib_dict.get("year", "n.d.")).strip()
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
        # Using dictionary comprehension
        bib_dict = {key: (value if value is not None else "") for key, value in bib_dict.items()}

        author = bib_dict.get("author", "Unknown Author").strip()
        year = str(bib_dict.get("year", "n.d.")).strip()
        title = bib_dict.get("title", "Untitled").strip()
        if title.startswith('"'):
            title = title[1:]
        if title.endswith('"'):
            title = title[:-1]
        journal = bib_dict.get("journal", "").strip()
        if journal.startswith('"'):
            journal = journal[1:]
        if journal.endswith('"'):
            journal = journal[:-1]
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
            doi_str = f"{doi}" if doi else ""
            if style == "apa":
                citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}. {doi_str}"
            elif style == "mla":
                citation = f'{formatted_authors}. "{title}." {journal} {volume}.{issue} ({year}): {pages}. {doi_str}'
            elif style == "chicago":
                citation = f'{formatted_authors}. "{title}." {journal} {volume}, no. {issue} ({year}): {pages}.{doi_str}'
            elif style == "harvard":
                citation = f"{formatted_authors} ({year}) '{title}', {journal}, vol. {volume}, no. {issue}, pp. {pages}. {doi_str}"
            elif style == "vancouver":
                citation = f"{formatted_authors}. {title}. {journal}. {year};{volume}({issue}):{pages}. {doi_str}"
            elif style == "abnt":
                citation = f"{formatted_authors}. {title}. {journal}, {volume}.({issue}), p. {pages}, {year}. {doi_str}"
            else:
                citation = f"{formatted_authors} ({year}). {title}. {journal}, {volume_issue}{pages_str}. {doi_str}"
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
        """Converts a dictionary representation of a BibTeX entry into a string.

        :param bib_dict: The dictionary containing the BibTeX entry data.
        :type bib_dict: dict
        :param entry_field: The key for the entry type in the dictionary.
        :type entry_field: str
        :param citation_field: The key for the citation key in the dictionary.
        :type citation_field: str
        :return: The BibTeX entry as a formatted string.
        :rtype: str
        """
        #
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
            + "\n}"
        )
        return bibtex_str

    @staticmethod
    def standard_author(bib_dict):
        """Converts a dictionary representation of a BibTeX entry into a string.

        :param bib_dict: The dictionary containing the BibTeX entry data.
        :type bib_dict: dict
        :param entry_field: The key for the entry type in the dictionary.
        :type entry_field: str
        :param citation_field: The key for the citation key in the dictionary.
        :type citation_field: str
        :return: The BibTeX entry as a formatted string.
        :rtype: str
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
    def query_doi(doi):
        """Web query for doi

        :param doi: reference doi
        :type doi: str
        :return: bibtex dict
        :rtype: dict or None
        """
        print(f">>> searching doi {doi}")
        # Construct the URL to retrieve the citation
        url = f"https://doi.org/{doi}"
        try:
            # get the citation
            bibtex_response = requests.get(
                url, headers={"Accept": "application/x-bibtex"}
            )

            # Check if the request was successful
            if bibtex_response.status_code == 200:
                print(">>> got doi response")
                bibtex_citation = bibtex_response.text
                bib_dict = Ref.bibstr_to_dict(bibtex_citation)
                bib_dict["doi"] = doi
                return bib_dict
            else:
                return None
        except requests.Timeout:
            print("The request timed out")
            return None

    @staticmethod
    def query_xref(search_query, include_refs=True):
        """Queries a cross-reference service and extracts BibTeX entries from the search results.

        :param search_query: The query string to search for.
        :type search_query: str
        :param include_refs: Whether to include references in the search results.
        :type include_refs: bool
        :return: A list of dictionaries containing BibTeX entries.
        :rtype: list
        """

        def extract_bibtex_entry(data):
            # Handle authors
            if "author" in data:
                lst_authors = [
                    f"{author['family']}, {author['given']}"
                    for author in data["author"]
                ]
                authors = " and ".join(lst_authors)
            else:
                authors = None

            bibtex_entry = {
                "entry_type": data.get(
                    "type", "article"
                ),  # Default to "article" if not specified
                "author": authors,
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
                "keywords": data.get("subject", []),
            }
            # Remove None values
            bibtex_entry = {k: v for k, v in bibtex_entry.items() if v is not None}

            # set citation key and author
            if "author" in bibtex_entry:
                bibtex_entry["author"] = Ref.standard_author(bibtex_entry)
                bibtex_entry["citation_key"] = Ref.standard_key(bibtex_entry)
            else:
                bibtex_entry["author"] = "Unknow"
                bibtex_entry["citation_key"] = str(bibtex_entry["doi"])

            return bibtex_entry

        def get_refs(data):

            def find_doi(citation):
                citation_doi = None
                lst_uns = citation.split(",")
                for e in lst_uns:
                    if "https://doi.org/" in e:
                        has_doi = True
                        citation_doi = e[len("https://doi.org/") :]
                        break
                return citation_doi

            lst_references = []
            for i in range(len(data["items"][0]["reference"])):

                # handle DOI
                if "DOI" in data["items"][0]["reference"][i]:
                    known_doi = data["items"][0]["reference"][i]["DOI"]

                elif "unstructured" in data["items"][0]["reference"][i]:
                    # try to find in the text
                    citation = data["items"][0]["reference"][i]["unstructured"]
                    known_doi = find_doi(citation)
                else:
                    known_doi = None

                # Handle text
                if known_doi:
                    # print(f">>>> DOI is known: {known_doi}")
                    ref_bib_dict = Ref.query_doi(doi=known_doi)
                    # get citation
                    citation_formatted = Ref.cite_full(
                        bib_dict=ref_bib_dict, text_format="md"
                    )

                    # print(f">>>> {citation_formatted}")
                    lst_references.append(citation_formatted)
                elif "unstructured" in data["items"][0]["reference"][i]:
                    citation_formatted = data["items"][0]["reference"][i][
                        "unstructured"
                    ]
                    lst_references.append(citation_formatted)

                    # print(f">>>> {citation_formatted}")
                else:
                    pass
            # sort by name
            lst_references.sort()
            return lst_references

        # Generic tool for cross ref API

        # CrossRef API search URL
        search_url = f'https://api.crossref.org/works?query.bibliographic="{search_query}"&rows=2'
        output_data = None

        try:
            response = requests.get(search_url, timeout=2)

            # Handle response
            if response.status_code == 200:  # json code
                print(">>> got response")
                data = response.json().get("message", {})
                print(">>> got data")
                # handle main bibtex:
                main_bib = extract_bibtex_entry(data=data["items"][0])
                # handle references
                lst_references = None
                if include_refs:
                    if "reference" in data["items"][0]:
                        lst_references = get_refs(data=data)
                    else:
                        lst_references = None

                output_data = {"Main": main_bib, "References": lst_references}
        except requests.Timeout:
            print("The request timed out")

        return output_data

    @staticmethod
    def add(lib_folder, file_bib, file_pdf=None, tags=None, related=None):
        """Adds a reference to the specified library folder.

        :param lib_folder: The path to the library folder where the reference will be added.
        :type lib_folder: str
        :param file_bib: The path to the BibTeX file.
        :type file_bib: str
        :param file_pdf: The path to the PDF file, if any.
        :type file_pdf: str or None
        :param tags: Optional tags associated with the reference.
        :type tags: list or None
        :param related: Optional related references.
        :type related: list or None
        :return: None
        :rtype: None
        """
        r = Ref()
        # set parameters
        r.file_bib = file_bib
        r.file_doc = file_pdf
        # load bib
        r.load_bib(order=0)

        if r.bib_dict["entry_type"] == "article":
            new_tags = ["science", "paper"]
            if tags:
                tags = list(set(tags + new_tags))
            else:
                tags = new_tags[:]
        # run
        r.add_to_lib(lib_folder=lib_folder, tags=tags, related=related)

    @staticmethod
    def add_bat(lib_folder, input_folder, note_template, tags=None, related=None):
        """Adds multiple references from an input folder to the specified library folder.

        :param lib_folder: The path to the library folder where the references will be added.
        :type lib_folder: str
        :param input_folder: The folder containing the BibTeX files to add.
        :type input_folder: str
        :param tags: Optional tags associated with the references.
        :type tags: list or None
        :param related: Optional related references.
        :type related: list or None
        :return: None
        :rtype: None
        """
        # get list of bib files
        ls_bib_files = glob.glob("{}/*.bib".format(input_folder))

        # load all bibs
        ls_bibs = []
        for f in ls_bib_files:
            print(f"--- Bat file: {f}")
            # parse the list of refs
            lst_lcl_bibs = Ref.parse_bibtex(f)
            ls_bibs = ls_bibs + lst_lcl_bibs[:]
            # delete file
            os.remove(f)

        for b in ls_bibs:
            r = Ref()
            r.bib_dict = b.copy()
            # expected pdfs with citation key names
            if r.bib_dict["entry_type"] == "article":
                expected_pdf = "{}/{}.pdf".format(input_folder, r.bib_dict["citation_key"])
            if r.bib_dict["entry_type"] == "book":
                expected_pdf = "{}/{}.pdf".format(input_folder, r.bib_dict["title"])

            if os.path.isfile(expected_pdf):
                r.file_doc = expected_pdf

            if r.bib_dict["entry_type"] == "article":
                new_tags = ["science", "paper"]
                if tags:
                    tags = list(set(tags + new_tags))
                else:
                    tags = new_tags[:]

            if r.bib_dict["entry_type"] == "book":
                new_tags = ["book"]
                if tags:
                    tags = list(set(tags + new_tags))
                else:
                    tags = new_tags[:]

            r.add_to_lib(
                lib_folder=lib_folder,
                note_template=note_template,
                tags=tags,
                related=related
            )
            if os.path.isfile(expected_pdf):
                os.remove(expected_pdf)

        return None

class RefNote(Note):

    def __init__(self, name="MyRefNote", alias="RNt1"):
        super().__init__(name=name, alias=alias)
        # ---

        # TEXT FIELD TO AVOID CORRUPTED HEADING BY : OR "
        self.text_fields = {
            "article": ["title", "abstract", "issn", "journal", "file"],
            "book": ["title", "isbn", "file", "abstract"]
        }

        self.metadata_entries = {
            "article": [
                "doi",
                "entry_type",
                "citation_key",
                "author",
                "year",
                "title",
                "journal",
                "volume",
                "number",
                "pages",
                "issn",
                "url",
                "abstract",
                "tags",
                "timestamp",
                "file",
                "citation_in"
            ],
            "book": [
                "isbn",
                "entry_type",
                "citation_key",
                "author",
                "year",
                "title",
                "publisher",
                "url",
                "abstract",
                "tags",
                "timestamp",
                "file",
                "citation_in"
            ]
        }

    def load_metadata(self):
        super().load_metadata()
        self._standardize_metatada()

    def _standardize_metatada(self):
        """Standardizes the metadata for the current reference.

        :return: None
        :rtype: None
        """
        new_meta = {}
        # pass
        for e in self.metadata_entries[self.metadata["entry_type"]]:
            new_meta[e] = self.metadata.get(e, None)

        # handle text fields
        ls_fields = self.text_fields[self.metadata["entry_type"]][:]
        for e in ls_fields:
            if new_meta[e]:
                new_meta[e] = '"{}"'.format(new_meta[e])

        # special procedures
        if self.metadata["entry_type"] == "article":
            # handle doi url
            if self.metadata["doi"]:
                doi = self.metadata["doi"]
                if doi.startswith("https://doi.org/"):
                    pass
                else:
                    new_meta["doi"] = "https://doi.org/" + doi

        self.metadata = new_meta.copy()


    def update_data(self, related_list=None):
        """Updates the data structure with the head, body, and tail sections.

        :param related_list: A list of related entries to include in the body (default is None).
        :type related_list: list, optional
        :return: None
        """
        self.update_head()
        self.update_body(related_list=related_list)
        self.update_tail()
        return None

    def update_head(self):
        """Updates the head section of the data structure based on the metadata.

        :return: None
        """
        entry_type = self.metadata["entry_type"]
        if entry_type == "article":
            bib_dict = self.metadata.copy()
            citation_in = Ref.cite_intext(bib_dict=bib_dict, text_format="md")
            if self.metadata["abstract"]:
                abs_str = self.metadata["abstract"][1:-1]
            else:
                abs_str = ""
            self.data["Head"] = [
                "", f"# {citation_in}", "",
                "{}".format(self.metadata["entry_type"]).upper(), "",
                "**{}**".format(self.metadata["title"][1:-1]), "",
                "by {}".format(citation_in), "",
                "file: [[{}.pdf]]".format(self.metadata["citation_key"]), "",
                "> [!Info]- Abstract", "> {}".format(abs_str)
            ]

        if entry_type == "book":
            bib_dict = self.metadata.copy()
            citation_in = Ref.cite_intext(bib_dict=bib_dict, text_format="md")
            title_str = self.metadata["title"][1:-1]
            if self.metadata["abstract"]:
                abs_str = self.metadata["abstract"][1:-1]
            else:
                abs_str = ""
            self.data["Head"] = [
                "", f"# {title_str}", "",
                "{}".format(self.metadata["entry_type"]).upper(), "",
                "**{}**".format(self.metadata["title"][1:-1]), "",
                "by {}".format(citation_in), "",
                "file: [[{}.pdf]]".format(title_str), "",
                "> [!Info]- Abstract", "> {}".format(abs_str)
            ]

        return None



    def update_body(self, related_list=None):
        """Updates the body section of the data structure, including highlights, related entries, and references.

        :param related_list: A list of related entries to include in the body (default is None).
        :type related_list: list, optional
        :return: None
        """

        def insert_list_at_flag(target_list, insert_list, flag):
            if flag in target_list:
                index = target_list.index(flag)
                return target_list[:index + 1] + insert_list + target_list[index + 1:]
            else:
                print(f"Flag '{flag}' not found in the target list.")
                return target_list

        if "# Overview" not in self.data["Body"]:
            _ls = [
                "# Overview", "",
                "> [!Abstract]+ Highlights", "> - List highlights", "",
                "> [!Example]+ Related", "> - List related", "",
            ]

            self.data["Body"] = _ls + self.data["Body"][:]
        if "# References" not in self.data["Body"]:
            _ls = [
                "",
                "# References", "",
                " - List references", "",
            ]
            self.data["Body"] =  self.data["Body"][:] + _ls


        if related_list:
            insert_ls = ["> - {}".format(related) for related in related_list]
            new_body = insert_list_at_flag(
                target_list=self.data["Body"],
                insert_list=insert_ls,
                flag="> [!Example]+ Related"
            )
            self.data["Body"] = new_body[:]



        return None

    def update_tail(self):
        """Updates the tail section of the data structure with bibliographic information.

        :return: None
        """
        entry_type = self.metadata["entry_type"]
        if entry_type == "article" or entry_type == "book":
            bib_dict = self.metadata.copy()
            citation_in = Ref.cite_intext(bib_dict=bib_dict, text_format="plain")
            citation_fu = Ref.cite_full(
                bib_dict=bib_dict, text_format="plain", entry_type=entry_type)
            bib_str = Ref.bib_to_str(bib_dict=self.get_bib_dict())
            self.data["Tail"] = [
                "# Bibliographic information", "",
                "## In-text citation",
                "```",
                citation_in,
                "```", "",
                "## Full citation",
                "```",
                citation_fu,
                "```", "",
                "## BibTeX entry",
                "```",
                bib_str,
                "```",
            ]
        return None


    @staticmethod
    def get_template(kind="bib", head_name=None):
        """"Returns a template dictionary for a given kind of entry.

        :param kind: The type of template to retrieve (default is "bib").
        :type kind: str
        :param head_name: The header name to use in the template (default is "Header").
        :type head_name: str
        :return: A dictionary containing the template structure.
        :rtype: dict
        """
        if head_name is None:
            head_name = "Header"
        templates = {
            "bib": {
                head_name: {
                    "Parent Section": None,
                    "Level": 1,
                    "Content": [
                        "{{LIBRARY ITEM}}\n",
                        "{{Title}}\n",
                        "**Summary:** Insert a paragraph comment here\n",
                        "related: {{related}}\n",
                        "file: [[{{file_link}}]]\n",
                        "## Abstract\n",
                        " > {{abstract}}\n" "\n---",
                    ],
                },
                "Comments": {
                    "Parent Section": None,
                    "Level": 1,
                    "Content": [
                        "*Start typing here*\n\n",
                        "\n---",
                    ],
                },
                "Bibliographic information": {
                    "Parent Section": None,
                    "Level": 1,
                    "Content": [
                        "## Citation",
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
                        "{{references}}",
                    ],
                },
            }
        }

        return templates[kind]


    def get_bib_dict(self):
        keys_to_remove = ['tags', 'timestamp', 'file', 'citation_in']
        new_dict = {k: v for k, v in self.metadata.items() if k not in keys_to_remove}
        # Using dictionary comprehension
        new_dict = {key: (value if value is not None else "") for key, value in new_dict.items()}
        lst_text_fields = self.text_fields[self.metadata["entry_type"]][:]
        for k in lst_text_fields:
            if k not in keys_to_remove:
                new_dict[k] = new_dict[k][1:-1]
        return new_dict


    @staticmethod
    def get_bib(file_path):
        """Get a bib dictionaty from the content of a RefNote file.
        The BibTex snippet is expected to exist in the note content

        :param file_path:
        :type file_path:
        :return:
        :rtype:
        """
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        bibtex_dict = {}
        entry_type = ""
        citation_key = ""
        in_bibtex = False
        bibtex_lines = []

        for line in lines:
            if line.strip().startswith("@"):
                in_bibtex = True
                entry_type, rest = line.strip()[1:].split("{", 1)
                citation_key, rest = rest.split(",", 1)
                bibtex_lines.append(rest.strip())
            elif in_bibtex:
                bibtex_lines.append(line.strip())
                if line.strip().endswith("}}"):
                    break

        if not in_bibtex:
            return None

        fields_raw = " ".join(bibtex_lines).rstrip("}}").strip()
        fields_raw = re.sub(r",\s*}", "}", fields_raw)
        fields_raw += ","

        fields_pattern = re.compile(r"(\w+)\s*=\s*\{(.*?)\},", re.DOTALL)
        fields = fields_pattern.findall(fields_raw)

        bibtex_dict = {
            "entry_type": entry_type,
            "citation_key": citation_key,
        }

        for field in fields:
            key, value = field
            bibtex_dict[key.strip()] = value.strip()

        return bibtex_dict

    @staticmethod
    def get_intext_citation(file_path):
        """Extracts the in-text citation from a given file.

        :param file_path: The path to the file containing the in-text citation.
        :type file_path: str
        :return: The extracted in-text citation.
        :rtype: str
        """
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Regex to find in-text citations and the following code blocks
        pattern = re.compile(r"In-text citation:\n```\n(.*?)\n```", re.DOTALL)
        matches = pattern.findall(content)

        return matches[0]


class RefColl(Collection):  # todo docstring

    def __init__(self, name="MyRefCollection", alias="myRefCol"):
        super().__init__(base_object=Ref, name=name, alias=alias)

    def load(self, file_path):
        """Loads references from a BibTeX file and appends them to the instance.

        :param file_path: The path to the BibTeX file.
        :type file_path: str
        :return: None
        :rtype: None
        """
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

    def load_library(self, lib_folder, by="notes"):
        """"Loads references from a library folder and appends them to the instance.

        :param lib_folder: The path to the library folder.
        :type lib_folder: str
        :param by: The method to load references by (default is "notes").
        :type by: str
        :return: None
        :rtype: None
        """
        if by == "notes":
            ls_files = glob.glob(f"{lib_folder}/*.md")
            # loop in files
            for f in ls_files:
                # Extract BibTeX entry into a dictionary
                bibtex_dict = RefNote.get_bib(f)
                r = Ref()
                setter = {
                    r.author_field: bibtex_dict["author"],
                    r.year_field: bibtex_dict["year"],
                    r.type_field: bibtex_dict["entry_type"],
                    r.citation_key_field: bibtex_dict["citation_key"],
                    r.title_field: bibtex_dict["title"],
                }
                r.set(dict_setter=setter)
                r.bib_dict = bibtex_dict.copy()
                r.file_note = f
                pdf = os.path.join(
                    os.path.dirname(f), os.path.basename(f)[:-3] + ".pdf"
                )
                if os.path.isfile(pdf):
                    r.file_doc = pdf
                r.load_note()
                self.append(new_object=r)
