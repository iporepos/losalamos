import os, glob
from losalamos.refs import Ref
import argparse

def get_subdirs(src_folder):
    # get list of valid subdirs in src folder
    lst_dirs = [
        d for d in os.listdir(src_folder)
        if os.path.isdir(os.path.join(src_folder, d)) and not d.startswith("_")
    ]
    return lst_dirs
def add(src_folder, lib_folder, template_folder, tags):
    lst_files = Ref.catalog_files(src_folder)
    if len(lst_files) == 0:
        print(f"--- no refs found\n")
        pass
    else:
        print("--- batching {} new refs from {} ...\n".format(len(lst_files), src_folder))
        # Add batch
        Ref.add_bat(
            src_folder=src_folder,
            lib_folder=lib_folder,
            template_folder=template_folder,
            tags=tags,
            related=None,
            clean=True,
        )
        print("\n--- OK")
    return None

def main(src_folder, lib_folder, template_folder):
    print(f"\n--- Adding refs from: {src_folder}")
    print(f"--- Library folder: {lib_folder}")

    # get list of valid subdirs in src folder
    lst_dirs = get_subdirs(src_folder=src_folder)

    # run for each subdir the add function
    for d in lst_dirs:
        tag = d.replace(" ", "-").lower()
        lst_tags = [tag]
        print(f"\n--- subfolder: {d} -- tag: {tag}")
        add(
            src_folder=f"{src_folder}/{d}",
            lib_folder=lib_folder,
            template_folder=template_folder,
            tags=lst_tags
        )
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Add references to library")
    parser.add_argument(
        '--src_folder',
        type=str,
        required=True,
        help="Path to the source folder containing references."
    )
    parser.add_argument(
        '--lib_folder',
        type=str,
        required=True,
        help="Path to the library folder where references will be added."
    )
    parser.add_argument(
        '--template_folder',
        type=str,
        required=True,
        help="Path to the folder of the note template file."
    )

    args = parser.parse_args()
    main(
        src_folder=args.src_folder,
        lib_folder=args.lib_folder,
        template_folder=args.template_folder,
    )