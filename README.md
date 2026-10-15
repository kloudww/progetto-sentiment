# Sentiment Analysis: deploy e monitoraggio

Servizio REST che classifica recensioni in inglese come positive, neutral o negative, con pipeline Jenkins per build, test e deploy e monitoraggio con Prometheus e Grafana.

## Struttura

```
app/                    codice dell'API (Flask) e funzioni sul modello
modelli/                modello pickle fornito
test/                   test unitari e di integrazione
monitoraggio/           configurazione Prometheus e Grafana (dashboard inclusa)
jenkins/                immagine di Jenkins con Docker, per provare la pipeline in locale
strumenti/              script per generare traffico di prova
Dockerfile              immagini di test e di produzione
docker-compose.yml      api, prometheus e grafana
Jenkinsfile             pipeline CI/CD
```

## Requisiti

- Docker con Compose v2
- Python 3.12 (solo per esecuzione locale senza Docker)

Il modello e stato salvato con scikit-learn 1.6.0, per questo la versione e fissata in `requirements.txt`.

## Avvio con Docker

```
docker compose up -d --build
```

| Servizio   | Indirizzo             |
|------------|-----------------------|
| API        | http://localhost:8000 |
| Prometheus | http://localhost:9090 |
| Grafana    | http://localhost:3000 |

Grafana: utente `admin`, password `admin`. La dashboard "Sentiment Analysis API" e gia caricata.

Per fermare tutto: `docker compose down` (aggiungere `-v` per cancellare anche i dati).

## Avvio locale senza Docker

```
python -m venv venv
source venv/bin/activate
pip install -r requirements_sviluppo.txt
gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 avvio:applicazione
```

Si usa un solo worker perche le metriche sono tenute in memoria dal processo.

## Uso dell'API

Predizione:

```
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"review": "This product is amazing! I love it."}'
```

Risposta:

```
{"sentiment": "positive", "confidence": 0.5683}
```

La confidenza e la probabilita della classe scelta restituita dal modello. Con questo modello i valori sono moderati, quindi non ci si deve aspettare valori come 0.95.

Codici di risposta di `/predict`:

- 200 predizione eseguita
- 400 campo `review` mancante, vuoto o non testuale
- 500 errore del modello

Altri endpoint:

- `GET /metrics` metriche in formato Prometheus
- `GET /salute` controllo di stato usato dal Docker healthcheck

## Metriche esposte

| Metrica | Contenuto |
|---------|-----------|
| `sentiment_richieste_total` | richieste per endpoint, metodo e stato |
| `sentiment_durata_richieste_secondi` | istogramma dei tempi di risposta |
| `sentiment_errori_predizione_total` | errori per tipo (`input_non_valido`, `errore_modello`) |
| `sentiment_predizioni_total` | predizioni per sentimento |
| `sentiment_confidenza` | distribuzione della confidenza |
| `sentiment_cpu_percentuale` | CPU usata dal processo |
| `sentiment_memoria_byte` | memoria residente del processo |

Per popolare la dashboard con dati di prova:

```
python strumenti/genera_traffico.py http://localhost:8000 500 0.05
```

Gli argomenti sono indirizzo, numero di richieste e pausa in secondi tra una richiesta e l'altra. Circa il 5% delle richieste e volutamente errato, cosi si vedono anche gli errori.

## Test

```
pytest
```

Oppure nel container, come fa Jenkins:

```
docker build --target test -t sentiment-api-test .
docker run --rm sentiment-api-test
```

## Pipeline Jenkins

Fasi del `Jenkinsfile`:

1. Checkout del repository
2. Build delle immagini di test e di produzione
3. Test nel container, con report JUnit
4. Deploy con `docker compose` e attesa dello stato "healthy" (solo branch `main`)
5. Notifica via email a fine pipeline, con esito positivo o negativo

Configurazione:

1. Sul server Jenkins servono Docker e Compose v2, e l'utente di Jenkins deve poter usare Docker.
2. Plugin necessari: Pipeline, Git, GitHub, JUnit, Mailer.
3. Creare un job di tipo Pipeline con "Pipeline script from SCM", indicando il repository e il branch `main`.
4. Trigger automatico: nelle impostazioni del repository GitHub aggiungere un webhook verso `http://SERVER_JENKINS/github-webhook/` per gli eventi push. Con GitLab installare il plugin GitLab e sostituire `githubPush()` con `gitlab(triggerOnPush: true)` nel Jenkinsfile.
5. Email: configurare il server SMTP in Gestisci Jenkins, Sistema, Notifica via email, e cambiare `DESTINATARIO` nel Jenkinsfile.

### Jenkins in locale con Docker

Prima fermare l'eventuale stack avviato a mano (`docker compose down`), per liberare le porte.

```
docker build -t jenkins-docker jenkins
docker run -d --name jenkins --user root -p 8080:8080 -v jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock jenkins-docker
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Poi aprire http://localhost:8080, inserire la password mostrata, installare i plugin consigliati, creare l'utente amministratore e seguire i punti 2-5 qui sopra. Con Git Bash su Windows scrivere `//var/run/docker.sock` al posto di `/var/run/docker.sock`.

Jenkins usa il Docker della macchina ospite: le immagini e i container creati dalla pipeline compaiono quindi anche in Docker Desktop. I file di Prometheus e Grafana sono copiati nelle rispettive immagini, per questo il deploy funziona anche da dentro il container di Jenkins.

## Manutenzione

- Aggiornare il modello: sostituire il file in `modelli/` mantenendo il nome (oppure impostare la variabile `MODELLO_PERCORSO`) e allineare la versione di scikit-learn in `requirements.txt` a quella usata per salvarlo.
- Aggiornare le dipendenze: modificare `requirements.txt` e rilanciare i test.
- Cambiare le credenziali di Grafana prima di usarlo fuori da un ambiente di prova.
- Il file pickle va caricato solo da fonti fidate.
- Dashboard: modificabile da Grafana, il file di partenza e `monitoraggio/grafana/dashboards/sentiment.json`.
