import json
import random
import sys
import time
import urllib.error
import urllib.request

RECENSIONI = [
    "This product is amazing! I love it.",
    "Great quality and fast delivery, highly recommended",
    "Terrible, broke after one day.",
    "Worst purchase ever, a complete waste of money",
    "It is okay I guess.",
    "Average product, nothing special",
    "Excellent value for the price",
    "Very disappointed, it stopped working",
]


def invia(indirizzo, contenuto):
    richiesta = urllib.request.Request(
        indirizzo + "/predict",
        data=json.dumps(contenuto).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=5) as risposta:
            return risposta.status
    except urllib.error.HTTPError as errore:
        return errore.code


def main():
    indirizzo = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    quante = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    pausa = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1

    esiti = {}
    for _ in range(quante):
        if random.random() < 0.05:
            contenuto = {"testo": "campo sbagliato"}
        else:
            contenuto = {"review": random.choice(RECENSIONI)}
        stato = invia(indirizzo, contenuto)
        esiti[stato] = esiti.get(stato, 0) + 1
        time.sleep(pausa)

    print("Richieste inviate:", quante)
    for stato, numero in sorted(esiti.items()):
        print("Stato", stato, ":", numero)


if __name__ == "__main__":
    main()
