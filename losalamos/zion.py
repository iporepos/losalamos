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
            "edu_background",
            "affiliation_pro",
            "affiliation_edu",
            #"abstract"
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
        #print(self.metadata)
        for tf in self.text_fields:
            self.metadata[tf] = '"{}"'.format(self.metadata[tf])


if __name__ == "__main__":

    print("hello world!")