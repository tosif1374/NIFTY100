from src.api.main import app


def test_app_imports():
    assert app is not None
    assert app.title
