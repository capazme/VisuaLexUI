# visualex_ui/network/data_fetcher.py

from PyQt6.QtCore import QThread, pyqtSignal
import requests
import logging
import time
import json
from ..tools.norma import NormaVisitata
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

class FetchDataThread(QThread):
    data_fetched = pyqtSignal(object)

    def __init__(self, url, payload):
        super().__init__()
        self.url = url
        self.payload = payload
        self.max_retries = 3  # Numero massimo di tentativi
        self.timeout = 10  # Timeout per le richieste in secondi

    def run(self):
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = requests.post(self.url, json=self.payload, timeout=self.timeout)
                response.raise_for_status()  # Lancia un'eccezione per codici di stato HTTP 4xx/5xx
                data = response.json()

                if isinstance(data, list):  # Gestiamo ora un array di risultati
                    normavisitate_list = []
                    for item in data:
                        normavisitata = NormaVisitata.from_dict(item['norma_data'])
                        normavisitata._article_text = item.get('result', '')
                        normavisitata._brocardi_info = item.get('brocardi_info', {})
                        normavisitate_list.append(normavisitata)

                    self.data_fetched.emit(normavisitate_list)  # Emit lista di risultati
                else:
                    error_msg = data.get('error', "Errore nella risposta dell'API.")
                    self.data_fetched.emit({'error': error_msg})

                logging.info("Richiesta completata con successo.")
                return  # Se la richiesta ha successo, esci dal metodo
            except (Timeout, ConnectionError) as e:
                attempts += 1
                logging.warning(f"Tentativo {attempts} fallito: {e}")
                time.sleep(2)  # Attendi 2 secondi prima di riprovare
                if attempts == self.max_retries:
                    self.data_fetched.emit({'error': "Impossibile connettersi al server. Verifica la tua connessione internet."})
            except HTTPError as e:
                self.data_fetched.emit({'error': f"Errore HTTP: {e.response.status_code}"})
                return
            except json.JSONDecodeError as e:
                self.data_fetched.emit({'error': "Errore nel decodificare la risposta del server."})
                return
            except RequestException as e:
                self.data_fetched.emit({'error': f"Errore nella richiesta: {str(e)}"})
                return
            except Exception as e:
                logging.error(f"Errore inaspettato: {e}")
                self.data_fetched.emit({'error': "Si è verificato un errore inaspettato."})
                return
