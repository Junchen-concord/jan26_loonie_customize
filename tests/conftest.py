import warnings

import pytest
import xgboost as xgb
from fastapi.testclient import TestClient

from app import create_app
from fastapi_app import app as fastapi_app

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"The '__version__' attribute is deprecated and will be removed in in a future version.*",
    module=r"flask_apispec\.apidoc",
)


@pytest.fixture(autouse=True, scope="session")
def silence_xgb():
    # completely silence all C-API logs (to suppress warnings)
    xgb.set_config(verbosity=0)
    yield


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["DEBUG"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def fastapi_client():
    """FastAPI test client fixture"""
    with TestClient(fastapi_app) as client:
        yield client
