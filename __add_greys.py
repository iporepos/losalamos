import os, glob
from losalamos.refs import Ref
import argparse

def get_relatead(src_folder):
    related_main = os.path.basename(src_folder)
    ls_related = [related_main]
    if os.path.isfile(f"{src_folder}/related.txt"):
        fle = open(file=f"{src_folder}/related.txt", mode="r", encoding="utf8")
        lst_1 = fle.readlines()
        fle.close()
        lst_2 = [line.split("\n")[0] for line in lst_1]
        ls_related = ls_related + lst_2
    ls_related = [f"[[{s}]]" for s in ls_related]
    return ls_related

def get_tags(src_folder):
    tag_main = os.path.basename(src_folder).lower().replace(" ", "-")
    ls_tags = [tag_main]
    if os.path.isfile(f"{src_folder}/tags.txt"):
        fle = open(file=f"{src_folder}/tags.txt", mode="r", encoding="utf8")
        lst_1 = fle.readlines()
        fle.close()
        lst_2 = [line.split("\n")[0] for line in lst_1]
        ls_tags = ls_tags + lst_2
    return ls_tags

def add(src_folder, lib_folder, template):
    lst_bibs = glob.glob(f"{src_folder}/*.bib")
    if len(lst_bibs) == 0:
        pass
    else:
        print("batching new refs...")
        # Add batch
        Ref.add_bat(
            lib_folder=lib_folder,
            input_folder=src_folder,
            note_template=template,
            tags=None,
            related=None,
            clean=False
        )
        print("OK.")
    return None


def main(src_folder, lib_folder, template_folder):
    lst_dirs = [
        d for d in os.listdir(src_folder)
        if os.path.isdir(os.path.join(src_folder, d)) and not d.startswith("_")
    ]
    for d in lst_dirs:
        add(
            src_folder=f"{src_folder}/{d}",
            lib_folder=f"{lib_folder}/testes2",
            template=f"{template_folder}/_{d}.md",
        )
    return None



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Batch add greys to library.")
    parser.add_argument(
        '--src_folder',
        type=str,
        required=True,
        help="Path to the source folder containing greys."
    )
    parser.add_argument(
        '--lib_folder',
        type=str,
        required=True,
        help="Path to the library folder where greys will be added."
    )
    parser.add_argument(
        '--template_folder',
        type=str,
        required=True,
        help="Path to the template folder."
    )

    args = parser.parse_args()
    main(
        src_folder=args.src_folder,
        lib_folder=args.lib_folder,
        template_folder=args.template_folder,
    )