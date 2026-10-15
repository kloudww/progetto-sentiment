import numpy as np

from app.applicazione import crea_app


class ModelloRotto:
    classes_ = np.array(["negative", "neutral", "positive"])

    def predict_proba(self, testi):
        raise RuntimeError("modello non disponibile")


def leggi_metrica(client, riga):
    testo = client.get("/metrics").get_data(as_text=True)
    for linea in testo.splitlines():
        if linea.startswith(riga + " "):
            return float(linea.split()[-1])
    return None


def test_predict_restituisce_sentimento(client):
    risposta = client.post("/predict", json={"review": "This product is amazing! I love it."})
    assert risposta.status_code == 200
    dati = risposta.get_json()
    assert dati["sentiment"] == "positive"
    assert 0 < dati["confidence"] <= 1


def test_predict_senza_campo_review(client):
    risposta = client.post("/predict", json={"testo": "ciao"})
    assert risposta.status_code == 400


def test_predict_con_review_vuota(client):
    risposta = client.post("/predict", json={"review": "   "})
    assert risposta.status_code == 400


def test_predict_senza_json(client):
    risposta = client.post("/predict", data="non e json", content_type="text/plain")
    assert risposta.status_code == 400


def test_predict_con_review_non_testuale(client):
    risposta = client.post("/predict", json={"review": 123})
    assert risposta.status_code == 400


def test_predict_con_modello_rotto():
    client = crea_app(ModelloRotto()).test_client()
    risposta = client.post("/predict", json={"review": "ciao"})
    assert risposta.status_code == 500
    riga = 'sentiment_errori_predizione_total{tipo="errore_modello"}'
    assert leggi_metrica(client, riga) == 1.0


def test_metrics_formato_prometheus(client):
    client.get("/salute")
    risposta = client.get("/metrics")
    assert risposta.status_code == 200
    assert risposta.mimetype == "text/plain"
    testo = risposta.get_data(as_text=True)
    for nome in (
        "sentiment_richieste_total",
        "sentiment_durata_richieste_secondi_bucket",
        "sentiment_errori_predizione_total",
        "sentiment_predizioni_total",
        "sentiment_cpu_percentuale",
        "sentiment_memoria_byte",
    ):
        assert nome in testo


def test_metriche_aumentano_dopo_le_richieste(client):
    riga = 'sentiment_predizioni_total{sentimento="negative"}'
    prima = leggi_metrica(client, riga)
    client.post("/predict", json={"review": "Terrible, broke after one day."})
    assert leggi_metrica(client, riga) == prima + 1


def test_errori_di_input_contati(client):
    riga = 'sentiment_errori_predizione_total{tipo="input_non_valido"}'
    client.post("/predict", json={})
    assert leggi_metrica(client, riga) == 1.0


def test_memoria_positiva(client):
    assert leggi_metrica(client, "sentiment_memoria_byte") > 0


def test_salute(client):
    risposta = client.get("/salute")
    assert risposta.status_code == 200
    assert risposta.get_json() == {"stato": "ok"}


def test_percorso_inesistente(client):
    assert client.get("/non_esiste").status_code == 404


def test_metodo_non_consentito(client):
    assert client.get("/predict").status_code == 405
