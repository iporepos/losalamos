import argparse
import glob
import os

from losalamos.refs import RefNote


def update(note_file):
    # load note
    n = RefNote()
    n.file_note = note_file
    n.load()

    # update only head and tail
    n.update_head()
    n.update_tail()

    # save
    n.save()
    file_name = os.path.basename(note_file)
    print(f"--- updated: {file_name}")

    return None


def main(lib_folder):
    print(f"\n--- Updating refs from: {lib_folder}")

    # get list of files
    ls_files = glob.glob(f"{lib_folder}/*.md")

    # run all
    for f in ls_files:
        update(note_file=f)

    print("\n ok.")
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update reference notes")
    parser.add_argument(
        "--lib_folder",
        type=str,
        required=True,
        help="Path to the library folder where reference notes are expected.",
    )
    args = parser.parse_args()
    main(lib_folder=args.lib_folder)
