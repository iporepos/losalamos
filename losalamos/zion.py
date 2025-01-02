from losalamos.root import Note

class Sapiens(Note):

    def __init__(self, name="MyNote", alias="Nt1"):
        super().__init__(name, alias)
        self.metadata = {
            "tags": None,
            "aliases": None,
            "name": None,
            "date_birth": None,
            "place": None,
            "email": None,
            "phone": None,
            "edu_background": None,
            "affiliation": None,
            "address": None,
            "lattes": None,
            "orcid": None,
            "website": None,
            "cpf": None,
            "linkedin": None,
            "instagram": None,
            "facebook": None,
            "timestamp": None,
            "abstract": None
        }
        self.text_fields = [
            "place",
            "edu_background",
            "affiliation",
            #"abstract"
        ]

    def load_metadata(self):
        incoming_metadata = Note.parse_metadata(self.file_note)
        self.metadata.update(incoming_metadata)
        #print(self.metadata)
        for tf in self.text_fields:
            self.metadata[tf] = '"{}"'.format(self.metadata[tf])
