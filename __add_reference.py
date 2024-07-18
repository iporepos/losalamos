"""
Simple terminal-based script for adding references from a folder to a library

Library is expected to hold subfolders

"""

import os, glob
import pandas as pd
from losalamos.refs import Ref, Note, RefForm


def add_ref(
    file_bib, file_pdf, lib_folder, tags=None, related=None, search_online=True
):
    """Add a reference to the library.

    :param file_bib: Path to the .bib file.
    :type file_bib: str
    :param file_pdf: Path to the .pdf file.
    :type file_pdf: str
    :param lib_folder: Path to the library folder.
    :type lib_folder: str
    :param tags: Optional tags for the reference.
    :type tags: list, optional
    :param related: Optional related references.
    :type related: list, optional
    :return: None
    :rtype: None
    """
    # instantiate reference object
    r = Ref()

    # setup
    r.file_bib = file_bib
    r.file_doc = file_pdf
    r.lib_folder = lib_folder

    # load bib file
    r.load_bib()
    # standardize bib
    r.standardize()

    # tags and related
    if tags:
        r.note_tags = tags
    if related:
        r.note_related = related

    print(f"\n\n>>> -- processing {r.citation_key}")
    if search_online:
        print(">>> fetching online resources...")

        xref = Ref.query_xref(search_query=f"{r.title} AND {r.author} AND {r.year}")
        if xref:
            print(">>> online resources retrieved.")
            # DOI setup
            if "doi" in r.bib_dict:
                pass
            else:
                if xref["Main"]["doi"]:
                    print(">>> doi updated.")
                    r.bib_dict["doi"] = xref["Main"]["doi"][:]
            if xref["References"]:
                print(">>> references list updated.")
                r.references_list = xref["References"][:]

    # APPEND TO LOCAL INVENTORY
    print(">>> appending to local database ... [todo]")
    # todo feed local database or datafile

    # EXPORT FILES
    print(">>> exporting files ...")
    r.export(
        output_dir=r.lib_folder,
        create_note=True,
        include_bib=False,
    )
    print(">>> ok")


def set_and_run(form_data, run=True):
    """Setup util

    :param form_data:
    :type form_data: dict
    :param run: option for testing
    :type run: bool
    :return:
    :rtype:
    """
    # *********************************************************
    # FILL INFO

    # setup output folder
    folder_lib = form_data["folder_lib"]
    # "C:/Users/Ipo/_testing_lib"
    # #"C:/Users/Ipo/My Drive/athens/alexandria"

    # get file paths
    folder_inp = form_data["folder_inp"]

    # kind of input
    kind = form_data["kind"]

    # 9 max TAGS
    tags = form_data["tags"]

    # RELATED NOTES
    related = form_data["related"]

    # Decide if add individual bib file
    include_bib = form_data["include_bib"]

    # *********************************************************
    # Aux steps

    # set output folder

    # Kind of library item
    kinds = {
        "paper": "papers",
        "textbook": r"books/textbooks",
        "handbook": r"books/handbooks",
        "popsci": "books/popsci",
        # ... keep
    }
    if kind in kinds:
        folder_lib = os.path.join(folder_lib, kinds[kind])
    if not os.path.isdir(folder_lib):
        os.mkdir(folder_lib)

    # *********************************************************
    # GATHER FILES

    # find bib files
    lst_bibs = [os.path.join(folder_inp, f) for f in glob.glob(f"{folder_inp}/*.bib")]

    # explode bibs
    lst_bibs_actual = []
    lst_bibs_to_clean = []
    for f in lst_bibs:
        lst_bibs_dicts = Ref.parse_bibtex(f)
        if len(lst_bibs_dicts) > 1:
            for i in range(len(lst_bibs_dicts)):
                r = Ref()
                r.bib_dict = lst_bibs_dicts[i]
                r.citation_key = lst_bibs_dicts[i]["citation_key"]
                new_file = os.path.join(os.path.dirname(f), r.citation_key + ".bib")
                r.to_bib(output_dir=os.path.dirname(f), filename=r.citation_key)
                lst_bibs_actual.append(new_file)
                lst_bibs_to_clean.append(new_file)
        else:
            lst_bibs_actual.append(f)

    lst_bibs_actual.sort()

    # look for available pdfs
    lst_names = [os.path.basename(f[:-4]) for f in lst_bibs_actual]
    lst_pdfs_pot = [os.path.join(folder_inp, f + ".pdf") for f in lst_names]
    lst_pdfs = []
    for p in lst_pdfs_pot:
        if os.path.exists(p):
            lst_pdfs.append(p)
        else:
            lst_pdfs.append(None)

    # Table of incoming references
    df = pd.DataFrame({"Bib": lst_bibs_actual, "Pdf": lst_pdfs})
    df = df.sort_values(by="Bib")
    print(f">> Importing the following references to {folder_lib}")
    print(df.to_string(index=False))

    # criteria for searching online
    if kind == "paper":
        search_online = True
    else:
        search_online = False

    # *********************************************************
    # ADDING LOOP
    for i in range(len(df)):  # range(len(df)):
        # set
        file_bib = df["Bib"].values[i]
        file_doc = df["Pdf"].values[i]
        # run
        if run:
            add_ref(
                file_bib=file_bib,
                file_pdf=file_doc,
                lib_folder=folder_lib,
                tags=tags,
                related=related,
                search_online=search_online,
            )

    # *********************************************************
    # clean created bib files
    for f in lst_bibs_to_clean:
        os.remove(f)


if __name__ == "__main__":

    # Get the form data after the Tkinter window is closed
    while True:
        app = RefForm(
            lib_folder="",
            inp_folder="",
        )
        app.mainloop()
        form_data = app.get_form_data()
        if form_data:
            app.destroy()
            ls_field = [e for e in form_data]
            ls_value = [form_data[e] for e in form_data]
            df_form = pd.DataFrame({"Field": ls_field, "Input": ls_value})
            print(df_form.to_string(index=False))
            user = input("\nconfirm input? (Y/n) [q] >> ")
            if user.lower().strip() == "q":

                break
            elif user.lower().strip() != "n":
                set_and_run(form_data=form_data, run=True)
                break
        else:
            break
