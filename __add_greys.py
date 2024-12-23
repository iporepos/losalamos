import os, glob
from losalamos.refs import Ref
import argparse

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
            clean=True
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
            lib_folder=f"{lib_folder}",
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