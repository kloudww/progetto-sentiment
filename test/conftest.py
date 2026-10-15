import pytest

from app.applicazione import PERCORSO_MODELLO, crea_app
from app.modello import carica_modello


@pytest.fixture(scope="session")
def modello():
    return carica_modello(PERCORSO_MODELLO)


@pytest.fixture
def client(modello):
    app = crea_app(modello)
    return app.test_client()
