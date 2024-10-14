import re
from dataclasses import dataclass, field
from functools import lru_cache
import logging

# Moving normalize_act_type to a separate utility module to avoid circular import
from text_op import normalize_act_type  # Assuming this function is defined in a utility module
from urngenerator import generate_urn  # Assuming this function is defined elsewhere

@dataclass
class Norma:
    tipo_atto: str
    data: str = None
    numero_atto: str = None
    _url: str = None
    _tree: any = field(default=None, repr=False)

    def __post_init__(self):
        logging.debug(f"Initializing Norma with tipo_atto: {self.tipo_atto}, data: {self.data}, numero_atto: {self.numero_atto}")
        self.tipo_atto_str = normalize_act_type(self.tipo_atto, search=True)
        self.tipo_atto_urn = normalize_act_type(self.tipo_atto)
        logging.debug(f"Norma initialized: {self}")

    @property
    def url(self):
        if not self._url:
            logging.debug("Generating URL for Norma.")
            self._url = generate_urn(
                act_type=self.tipo_atto_urn,
                date=self.data,
                act_number=self.numero_atto,
                urn_flag=False
            )
        return self._url

@dataclass(eq=False)
class NormaVisitata:
    norma: Norma
    allegato: str = None
    numero_articolo: str = None
    versione: str = None
    data_versione: str = None
    _urn: str = field(default=None, repr=False)

    @property
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def urn(self):
        if not self._urn:
            logging.debug("Generating URN for NormaVisitata.")
            self._urn = generate_urn(
                act_type=self.norma.tipo_atto_urn,
                date=self.norma.data,
                act_number=self.norma.numero_atto,
                annex=self.allegato,
                article=self.numero_articolo,
                version=self.versione,
                version_date=self.data_versione
            )
        return self._urn

def parse_urn(urn):
    """
    Parses the URN and extracts the components of the legal norm.

    Arguments:
    urn -- The URN string to be parsed

    Returns:
    NormaVisitata -- An instance of NormaVisitata containing the extracted components
    """
    base_pattern = r"https://www\.normattiva\.it/uri-res/N2Ls\?urn:nir:stato:(.*)"
    match = re.match(base_pattern, urn)
    if not match:
        raise ValueError("Invalid URN format")
    
    urn_content = match.group(1)
    components = urn_content.split(":")

    tipo_atto = components[0]
    date = None
    act_number = None
    article = None
    annex = None
    version = None
    version_date = None
    
    # Extracting date and act number
    date_and_number = components[1].split(";")
    date = date_and_number[0]
    if len(date_and_number) > 1:
        act_number = date_and_number[1]
    
    # Extracting annex, article, and other optional fields
    for comp in components[2:]:
        if comp.startswith("allegato"):
            annex = comp
        elif comp.startswith("art"):
            article = comp
        elif comp.startswith("version"):
            version = comp
        elif comp.startswith("version_date"):
            version_date = comp
    
    norma = Norma(tipo_atto=tipo_atto, data=date, numero_atto=act_number)
    norma_visitata = NormaVisitata(norma=norma, allegato=annex, numero_articolo=article, versione=version, data_versione=version_date)
    
    return norma_visitata

def convert_dict_to_norma_visitata(norm_dict):
    """
    Converts a dictionary with norm names and URN specifications into a dictionary with NormaVisitata objects.

    Arguments:
    norm_dict -- A dictionary where keys are norm names and values are URN specifications

    Returns:
    dict -- A dictionary where keys are norm names and values are NormaVisitata objects
    """
    result_dict = {}
    for norm_name, urn_spec in norm_dict.items():
        urn = f"https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:{urn_spec}"
        try:
            norma_visitata = parse_urn(urn)
            result_dict[norm_name] = norma_visitata
        except ValueError as e:
            logging.error(f"Error parsing URN for {norm_name}: {e}")
    return result_dict

# Esempio di utilizzo
NORMATTIVA_URN_CODICI = {
    "costituzione": "costituzione",
    "codice penale": "regio.decreto:1930-10-19;1398:1",
    "codice di procedura civile": "regio.decreto:1940-10-28;1443:1",
    "disposizioni per l'attuazione del Codice di procedura civile e disposizioni transitorie": "regio.decreto:1941-08-25;1368:1",
    "codici penali militari di pace e di guerra": "relazione.e.regio.decreto:1941-02-20;303",
    "disposizioni di coordinamento, transitorie e di attuazione dei Codici penali militari di pace e di guerra": "regio.decreto:1941-09-09;1023",
    "codice civile": "regio.decreto:1942-03-16;262:2",
    "preleggi": "regio.decreto:1942-03-16;262:1",
    "disposizioni per l'attuazione del Codice civile e disposizioni transitorie": "regio.decreto:1942-03-30;318:1",
    "codice della navigazione": "regio.decreto:1942-03-30;327:1",
    "approvazione del Regolamento per l'esecuzione del Codice della navigazione (Navigazione marittima)": "decreto.del.presidente.della.repubblica:1952-02-15;328",
    "codice postale e delle telecomunicazioni": "decreto.del.presidente.della.repubblica:1973-03-29;156:1",
    "codice di procedura penale": "decreto.del.presidente.della.repubblica:1988-09-22;447",
}

norma_visitata_dict = convert_dict_to_norma_visitata(NORMATTIVA_URN_CODICI)
for norm_name, norma_visitata in norma_visitata_dict.items():
    print(f"{norm_name}: {norma_visitata}")