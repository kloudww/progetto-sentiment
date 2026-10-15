import numpy as np
import pytest

from app.modello import analizza_testo, carica_modello


class ModelloFinto:
    classes_ = np.array(["negative", "neutral", "positive"])

    def predict_proba(self, testi):
        return np.array([[0.1, 0.2, 0.7]])


def test_recensione_positiva(modello):
    sentimento, _ = analizza_testo(modello, "This product is amazing! I love it.")
    assert sentimento == "positive"


def test_recensione_negativa(modello):
    sentimento, _ = analizza_testo(modello, "Terrible, broke after one day.")
    assert sentimento == "negative"


def test_recensione_neutra(modello):
    sentimento, _ = analizza_testo(modello, "It is okay I guess.")
    assert sentimento == "neutral"


def test_confidenza_tra_zero_e_uno(modello):
    _, confidenza = analizza_testo(modello, "Great quality and fast delivery")
    assert 0 < confidenza <= 1


def test_modello_finto():
    sentimento, confidenza = analizza_testo(ModelloFinto(), "qualsiasi testo")
    assert sentimento == "positive"
    assert confidenza == 0.7


def test_file_inesistente():
    with pytest.raises(FileNotFoundError):
        carica_modello("non_esiste.pkl")
