"""
Classes for parsing, handling and managing documents

"""

import os, shutil, re
import pandas as pd
from losalamos.root import DataSet, MbaE, Collection

def blind_text():
    return "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed ac bibendum orci. Cras erat elit, consequat vel erat ac, tincidunt pulvinar lacus. Pellentesque vitae consectetur quam."


class DocFig(MbaE):
    def __init__(self, name="MyFig", alias="Fig"):
        super().__init__(name=name, alias=alias)
        # setup attributes
        self.fig_id = self.name # use name by default
        self.caption = blind_text()
        self.caption_lof = blind_text()
        self.label = self.alias
        self.status_t1 = "Expected"
        self.status_t2 = "Expected"
        self.part = "Main text"
        self.figsize = "Large"
        self.playout = "Columns 1 Rows 1"
        self.descr = blind_text()
        self.fig_file = None
        self.svg_file = None
        self.thumbnail_file = None
        self.thumbnail_t1_file = None
        self.thumbnail_t2_file = None
        self.pannels_dct = None

    def _set_fields(self):
        """Set fields names"""
        super()._set_fields()
        # Attribute fields
        self.fig_id_field = "Id"
        self.caption_field = "Caption"
        self.caption_lof_field = "Caption LOF"
        self.status_t1_field = "Status Tier 1"
        self.status_t2_field = "Status Tier 2"
        self.descr_field = "Description"
        self.part_field = "Part"
        self.label_field = "Label"
        self.figsize_field = "Figure Size"
        self.playout_field = "Pannels Layout"
        self.thumbnail_t1_file_field = "Thumbnail Tier 1"
        self.thumbnail_t2_file_field = "Thumbnail Tier 2"
        # ... continues in downstream objects ... #

    def get_metadata(self):
        """Get a dictionary with object metadata.

        .. note::

            Metadata does **not** necessarily inclue all object attributes.

        :return: dictionary with all metadata
        :rtype: dict
        """
        dict_meta = super().get_metadata()

        # add new fields
        dict_meta[self.fig_id_field] = self.fig_id
        dict_meta[self.label_field] = self.label
        dict_meta[self.caption_field] = self.caption
        dict_meta[self.caption_lof_field] = self.caption_lof
        dict_meta[self.status_t1_field] = self.status_t1
        dict_meta[self.status_t2_field] = self.status_t2
        dict_meta[self.descr_field] = self.descr
        dict_meta[self.part_field] = self.part
        dict_meta[self.figsize_field] = self.figsize
        dict_meta[self.playout_field] = self.playout
        dict_meta[self.thumbnail_t1_file_field] = self.thumbnail_t1_file
        dict_meta[self.thumbnail_t2_file_field] = self.thumbnail_t2_file

        return dict_meta

    def to_latex(self, folder=None, filename=None, position="h!", fontsize="scriptsize", fontfamily="sffamily", wfactor=0.95):
        """Generates a LaTeX figure environment containing an image and its corresponding caption,
        and saves it as a `.tex` file if folder and filename is provided.

        :param folder: The directory where the LaTeX file will be saved.
        :type folder: str, optional
        :param filename: The name of the LaTeX file (without extension).
        :type filename: str, optional
        :param position: The positioning argument for the LaTeX figure environment (e.g., "h!", "t", "b").
        :type position: str, optional
        :param fontsize: The font size command to be used (e.g., "scriptsize", "footnotesize").
        :type fontsize: str, optional
        :param fontfamily: The font family command to be used (e.g., "sffamily", "rmfamily").
        :type fontfamily: str, optional
        :param wfactor: The width factor for scaling the included image relative to text width.
        :type wfactor: float, optional
        :return: A list of strings representing the lines of the generated LaTeX figure environment.
        :rtype: list[str]
        """
        list_bulk = list()
        # preable
        list_bulk.append(r"\begin{figure}["+ position + "]")
        list_bulk.append(r"\centering")
        list_bulk.append(r"\{}".format(fontsize) )
        list_bulk.append(r"\{}".format(fontfamily))

        # image
        list_bulk.append(r"\includegraphics[width={}\textwidth]".format(wfactor) + "{" + os.path.basename(self.fig_file) + "}")
        list_bulk.append(r"\caption[" + self.caption_lof + "]{" + self.caption + "}")
        list_bulk.append(r"\label{" + self.label + "}")
        list_bulk.append(r"\end{figure}")

        # include new line
        list_bulk = [line + "\n" for line in list_bulk]

        # export
        if folder and filename:
            filepath = os.path.join(folder, filename + ".tex")
            f = open(filepath, mode="w", encoding="utf-8")
            f.writelines(list_bulk)
            f.close()

        return list_bulk

    def to_latex_report(self, template_file, folder=None, filename=None):
        """Generates a LaTeX report based on a template file, replacing placeholders with
        instance attributes and optionally saving the output to a `.tex` file.

        :param template_file: Path to the LaTeX template file containing placeholders.
        :type template_file: str
        :param folder: Directory where the output LaTeX file should be saved (optional).
        :type folder: str, optional
        :param filename: Name of the output LaTeX file (without extension) (optional).
        :type filename: str, optional
        :return: A list of strings representing the lines of the generated LaTeX report.
        :rtype: list[str]
        """

        # open the template
        fle = open(file=template_file, encoding="utf-8", mode="r")
        list_bulk = fle.readlines()
        fle.close()

        # handle colors
        dct_status = {
            "Expected": r"\textcolor{red}{Expected}",
            "Concluded": r"\textcolor{YellowOrange}{In progress}",
            "Concluded": r"\textcolor{OliveGreen}{Concluded}",
        }

        # set replacer object
        dct_replacer = {
            "[{}]".format(self.label_field): self.label,
            "[{}]".format(self.name_field): self.name,
            "[{}]".format(self.part_field): self.part,
            "[{}]".format(self.descr_field): self.descr,
            "[{}]".format(self.caption_field): self.caption,
            "[figt1sts]": dct_status[self.status_t1],
            "[figt2sts]": dct_status[self.status_t2],
            "[{}]".format(self.thumbnail_t1_file_field): self.thumbnail_t1_file if self.thumbnail_t1_file is not None else "example-image",
            "[{}]".format(self.thumbnail_t2_file_field): self.thumbnail_t2_file if self.thumbnail_t1_file is not None else "example-image",
        }

        # loop for replace itens in placeholders
        for k in dct_replacer:
            for i in range(len(list_bulk)):
                list_bulk[i] = list_bulk[i].replace(k, dct_replacer[k])[:]

        # handle pannel list
        if self.pannels_dct is not None:
            list_bulk.append("\n\n")
            list_bulk.append(r"\noindent \textbf{Pannels}" + "\n")
            list_bulk.append(r"\begin{itemize}" + "\n")
            for k in self.pannels_dct:
                s_aux = r"    \item Pannel \textbf{" + k + "}: " + self.pannels_dct[k] + ";" + "\n"
                list_bulk.append(s_aux)
            list_bulk.append(r"\end{itemize}" + "\n")

        # new page
        list_bulk.append("\n")
        list_bulk.append(r"\clearpage" + "\n")
        list_bulk.append("\n")

        # export
        if folder and filename:
            filepath = os.path.join(folder, filename + ".tex")
            f = open(filepath, mode="w", encoding="utf-8")
            f.writelines(list_bulk)
            f.close()

        return list_bulk


