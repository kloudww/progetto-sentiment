FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY modelli ./modelli
COPY avvio.py .


FROM base AS test

COPY requirements_sviluppo.txt .
RUN pip install --no-cache-dir -r requirements_sviluppo.txt

COPY pytest.ini .
COPY test ./test
RUN mkdir report

CMD ["pytest", "--junitxml=report/risultati.xml"]


FROM base AS produzione

RUN useradd --create-home --uid 1000 utente
USER utente

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/salute', timeout=2)"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "avvio:applicazione"]
