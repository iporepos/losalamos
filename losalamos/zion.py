from losalamos.root import Note


class Sapiens(Note):

    def __init__(self, name="MyNote", alias="Nt1"):
        super().__init__(name, alias)
        self.metadata = {
            "tags": None,
            "aliases": None,
            "name": None,
            "email": None,
            "email_pro": None,
            "phone": None,
            "place": None,
            "abstract": None,
            "edu_background": None,
            "degree": None,
            "profession": None,
            "affiliation_edu": None,
            "affiliation_pro": None,
            "address": None,
            "lattes": None,
            "orcid": None,
            "website": None,
            "cpf": None,
            "nit": None,
            "father": None,
            "mother": None,
            "date_birth": None,
            "bank_info": None,
            "github": None,
            "linkedin": None,
            "researchgate": None,
            "instagram": None,
            "facebook": None,
            "timestamp": None,
        }
        self.text_fields = [
            "place",
            "abstract",
            "edu_background",
            "affiliation_pro",
            "affiliation_edu",
            "address",
            # "abstract"
        ]
        self.photo = False

    def load_metadata(self):
        incoming_metadata = Note.parse_metadata(self.file_note)
        expected_fields = list(self.metadata.keys())
        filtered_metadata = {}
        for k in self.metadata:
            if k in expected_fields:
                filtered_metadata[k] = incoming_metadata[k]
        self.metadata.update(filtered_metadata)
        # print(self.metadata)
        for tf in self.text_fields:
            self.metadata[tf] = '"{}"'.format(self.metadata[tf])

    def update_data(self):
        """Updates all standard sections of the data structure based on the metadata.

        :return: None
        """
        # update head of data
        self.update_head()
        return None

    def update_head(self):
        """Updates the head section of the data structure based on the metadata.

        :return: None
        """

        image_name = self.metadata["name"]
        title_str = self.metadata["name"]
        entry_type = "sapiens"
        abstract = self.metadata.get("abstract", "{abstract}") or "{abstract}"
        if abstract == '""':
            abstract = "{abstract}"
        head_lst = [
            "",
            f"![[{image_name}.jpg|200]]",
            "",
            entry_type.upper(),
            "",
            f"# {title_str}",
            "{}".format(self.metadata.get("email", "{email}") or "{email}"),
            "",
            "> [!Info]+ Abstract",
            f"> {abstract}",
        ]

        # overwrite head
        self.data["Head"] = head_lst[:]

        return None


if __name__ == "__main__":

    print("hello world!")
