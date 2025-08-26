from src.webapp.app import create_dash_app


def test_create_dash_app():
    dash_app = create_dash_app("/test/")
    assert dash_app is not None
    assert dash_app.title == "SUSPS Dashboard"