class DocFigColl(Collection):

    def __init__(self):
        super().__init__(base_object=DocFig, name="MyFigColl", alias="FigCol0")

    def load_catalog(self, df_file):
        df = pd.read_csv(df_file, sep=";")
        for i in range(len(df)):
            _NewFig= DocFig()
            _NewFig.name = df[_NewFig.name_field].values[i]
            _NewFig.alias = df[_NewFig.alias_field].values[i]
            _NewFig.fig_id = df[_NewFig.fig_id_field].values[i]
            _NewFig.caption = df[_NewFig.caption_field].values[i]
            _NewFig.caption_lof = df[_NewFig.caption_lof_field].values[i]
            _NewFig.status_t1 = df[_NewFig.status_t1_field].values[i]
            _NewFig.status_t2 = df[_NewFig.status_t2_field].values[i]
            _NewFig.descr = df[_NewFig.descr_field].values[i]
            _NewFig.part = df[_NewFig.part_field].values[i]
            _NewFig.figsize = df[_NewFig.figsize_field].values[i]
            _NewFig.playout = df[_NewFig.playout_field].values[i]
            _NewFig.label = df[_NewFig.label_field].values[i]
            _NewFig.thumbnail_t1_file = df[_NewFig.thumbnail_t1_file_field].values[i]
            _NewFig.thumbnail_t2_file = df[_NewFig.thumbnail_t2_file_field].values[i]

            self.append(new_object=_NewFig)


