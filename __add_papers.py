import os, glob
from losalamos.refs import Ref
import argparse

def get_relatead(src_folder):
    fle = open(file=f"{src_folder}/related.txt", mode="r", encoding="utf8")
    lst_1 = fle.readlines()
    fle.close()
    lst_2 = [line.split("\n")[0] for line in lst_1]
    return lst_2

def get_tags(src_folder):
    fle = open(file=f"{src_folder}/tags.txt", mode="r", encoding="utf8")
    lst_1 = fle.readlines()
    fle.close()
    lst_2 = [line.split("\n")[0] for line in lst_1]
    return lst_2


def add_papers(src_folder, lib_folder, template):
    lst_related = get_relatead(src_folder=src_folder)
    lst_tags = get_tags(src_folder=src_folder)
    print("batching new refs...")
    # Add batch
    Ref.add_bat(
        lib_folder=lib_folder,
        input_folder=src_folder,
        note_template=template,
        tags=lst_tags,
        related=lst_related
    )
    print("OK.")

def main(src_folder, lib_folder, template):
    lst_dirs = [
        d for d in os.listdir(src_folder)
        if os.path.isdir(os.path.join(src_folder, d)) and not d.startswith("_")
    ]
    for d in lst_dirs:
        add_papers(
            src_folder=f"{src_folder}/{d}",
            lib_folder=lib_folder,
            template=template,
        )



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Batch add papers to library.")
    parser.add_argument(
        '--src_folder',
        type=str,
        required=True,
        help="Path to the source folder containing papers."
    )
    parser.add_argument(
        '--lib_folder',
        type=str,
        required=True,
        help="Path to the library folder where papers will be added."
    )
    parser.add_argument(
        '--template',
        type=str,
        required=True,
        help="Path to the note template file."
    )

    args = parser.parse_args()
    main(
        src_folder=args.src_folder,
        lib_folder=args.lib_folder,
        template=args.template,
    )