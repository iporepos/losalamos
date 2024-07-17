def teste():
    print("Add ref")





if __name__ == "__main__":
    import os, re
    from losalamos.refs import Ref, Note

    # setup
    folder_lib = "C:/Users/Ipo/_testing_lib"
    # get file paths
    file_bib = "C:/Users/Ipo/Downloads/hess-21-3427-2017.bib" # "C:/Users/Ipo/Downloads/Baker1936x.bib"
    file_doc = "C:/Users/Ipo/Downloads/hess-21-3427-2017.pdf" # "C:/Users/Ipo/Downloads/Baker1936x.pdf"

    export_all = True

    # instantiate reference object
    r = Ref()
    r.file_bib = file_bib
    r.file_doc = file_doc
    r.lib_folder = folder_lib
    # load bib file
    r.load_bib()

    # standardize bib
    r.standardize()
    print(r.bib_dict)
    print("fetching online resources...")
    xref = Ref.query_xref(
        search_query=f"{r.title} AND {r.author} AND {r.year}"
    )

    # DOI setup
    if "doi" in r.bib_dict:
        pass
    else:
        if xref:
            r.bib_dict["doi"] = xref["Main"]["doi"][:]
    print()
    print(r.bib_dict)

    r.references_list = xref["References"][:]

    # EXPORT
    if export_all:
        print("exporting...")
        r.export(
            output_dir=r.lib_folder,
            create_note=True,
        )
    print("Done")
