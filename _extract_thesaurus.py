def extract_code_from_markdown(markdown_file, output_file):
    with open(markdown_file, "r") as md_file:
        lines = md_file.readlines()

    code_block = False
    code_snippets = []

    for line in lines:
        if line.strip() == "```":  # Detect the start or end of a code block
            code_block = not code_block
            continue

        if code_block:
            code_snippets.append(line)

    with open(output_file, "w") as out_file:
        out_file.writelines(code_snippets)


if __name__ == "__main__":
    # Usage
    markdown_file = "_misc/thesaurus_en.md"
    output_file = "_misc/thesaurus_en.txt"
    extract_code_from_markdown(markdown_file, output_file)
