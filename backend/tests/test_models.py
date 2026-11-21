# @author: David Lameck

"""Structural smoke test to ensure the backend models package imports."""


def test_models_package_exists():
    import importlib

    pkg = importlib.import_module("models")
    assert pkg is not None
