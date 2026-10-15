from app.applicazione import crea_app

applicazione = crea_app()

if __name__ == "__main__":
    applicazione.run(host="0.0.0.0", port=8000)
