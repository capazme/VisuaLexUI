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

    def __init__(self, url, payload, endpoint_type):
        super().__init__()
        self.url = url
        self.payload = payload
        self.endpoint_type = endpoint_type  # Tipo di endpoint per decidere quale chiamata effettuare
        self.max_retries = 3  # Numero massimo di tentativi
        self.timeout = 1000  # Timeout per le richieste in secondi

    def run(self):
        attempts = 0
        while attempts < self.max_retries:
            try:
                logging.info(f"Tentativo {attempts + 1} di inviare la richiesta a {self.url} con payload: {self.payload}")
                response = requests.post(self.url, json=self.payload, timeout=self.timeout)
                response.raise_for_status()  # Lancia un'eccezione per codici di stato HTTP 4xx/5xx
                logging.info(f"Richiesta riuscita al tentativo {attempts + 1}. Status code: {response.status_code}")
                data = response.json()
                logging.debug(f"Dati ricevuti: {data}")

                if self.endpoint_type == "fetch_all_data":
                    self.handle_fetch_all_data(data)
                elif self.endpoint_type == "fetch_article_text":
                    self.handle_fetch_article_text(data)
                elif self.endpoint_type == "fetch_brocardi_info":
                    self.handle_fetch_brocardi_info(data)
                elif self.endpoint_type == "fetch_normattiva_info":
                    self.handle_fetch_normattiva_info(data)
                else:
                    logging.error("Endpoint non valido specificato")
                    self.data_fetched.emit({'error': "Endpoint non valido"})

                logging.info("Richiesta completata con successo.")
                return  # Se la richiesta ha successo, esci dal metodo
            except (Timeout, ConnectionError) as e:
                attempts += 1
                logging.warning(f"Tentativo {attempts} fallito: {e}")
                backoff_time = 2 ** attempts  # Exponential backoff
                logging.info(f"Attesa di {backoff_time} secondi prima di riprovare.")
                time.sleep(backoff_time)  # Attendi per un periodo crescente
                if attempts == self.max_retries:
                    logging.error("Numero massimo di tentativi raggiunto. Impossibile connettersi al server.")
                    self.data_fetched.emit({'error': "Impossibile connettersi al server. Verifica la tua connessione internet."})
            except HTTPError as e:
                logging.error(f"Errore HTTP: {e.response.status_code}")
                self.data_fetched.emit({'error': f"Errore HTTP: {e.response.status_code}"})
                return
            except json.JSONDecodeError as e:
                logging.error("Errore nel decodificare la risposta del server.")
                self.data_fetched.emit({'error': "Errore nel decodificare la risposta del server."})
                return
            except RequestException as e:
                logging.error(f"Errore nella richiesta: {str(e)}")
                self.data_fetched.emit({'error': f"Errore nella richiesta: {str(e)}"})
                return
            except Exception as e:
                logging.error(f"Errore inaspettato: {e}")
                self.data_fetched.emit({'error': "Si è verificato un errore inaspettato."})
                return

    def handle_fetch_all_data(self, data):
        logging.info("Gestione dei dati per fetch_all_data.")
        try:
            # Se data è un dict, estrai 'response' se presente
            if isinstance(data, dict):
                if 'response' in data:
                    data = data['response']
                elif 'error' in data:
                    error_msg = data['error']
                    logging.error(f"Errore ricevuto dalla risposta dell'API: {error_msg}")
                    self.data_fetched.emit({'error': error_msg})
                    return
                else:
                    logging.error("Formato dei dati ricevuti non riconosciuto.")
                    self.data_fetched.emit({'error': "Formato dei dati ricevuti non riconosciuto."})
                    return

            if isinstance(data, list):
                normavisitate_list = []
                for item in data:
                    logging.debug(f"Processando item: {item}")
                    normavisitata = NormaVisitata.from_dict(item['norma_data'])
                    normavisitata._article_text = item.get('article_text', '')
                    normavisitata._brocardi_info = item.get('brocardi_info', {})
                    normavisitate_list.append(normavisitata)

                logging.info("Dati fetch_all_data elaborati con successo.")
                self.data_fetched.emit(normavisitate_list)
            else:
                logging.error("Formato dei dati ricevuti non riconosciuto.")
                self.data_fetched.emit({'error': "Formato dei dati ricevuti non riconosciuto."})
        except Exception as e:
            logging.error(f"Errore inaspettato: {e}")
            self.data_fetched.emit({'error': "Si è verificato un errore inaspettato."})


    def handle_fetch_article_text(self, data):
        logging.info("Gestione dei dati per fetch_article_text.")
        if isinstance(data, list):
            results = []
            for item in data:
                logging.debug(f"Processando item: {item}")
                normavisitata = NormaVisitata.from_dict(item['norma_data'])
                normavisitata._article_text = item.get('article_text', '')
                results.append(normavisitata)
            logging.info("Dati fetch_article_text elaborati con successo.")
            self.data_fetched.emit(results)
        else:
            error_msg = data.get('error', "Errore nella risposta dell'API.")
            logging.error(f"Errore ricevuto dalla risposta dell'API: {error_msg}")
            self.data_fetched.emit({'error': error_msg})

    def handle_fetch_brocardi_info(self, data):
        logging.info("Gestione dei dati per fetch_brocardi_info.")
        if isinstance(data, list):
            results = []
            for item in data:
                logging.debug(f"Processando item: {item}")
                normavisitata = NormaVisitata.from_dict(item['norma_data'])
                normavisitata._brocardi_info = item.get('brocardi_info', {})
                results.append(normavisitata)
            logging.info("Dati fetch_brocardi_info elaborati con successo.")
            self.data_fetched.emit(results)
        else:
            error_msg = data.get('error', "Errore nella risposta dell'API.")
            logging.error(f"Errore ricevuto dalla risposta dell'API: {error_msg}")
            self.data_fetched.emit({'error': error_msg})

    def handle_fetch_normattiva_info(self, data):
        logging.info("Gestione dei dati per fetch_normattiva_info.")
        if isinstance(data, list):
            results = []
            for item in data:
                logging.debug(f"Processando item: {item}")
                normavisitata = NormaVisitata.from_dict(item['norma_data'])
                normavisitata._normattiva_info = item.get('normattiva_info', {})
                results.append(normavisitata)
            logging.info("Dati fetch_normattiva_info elaborati con successo.")
            self.data_fetched.emit(results)
        else:
            error_msg = data.get('error', "Errore nella risposta dell'API.")
            logging.error(f"Errore ricevuto dalla risposta dell'API: {error_msg}")
            self.data_fetched.emit({'error': error_msg})
