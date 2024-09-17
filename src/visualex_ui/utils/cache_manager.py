# visualex_ui/utils/cache_manager.py

from functools import lru_cache

class CacheManager:
    def __init__(self):
        self.cache = {}  # Dizionario per memorizzare i dati della cache

    @lru_cache(maxsize=32)
    def get_cached_data(self, key):
        """
        Funzione per ottenere i dati memorizzati nella cache utilizzando una chiave specifica.
        
        Args:
            key (str): La chiave per cui recuperare i dati nella cache.
        
        Returns:
            object: I dati memorizzati nella cache o None se non presenti.
        """
        return self.cache.get(key)

    def cache_data(self, key, data):
        """
        Funzione per memorizzare i dati nella cache associandoli a una chiave specifica.
        
        Args:
            key (str): La chiave con cui memorizzare i dati.
            data (object): I dati da memorizzare nella cache.
        """
        self.cache[key] = data

    def clear_cache(self):
        """
        Funzione per cancellare tutti i dati nella cache.
        """
        self.cache.clear()
