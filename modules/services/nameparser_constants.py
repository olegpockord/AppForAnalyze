import copy
from nameparser.config import CONSTANTS

def get_extend_constants():
        C = copy.deepcopy(CONSTANTS)

        prefixes = [
            # Arabic / Semitic:
            "al", "al-", "al'", "al shaikh", "al-sheikh", "ibn", "bin", "bint", "ben",
            "abu", "abu-", "ibn al", "bint al", "ibn al-",

            # Urdu / Persian / South Asian connectors and common multiword forms:
            "ur", "ur-", "ur ", "ullah", "ulla", "khan", "khawaja", "khwaja", "zada",
            "zada-", "ullah-", "ulla-", "bhai",

            # South/SE Asian honorific connectors (often part of family-name clusters):
            "bai", "begum", "bibi", "rao", "shah", "ahmed", "singh",

            # Romance / Iberian / Latin:
            "de", "del", "de la", "de las", "de los", "dos", "das", "do", "da", "di",
            "della", "della", "d'", "d’", "du", "des", "de le",

            # Spanish multiword particles:
            "y", "y de", "y del",

            # Dutch / Flemish / Afrikaans:
            "van", "van de", "van der", "van den", "van 't", "vander", "van het",

            # Germanic / Austrian / Swiss:
            "von", "zu", "zum", "zur", "vom", "von der", "von den", "freiherr", "freifrau",

            # French:
            "le", "la", "du", "des", "de la",

            # Celtic / Gaelic:
            "mac", "mc", "o'", "o’", "fitz",

            # Italian:
            "della", "del", "d'", "de'",

            # Portuguese / Brazilian:
            "da", "das", "dos", "do", "dos santos", "dos Reis",

            # Malay / Indonesian / SE Asia:
            "bin", "binti", "bte", "bte.", "binti-", "bin-",

            # Other multiword/rare but encountered in metadata:
            "af", "al-qahtani", "al qasimi", "al farsi", "al-farsi", "de la cruz", "de la fuente",
            "van de venen", "van den berg", "van berg"
        ]

        for p in set([s.strip().lower() for s in prefixes if s and not s.isspace()]):
            C.prefixes.add(p)
        
        suffix_not_acronyms = [
        "jr", "sr", "ii", "iii", "iv", "v", "esq", "qc", "kc", "ret"
        ]

        for s in suffix_not_acronyms:
            C.suffix_not_acronyms.add(s)
        
        cap_exceptions = {
        # Romance / Dutch / Germanic
        "de": "de",
        "del": "del",
        "de la": "de la",
        "de los": "de los",
        "van": "van",
        "van der": "van der",
        "van den": "van den",
        "van 't": "van 't",
        "von": "von",
        "zu": "zu",
        "le": "le",
        "la": "la",
        "du": "du",
        "dos": "dos",
        "da": "da",
        "der": "der",
        # Arabic / South Asian
        "al": "al",
        "al-": "al-",
        "ibn": "ibn",
        "bin": "bin",
        "binti": "binti",
        "ur": "ur",
        "ullah": "ullah",
        # Celtic / Gaelic
        "mac": "mac",
        "mc": "mc",
        "o'": "o'",
        }

        C.capitalization_exceptions.update(cap_exceptions)

        return C    