"""
Classes for parsing, handling and managing documents

"""
import os
import pandas as pd
from losalamos.root import DataSet


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

    dt = DocTable(name="datasets", alias="ds")
    dt.file_data_sep = ","

    d = {
        "Name": "parameters",
        "Alias": "prm",
        "Color": "red",
        "File_Data": "../ml_pipeline/data/model_parameters.csv",
        "Souce": "",
        "Description": ""
    }

    dt.set(dict_setter=d, load_data=True)

    print(dt)
    #dt.update()
    dt.to_rst(
        df=dt.data,
        filename="teste",
        folder="C:/data"
    )



