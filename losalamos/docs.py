"""
Classes for parsing, handling and managing documents

"""
import os
import pandas as pd
import re
from losalamos.root import DataSet, MbaE


class TexDoc(MbaE):

    def __init__(self, name="MyTex", alias="Tex"):
        super().__init__(name=name, alias=alias)
        self.red_blind = r"\textcolor{red}{Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed ac bibendum orci. Cras erat elit, consequat vel erat ac, tincidunt pulvinar lacus. Pellentesque vitae consectetur quam. Interdum et malesuada fames ac ante ipsum primis in faucibus}"
        # ... continues in downstream objects ... #

    @staticmethod
    def format_gls(gls_name, gls_alias, gls_descr):
        line_0 = ""
        line_1 = r"\newglossaryentry{" + gls_alias +"}"
        line_2 = "{"
        line_3 = f"\tname={gls_name},"
        line_4 = f"\tdescription={gls_descr}"
        line_5 = "}"
        return [line_0, line_1, line_2, line_3, line_4, line_5]

    @staticmethod
    def insert_newgls(tex_file, gls_name, gls_alias, gls_descr):
        new_lines = TexDoc.format_gls(gls_name, gls_alias, gls_descr)
        # Open the file in append mode
        with open(tex_file, 'a',  encoding="utf-8") as file:
            # Iterate through the list and write each line
            for line in new_lines:
                file.write(line + '\n')
        return None

    @staticmethod
    def gls_to_df(tex_file):
        # Read the file content
        with open(tex_file, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # Define a regex pattern to extract glossary entries
        pattern = re.compile(r'\\newglossaryentry\{(.*?)\}\s*{\s*name=(.*?),\s*description=\{(.*?)\}\s*}', re.DOTALL)

        # Find all matches
        matches = pattern.findall(file_content)

        # Create a DataFrame from the matches
        df = pd.DataFrame(matches, columns=['Alias', 'Name', 'Description'])
        return df

    @staticmethod
    def process_glossaries(src_file, gls_file, inplace=False):
        # Read the file content
        with open(src_file, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # Define a regex pattern to match [to do:gls >> name >> alias] and capture name and alias
        pattern = re.compile(r'\[todo:gls\s*>>\s*\\textbf\{(.*?)\}\s*>>\s*(.*?)\]', re.DOTALL)

        # Find all matches
        matches = pattern.findall(file_content)

        # Display extracted name and alias
        for name, alias in matches:
            print(f'Name: {name}')
            print(f'Alias: {alias}')
            TexDoc.insert_newgls(
                tex_file=gls_file,
                gls_name=name,
                gls_alias=alias,
                gls_descr=TexDoc().red_blind
            )

        # Replace the full expression with \gls{alias}
        replaced_content = pattern.sub(r'\\gls{\2}', file_content)

        if inplace:
            pass
        else:
            d = os.path.dirname(src_file)
            fm = os.path.basename(src_file).split(".")[0] + "_2.tex"
            src_file = os.path.join(d, fm)

        # Save the modified content back to the file
        with open(src_file, 'w', encoding='utf-8') as file:
            file.write(replaced_content)

        return None

class DocTable(DataSet):

    def __init__(self, name, alias):
        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def load_data(self, file_data):
        """Load data from file_doc. Expected to overwrite superior methods.

        :param file_data: file_doc path to data.
        :entry_type file_data: str
        :return: None
        :rtype: None
        """

        # -------------- overwrite relative path input -------------- #
        file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #

        # -------------- call loading function -------------- #
        self.data = pd.read_csv(
            file_data,
            sep=self.file_data_sep,
            dtype=str
        )


        # -------------- post-loading logic -------------- #
        for c in self.data.columns:
            self.data[c] = self.data[c].str.strip()

        return None

    @staticmethod
    def to_latex(df, filename, folder, caption=None, label=None):
        list_bulk = list()
        # preable
        list_bulk.append(r"% Insert Table")
        list_bulk.append(r"\begin{table}[t]")
        list_bulk.append(r"\centering")
        list_bulk.append(r"\tiny")
        list_bulk.append(r"\rowcolors{2}{white}{rowgray}")
        # heading
        str_aux = "p{1cm}" * len(df.columns)
        list_bulk.append(r"\begin{tabular}{" + str_aux + "}")
        list_bulk.append(r"\toprule")
        list_bulk.append(r"\midrule")
        list_heading = [r"\textbf{" + c + "}" for c in df.columns]
        str_heading = " & ".join(list_heading) + r"\\"
        list_bulk.append(str_heading)
        # data
        df.fillna(value="", inplace=True)
        for i in range(len(df)):
            row = df.values[i]
            print(row)
            str_row = " & ".join(list(row)) + r"\\"
            list_bulk.append(str_row[:])
        list_bulk.append(r"\bottomrule")
        list_bulk.append(r"\end{tabular}")
        if caption is None:
            list_bulk.append(r"\caption{Table Caption}")
        else:
            list_bulk.append(r"\caption{" + caption + "}")
        if label is None:
            list_bulk.append(r"\label{tab:label}")
        else:
            list_bulk.append(r"\label{" + label + "}")
        list_bulk.append(r"\end{table}")

        # include new line
        list_bulk = [line + "\n" for line in list_bulk]

        filepath = os.path.join(folder, filename + ".txt")
        f = open(filepath, mode="w")
        f.writelines(list_bulk)
        f.close()
        return None

    @staticmethod
    def to_rst(df, filename, folder):
        def format_row(row):
            return "| " + " | ".join(f"{x:<{max_widths[i]}}" for i, x in enumerate(row)) + " |"

        list_bulk = list()

        # header setup
        header = df.columns.tolist()
        max_widths = [max(df[col].astype(str).apply(len).max(), len(col)) for col in header]

        list_bulk.append("+" + "+".join(["-" * (w + 2) for w in max_widths]))
        list_bulk.append(format_row(header))
        list_bulk.append("+" + "+".join(["=" * (w + 2) for w in max_widths]))

        for _, row in df.iterrows():
            list_bulk.append(format_row(row))
            list_bulk.append("+" + "+".join(["-" * (w + 2) for w in max_widths]))

        # include new line
        list_bulk = [line + "\n" for line in list_bulk]

        filepath = os.path.join(folder, filename + ".txt")
        f = open(filepath, mode="w")
        f.writelines(list_bulk)
        f.close()
        return None




if __name__ == "__main__":

    f = "C:/Users/Ipo/Downloads/glossary_pt.tex"

    t = TexDoc()
    t.insert_newgls(
        tex_file=f,
        gls_name="Teste",
        gls_alias="test-t",
        gls_descr=r"\textcolor{red}{Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed ac bibendum orci. Cras erat elit, consequat vel erat ac, tincidunt pulvinar lacus. Pellentesque vitae consectetur quam. Interdum et malesuada fames ac ante ipsum primis in faucibus}"
    )

    df = TexDoc.gls_to_df(f)
    print(df.head())

    f = "C:/Users/Ipo/Downloads/glossary_teste.tex"

    f2 = "C:/Users/Ipo/Downloads/chap_hydrology.tex"
    TexDoc.process_glossaries(src_file=f2, gls_file=f, inplace=False)


