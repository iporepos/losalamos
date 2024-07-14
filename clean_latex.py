import re

def process_line(line):
    # Remove \added{} expressions and extract content
    line = re.sub(r'\\added\{(.*?)\}', r'\1', line)
    # Remove \removed{} expressions and extract content
    line = re.sub(r'\\removed\{(.*?)\}', '', line)
    return line


def process_removed_block(lines):
    processed_lines = []
    inside_removed_block = False
    for line in lines:
        if '\\removed{' in line:
            inside_removed_block = True
        if not inside_removed_block:
            processed_lines.append(line)
        if "}" in line[0] and inside_removed_block:
            inside_removed_block = False
    return processed_lines
def process_added_block(lines):
    processed_lines = []
    inside_added_block = False
    skip = False
    for line in lines:
        if '\\added{' in line:
            inside_added_block = True
            skip = True
        if "}" in line[0] and inside_added_block:
            inside_added_block = False
            skip = True
        if not skip:
            processed_lines.append(line)
        skip = False
    return processed_lines

def main():
    input_filename = 'C:/data/revision_tracked.tex'
    output_filename = 'C:/data/revision_cleaned.tex'

    # Open input file for reading
    with open(input_filename, 'r', encoding="utf-8") as input_file:
        # Read lines from input file
        lines = input_file.readlines()

    # Process individual lines
    processed_lines = [process_line(line) for line in lines]

    # Process blocks of lines
    processed_lines = process_removed_block(processed_lines)
    processed_lines = process_added_block(processed_lines)

    # Open output file for writing
    with open(output_filename, 'w', encoding="utf-8") as output_file:
        # Write processed lines to output file
        output_file.writelines(processed_lines)

    print("Processing complete. Output written to", output_filename)

if __name__ == "__main__":
    main()