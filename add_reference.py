def teste():
    print("Add ref")


if __name__ == "__main__":
    import os
    from losalamos.refs import Ref, Note
    folder_lib = "C:/Users/Ipo/_testing_lib"
    conflict_list = Ref.get_citation_keys(lib_folder=folder_lib)
    print(f"Library: {folder_lib}")
    print("Current references:")
    for c in conflict_list:
        print(c)
    print("")
    # get file paths
    file_bib = "C:/Users/Ipo/Downloads/hess-21-3427-2017.bib"
    file_doc = "C:/Users/Ipo/Downloads/hess-21-3427-2017.pdf"

    # instantiate reference object
    r = Ref(
        file_bib=file_bib,
        file_doc=file_doc
    )
    # load bib file
    r.load_bib()

    # standardize bib
    r.standardize(conflict_list=conflict_list)
    # check out
    for e in r.bib_dict:
        print(f"{e}: {r.bib_dict[e]}")

    # EXPORT
    print("exporting...")
    #r.export(output_dir=folder_lib, create_note=False)

    print("Done")

    f_note = "C:/Users/Ipo/_testing_lib/bash.md"
    n = Note()
    print(n)

    n.file_note = f_note
    n.load()

    print(n)
    print(n.get_metadata_df()["Value"].values)
    # export method
    '''
    Note.to_md(
        md_dict=nt_dict,
        output_dir=folder_lib,
        filename="bash_2"
    )
    '''
