import pickle


def carica_modello(percorso):
    with open(percorso, "rb") as file:
        return pickle.load(file)


def analizza_testo(modello, testo):
    probabilita = modello.predict_proba([testo])[0]
    posizione = int(probabilita.argmax())
    sentimento = str(modello.classes_[posizione])
    confidenza = round(float(probabilita[posizione]), 4)
    return sentimento, confidenza
