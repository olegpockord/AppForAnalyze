from .bib import BibTexTemplate
from .ris import RisTemplate
from .enw import EnwTemplate
from .csljson import CSLJsonTemplate

FORMATTERS = {
    "BibTex": BibTexTemplate,
    "Ris": RisTemplate,
    "EndNote": EnwTemplate,
    "CSLJson": CSLJsonTemplate,
}