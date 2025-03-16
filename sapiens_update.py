import glob
from losalamos.zion import Sapiens
import argparse


def update(note_file):
    # load note
    n = Sapiens()
    n.file_note = note_file
    n.load()

    # update only head
    n.update_head()

    # save
    n.save()

    file_name = n.metadata["name"]
    print(f"--- updated: {file_name}")

    return None


def main(lib_folder):
    print(f"\n--- Updating sapiens from: {lib_folder}")

    # get list of files
    ls_files = glob.glob(f"{lib_folder}/*.md")

    # run all
    for f in ls_files:
        update(note_file=f)

    print("\n ok.")
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update sapiens notes")
    parser.add_argument(
        "--lib_folder",
        type=str,
        required=True,
        help="Path to the folder where sapiens notes are expected.",
    )
    args = parser.parse_args()
    main(lib_folder=args.lib_folder)