class DocTex(MbaE):

    def __init__(self, name="MyTex", alias="Tex"):
        super().__init__(name=name, alias=alias)
        self.red_blind = r"\textcolor{red}{Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed ac bibendum orci. Cras erat elit, consequat vel erat ac, tincidunt pulvinar lacus. Pellentesque vitae consectetur quam. Interdum et malesuada fames ac ante ipsum primis in faucibus}"
        # ... continues in downstream objects ... #

    @staticmethod
    def gls_format(gls_name, gls_alias, gls_descr=None):
        """Format a glossary entry

        :param gls_name: entry name
        :type gls_name: str
        :param gls_alias: entry alias (key)
        :type gls_alias: str
        :param gls_descr: entry description (if None, a blind text is iserted)
        :type gls_descr: str
        :return: list of lines to append to main file
        :rtype: list
        """
        line_0 = ""
        line_1 = r"\newglossaryentry{" + gls_alias + "}"
        line_2 = "{"
        line_3 = f"\tname={gls_name},"
        if gls_descr is None:
            gls_descr = DocTex().red_blind
        line_4 = "\tdescription={" + gls_descr + "}"
        line_5 = "}"
        return [line_0, line_1, line_2, line_3, line_4, line_5]

    @staticmethod
    def gls_newentry(gls_file, gls_name, gls_alias, gls_descr=None):
        """Insert new glossary entry into a glossary file

        :param gls_file: path to glossary file
        :type gls_file: str
        :param gls_name: entry name
        :type gls_name: str
        :param gls_alias: entry alias (key)
        :type gls_alias: str
        :param gls_descr: entry description (if None, a blind text is iserted)
        :type gls_descr: str
        :return: None
        :rtype: None
        """
        # get formatted entry in list
        new_lines = DocTex.gls_format(gls_name, gls_alias, gls_descr)
        # Open the file in append mode
        with open(gls_file, "a", encoding="utf-8") as file:
            # Iterate through the list and write each line
            for line in new_lines:
                file.write(line + "\n")
        return None

    @staticmethod
    def gls_to_df(gls_dct):
        """convert a glossary dict in a dataframe

        :param gls_dct: glossary dict
        :type gls_dct: dict
        :return: dataframe of glossary
        :rtype: `pandas.DataFrame`
        """
        alias_ls = []
        name_ls = []
        descr_ls = []
        for e in gls_dct:
            alias_ls.append(e)
            name_ls.append(gls_dct[e]["name"])
            descr_ls.append(gls_dct[e]["description"])

        # Create a DataFrame from the matches
        df = pd.DataFrame({"Alias": alias_ls, "Name": name_ls, "Description": descr_ls})
        return df

    @staticmethod
    def gls_parse(gls_file):
        # Read the file content
        with open(gls_file, "r", encoding="utf-8") as file:
            file_content = file.read()

        # Define a regex pattern to extract glossary entries
        pattern = re.compile(
            r"\\newglossaryentry\{(.*?)\}\s*{\s*name=(.*?),\s*description=\{(.*?)\}\s*}",
            re.DOTALL,
        )

        # Find all matches
        matches = pattern.findall(file_content)
        # create dict
        gls_dct = {}
        for e in matches:
            gls_dct[e[0]] = {"name": e[1], "description": e[2]}
        return gls_dct

    @staticmethod
    def gls_to_file(gls_dct, filename, output_dir):
        """Export glossary to new tex file

        :param gls_dct: glossary dict
        :type gls_dct: dict
        :param filename: name of file (without extension)
        :type filename: str
        :param output_dir: path to output folder
        :type output_dir: str
        :return: file path
        :rtype: str
        """
        # set the output file
        gls_file = os.path.join(output_dir, filename + ".tex")

        # create a new glossary file
        header_ls = ["\makeglossaries", "\n"]
        with open(gls_file, "w", encoding="utf-8") as file:
            file.writelines(header_ls)

        for alias in gls_dct:
            DocTex.gls_newentry(
                gls_file=gls_file,
                gls_alias=alias,
                gls_name=gls_dct[alias]["name"],
                gls_descr=gls_dct[alias]["description"],
            )

        return gls_file

    @staticmethod
    def gls_consolidate(src_file, gls_file, inplace=True):
        """Process a source tex file to consolidate the glossaries file (append new entries).
        Expected pattern in source file: [todo:gls >> \textbf{gls_name} >> gls_alias]

        :param src_file: path to source tex file
        :type src_file: str
        :param gls_file: path to glossary tex file
        :type gls_file: str
        :param inplace: option for overwrite the source file
        :type inplace: bool
        :return:
        :rtype:
        """
        # Read the file content
        with open(src_file, "r", encoding="utf-8") as file:
            file_content = file.read()

        # Define a regex pattern to match [to do:gls >> name >> alias] and capture name and alias
        pattern = re.compile(
            r"\[todo:gls\s*>>\s*\\textbf\{(.*?)\}\s*>>\s*(.*?)\]", re.DOTALL
        )

        # Find all matches
        matches = pattern.findall(file_content)

        # append entries
        for name, alias in matches:
            DocTex.gls_newentry(
                gls_file=gls_file,
                gls_name=name,
                gls_alias=alias,
                gls_descr=DocTex().red_blind,  # defaults to blind text
            )

        # Replace the full expression with \gls{alias}
        replaced_content = pattern.sub(r"\\textbf{\\gls{\2}}", file_content)

        # handle file
        if inplace:
            pass
        else:
            # re set the source file path
            d = os.path.dirname(src_file)
            fm = os.path.basename(src_file).split(".")[0] + "_2.tex"
            src_file = os.path.join(d, fm)

        # Save the modified content back to the file
        with open(src_file, "w", encoding="utf-8") as file:
            file.write(replaced_content)

        return None

    @staticmethod
    def gls_expand(src_file, gls_file, inplace=True):
        # parse file
        gls_dct = DocTex.gls_parse(gls_file=gls_file)
        # get df
        gls_df = DocTex.gls_to_df(gls_dct=gls_dct)
        # get helper column
        gls_df["LenName"] = [len(s) for s in gls_df["Name"].values]
        # sort
        gls_df = gls_df.sort_values(by="LenName", ascending=False).reset_index(
            drop=True
        )
        # inset helper column
        gls_df["NewExp"] = ["\gls{" + s + "}" for s in gls_df["Alias"]]

        # handle new files
        if not inplace:
            # make copy and rename
            _d = os.path.dirname(src_file)
            _f = os.path.basename(src_file)
            _f = _f.split(".")[0] + "_2." + _f.split(".")[1]
            shutil.copy(src=src_file, dst=os.path.join(_d, _f))
            src_file = os.path.join(_d, _f)

        # replace all items
        for i in range(len(gls_df)):
            # ensure not re-replace
            # suffix list
            suffs_ls = [" ", ",", ";", ".", ":", "!", "?"]
            old_ls = [gls_df["Name"].values[i] + s for s in suffs_ls]
            new_ls = [gls_df["NewExp"].values[i] + s for s in suffs_ls]
            # run for all suffixes
            for j in range(len(old_ls)):
                DocTex.replace_infile(
                    src_file=src_file,
                    old_expression=old_ls[j],
                    new_expression=new_ls[j],
                    inplace=True,
                )

        return src_file

    @staticmethod
    def replace_infile(src_file, old_expression, new_expression, inplace=True):
        """Replace expression directly in file
        todo evaluate move this upstream

        :param src_file: path to file (tex, md, etc)
        :type src_file: str
        :param old_expression: text of expression to be replaced
        :type old_expression: str
        :param new_expression: new expression
        :type new_expression: str
        :return: None
        :rtype: None
        """
        with open(src_file, "r", encoding="utf-8") as file:
            content = file.read()

        new_content = content.replace(old_expression, new_expression)

        if inplace:
            pass
        else:
            # re set the source file path
            d = os.path.dirname(src_file)
            bse_ls = os.path.basename(src_file).split(".")
            fm = bse_ls[0] + "_2." + bse_ls[1]
            src_file = os.path.join(d, fm)

        with open(src_file, "w", encoding="utf-8") as file:
            file.write(new_content)

        if not inplace:
            return src_file
        else:
            return None

    @staticmethod
    def get_authors(src_table, dst_folder=None):
        df = pd.read_csv(src_table, sep=";")
        df = df.sort_values(by="Order")

        # Handle affiliations
        lst_institutes = df["Affiliation"].unique()
        d_inst = {}
        lst_affs = []
        for i in range(len(lst_institutes)):
            _code = str(chr(96 + i + 1))
            d_inst[lst_institutes[i]] = _code
            s = r"$^\text{" + _code + "}$\;" + lst_institutes[i]
            lst_affs.append(s)
        authors_affs = r" \newline ".join(lst_affs)

        # Handle list
        lst_authors = []
        for i in range(len(df)):
            _nm = df["Name"].values[i]
            _af = df["Affiliation"].values[i]
            _oi = df["OrcID"].values[i]
            _ex = d_inst[_af]
            s = "\href{" + _oi + "}{" + _nm + r"}\,$^\text{" + _ex + "}$"
            lst_authors.append(s)
        authors_list = ",\;".join(lst_authors)

        # Handle corresponding
        df_corr = df.query("Corresponding == 'yes'").copy()
        _nm = df_corr["Name"].values[0]
        _em = df_corr["Email"].values[0]
        authors_corr = (
            "Corresponding author: {"
            + _nm
            + r"} (\href{mailto:"
            + _em
            + r"}{"
            + _em
            + "})"
        )

        # Handle credits
        lst_credits = []
        for i in range(len(df)):
            _nm = df["Name"].values[i]
            _cr = df["Credit"].values[i]
            s = r"\textbf{" + _nm + "}: " + _cr + ". "
            lst_credits.append(s)
        authors_credit = "".join(lst_credits)

        # export
        if dst_folder:
            with open(f"{dst_folder}/authors_list.tex", "w", encoding="utf-8") as file:
                file.write(authors_list + "\n")
            with open(f"{dst_folder}/authors_affs.tex", "w", encoding="utf-8") as file:
                file.write(authors_affs + "\n")
            with open(f"{dst_folder}/authors_corr.tex", "w", encoding="utf-8") as file:
                file.write(authors_corr + "\n")
            with open(
                f"{dst_folder}/authors_credit.tex", "w", encoding="utf-8"
            ) as file:
                file.write(authors_credit + "\n")

        return None

    @staticmethod
    def get_team(src_table, dst_folder=None):
        df = pd.read_csv(src_table, sep=";")
        df = df.sort_values(by="Order")

        ls_std = [
            r"\noindent \sffamily \large{\textbf{@name}} \rmfamily\\ [3mm]",
            r"\small{",
            r"\href{mailto:@email}{@email} | @phone \\",
            r"@profession | @education \\",
            r"@jobtitle \\",
            r"\href{@cv}{@cv} \\ [3mm]",
            r"}",
            r"@credit \\",
            "\n\n",
        ]

        team_list = []

        for i in range(len(df)):
            # get the dict
            d = {
                "@name": df["Name"].values[i],
                "@phone": df["Phone"].values[i],
                "@email": df["Email"].values[i],
                "@profession": df["Profession"].values[i],
                "@education": df["Education"].values[i],
                "@jobtitle": df["Jobtitle"].values[i],
                "@credit": df["Credit"].values[i],
                "@cv": df["CV"].values[i],
            }
            print(d)
            lst_new = ls_std.copy()
            for j in range(len(lst_new)):
                for k in d:
                    lst_new[j] = lst_new[j].replace(k, d[k])
            team_list = team_list + lst_new[:]

        # export
        if dst_folder:
            with open(f"{dst_folder}/team_list.tex", "w", encoding="utf-8") as file:
                file.writelines(team_list)

        return None

