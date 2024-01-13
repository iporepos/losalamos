"""
Classes for parsing, handling and managing documents

"""
import os
import pandas as pd
from root import DataSet, Collection


class DocTable(DataSet):

    def __init__(self, name, alias):
        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def load_data(self, file_data):
        """Load data from file. Expected to overwrite superior methods.

        :param file_data: file path to data.
        :type file_data: str
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

    def to_latex(self, filename=None, folder=None, caption=None, label=None):
        if filename is None:
            filename = self.name
        if folder is None:
            folder = self.folder_data
        list_bulk = list()
        # preable
        list_bulk.append(r"% Insert Table")
        list_bulk.append(r"\begin{table}[t]")
        list_bulk.append(r"\centering")
        list_bulk.append(r"\tiny")
        list_bulk.append(r"\rowcolors{2}{white}{rowgray}")
        # heading
        str_aux = "p{1cm}" * len(self.data.columns)
        list_bulk.append(r"\begin{tabular}{" + str_aux + "}")
        list_bulk.append(r"\toprule")
        list_bulk.append(r"\midrule")
        list_heading = [r"\textbf{" + c + "}" for c in self.data.columns]
        str_heading = " & ".join(list_heading) + r"\\"
        list_bulk.append(str_heading)
        # data
        df = self.data.copy()
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
    dt.to_latex(
        caption="Ranges of hyperparameter values for tuning each ML model.",
        label="tab:parameters"
    )



