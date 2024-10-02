import logging
from .config import MAX_CACHE_SIZE
from functools import lru_cache
from .map import EURLEX
import requests
from bs4 import BeautifulSoup

def get_eur_uri(act_type, year, num):
    """
    Constructs the EUR-Lex URI for a given act type, year, and number.

    Arguments:
    act_type -- Type of the act (e.g., TUE, TFUE)
    year -- Year of the act
    num -- Number of the act

    Returns:
    str -- The constructed URI
    """
    logging.debug(f"Constructing URI for act_type: {act_type}, year: {year}, num: {num}")
    base_url = 'https://eur-lex.europa.eu/eli'
    uri = f'{base_url}/{act_type}/{year}/{num}/oj/ita'
    logging.info(f"Constructed URI: {uri}")
    return uri
