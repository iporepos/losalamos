import argparse
import os

from losalamos.refs import Ref


def process_bibtex(src_folder):
    f = f"{src_folder}/src.bib"
    ls = Ref.parse_bibtex(file_bib=f)

    for e in ls:
        r = Ref()
        r.set(dict_setter=e.copy())
        r.bib_dict = e.copy()
        r.to_bib(output_dir=src_folder, filename=r.citation_key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process .bib files in the specified directory.")
    parser.add_argument('src_folder', type=str, help='The source folder containing the src.bib file')

    args = parser.parse_args()

    # Ensure the source folder and the bib file exists before proceeding
    bib_file = f"{args.src_folder}/src.bib"
    if not os.path.exists(args.src_folder):
        print("The specified source folder does not exist.")
    elif not os.path.exists(bib_file):
        print("The src.bib file does not exist in the specified folder.")
    else:
        process_bibtex(args.src_folder)
