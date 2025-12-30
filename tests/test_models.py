# @author: Lameck David Musumpuka

"""Structural smoke test to ensure the backend models package imports."""


def test_models_package_exists():
    import importlib

    pkg = importlib.import_module("src.backend.models")
    assert pkg is not None
