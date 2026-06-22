from .bib import BibTexTemplate
from .ris import RisTemplate
from .enw import EnwTemplate

FORMATTERS = {
    "BibTex": BibTexTemplate,
    "Ris": RisTemplate,
    "EndNote": EnwTemplate,
}