class DocTable(DataSet):

    def __init__(self, name, alias):
        super().__init__(name=name, alias=alias)
        # ... continues in downstream objects ... #

    def load_data(self, file_data):
        """Load data from file. Expected to overwrite superior methods.

        :param file_data: file_doc path to data.
        :entry_type file_data: str
        :return: None
        :rtype: None
        """

        # -------------- overwrite relative path input -------------- #
        file_data = os.path.abspath(file_data)

        # -------------- implement loading logic -------------- #

        # -------------- call loading function -------------- #
        self.data = pd.read_csv(file_data, sep=self.file_data_sep, dtype=str)

        # -------------- post-loading logic -------------- #
        for c in self.data.columns:
            self.data[c] = self.data[c].str.strip()

        return None

    @staticmethod
    def to_latex(
        df, caption=None, caption_lot=None, label=None, filename=None, folder=None
    ):
        """Convert a DataFrame to a LaTeX table and save it as a .tex file in the specified folder.

        :param df: DataFrame to be converted to LaTeX format.
        :type df: pandas.DataFrame
        :param filename: The name of the file to save the LaTeX table as (without the extension).
        :type filename: str
        :param folder: The path to the folder where the .tex file will be saved.
        :type folder: str
        :param caption: The caption for the table. Defaults to a placeholder caption if None.
        :type caption: Optional[str]
        :param caption_lot: The List of Tables caption. Defaults to a placeholder caption if None.
        :type caption_lot: Optional[str]
        :param label: The LaTeX label to be used for referencing the table. Defaults to 'tab:label' if None.
        :type label: Optional[str]
        :return: None
        :rtype: None
        """

        # handle width
        w_len = len(df.columns)
        _f = str(round(1 / w_len, 1))

        list_bulk = list()
        # preable
        list_bulk.append(r"\begin{table}[h!]")
        list_bulk.append(r"\centering")
        list_bulk.append(r"\tiny")
        list_bulk.append(r"\sffamily")
        # caption
        if caption is None:
            caption = "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip."
        if caption_lot is None:
            caption_lot = "Duis aute irure dolor"
        list_bulk.append(r"\caption[" + caption_lot + "]{" + caption + "}")

        if label is None:
            label = "tab:label"

        list_bulk.append(r"\label{" + label + "}")

        # heading
        list_bulk.append(r"\rowcolors{2}{white}{rowgray}")
        str_aux2 = r">{\raggedright\arraybackslash}m{" + _f + r"\textwidth}"
        str_aux = str_aux2 * len(df.columns)
        list_bulk.append(r"\begin{tabular}{" + str_aux + "}")
        list_bulk.append(r"\toprule")
        list_heading = [r"\textbf{" + c + "}" for c in df.columns]
        str_heading = " & ".join(list_heading) + r"\\"
        list_bulk.append(str_heading)
        list_bulk.append(r"\midrule")

        # data
        df.fillna(value="", inplace=True)
        for i in range(len(df)):
            row = df.values[i]

            str_row = " & ".join(list(row)) + r"\\"
            # handle underscores
            str_row = str_row.replace("_", "\_")

            list_bulk.append(str_row[:])
        list_bulk.append(r"\bottomrule")
        list_bulk.append(r"\end{tabular}")
        list_bulk.append(r"\end{table}")

        # include new line
        list_bulk = [line + "\n" for line in list_bulk]

        if folder and filename:
            filepath = os.path.join(folder, filename + ".tex")
            f = open(filepath, mode="w", encoding="utf-8")
            f.writelines(list_bulk)
            f.close()
        return list_bulk

    @staticmethod
    def to_rst(df, filename, folder):
        def format_row(row):
            return (
                "| "
                + " | ".join(f"{x:<{max_widths[i]}}" for i, x in enumerate(row))
                + " |"
            )

        list_bulk = list()

        # header setup
        header = df.columns.tolist()
        max_widths = [
            max(df[col].astype(str).apply(len).max(), len(col)) for col in header
        ]

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

    d = "C:/Users/Ipo/My Drive/athens/losalamos/B000/B008_paper-dma/inputs"
    DocTex.get_authors(src_table=f"{d}/authors.csv", dst_folder=d)
