import os
import time

import psutil
from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from app.modello import analizza_testo, carica_modello

CARTELLA_PROGETTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERCORSO_MODELLO = os.path.join(CARTELLA_PROGETTO, "modelli", "sentiment_analysis_model.pkl")

TIPI_ERRORE = ("input_non_valido", "errore_modello")


def crea_app(modello=None):
    app = Flask(__name__)

    if modello is None:
        modello = carica_modello(os.environ.get("MODELLO_PERCORSO", PERCORSO_MODELLO))

    # Ogni app ha un registro suo, cosi i test possono crearne piu di una
    registro = CollectorRegistry()

    richieste = Counter(
        "sentiment_richieste",
        "Numero di richieste ricevute",
        ["endpoint", "metodo", "stato"],
        registry=registro,
    )
    durata_richieste = Histogram(
        "sentiment_durata_richieste_secondi",
        "Tempo di risposta delle richieste in secondi",
        ["endpoint"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
        registry=registro,
    )
    errori_predizione = Counter(
        "sentiment_errori_predizione",
        "Numero di richieste di predizione fallite",
        ["tipo"],
        registry=registro,
    )
    predizioni = Counter(
        "sentiment_predizioni",
        "Numero di predizioni per sentimento",
        ["sentimento"],
        registry=registro,
    )
    confidenza_predizioni = Histogram(
        "sentiment_confidenza",
        "Distribuzione della confidenza delle predizioni",
        buckets=(0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
        registry=registro,
    )

    processo = psutil.Process()
    processo.cpu_percent(interval=None)
    cpu = Gauge(
        "sentiment_cpu_percentuale",
        "Utilizzo della CPU del processo in percentuale",
        registry=registro,
    )
    cpu.set_function(lambda: processo.cpu_percent(interval=None))
    memoria = Gauge(
        "sentiment_memoria_byte",
        "Memoria residente usata dal processo in byte",
        registry=registro,
    )
    memoria.set_function(lambda: processo.memory_info().rss)

    for tipo in TIPI_ERRORE:
        errori_predizione.labels(tipo)
    for classe in getattr(modello, "classes_", []):
        predizioni.labels(str(classe))

    @app.before_request
    def inizio_richiesta():
        g.inizio = time.perf_counter()

    @app.after_request
    def fine_richiesta(risposta):
        endpoint = request.url_rule.rule if request.url_rule else "non_trovato"
        durata = time.perf_counter() - g.get("inizio", time.perf_counter())
        durata_richieste.labels(endpoint).observe(durata)
        richieste.labels(endpoint, request.method, str(risposta.status_code)).inc()
        return risposta

    @app.post("/predict")
    def predici():
        dati = request.get_json(silent=True)
        testo = dati.get("review") if isinstance(dati, dict) else None

        if not isinstance(testo, str) or not testo.strip():
            errori_predizione.labels("input_non_valido").inc()
            return jsonify(errore="Il campo 'review' e obbligatorio e deve essere un testo non vuoto"), 400

        try:
            sentimento, confidenza = analizza_testo(modello, testo)
        except Exception:
            app.logger.exception("Errore durante la predizione")
            errori_predizione.labels("errore_modello").inc()
            return jsonify(errore="Errore interno durante la predizione"), 500

        predizioni.labels(sentimento).inc()
        confidenza_predizioni.observe(confidenza)
        return jsonify(sentiment=sentimento, confidence=confidenza)

    @app.get("/metrics")
    def metriche():
        return Response(generate_latest(registro), content_type=CONTENT_TYPE_LATEST)

    @app.get("/salute")
    def salute():
        return jsonify(stato="ok")

    @app.errorhandler(404)
    def non_trovato(errore):
        return jsonify(errore="Risorsa non trovata"), 404

    @app.errorhandler(405)
    def metodo_non_consentito(errore):
        return jsonify(errore="Metodo non consentito"), 405

    return app
