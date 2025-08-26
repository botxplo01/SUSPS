def test_models_package_exists():
    import importlib
    pkg = importlib.import_module('src.backend.models')
    assert pkg is not None
