"""Data pipeline package for SUSPS.

Modules:
- ingest: fetches raw datasets (provider-backed when available, with offline fallbacks)
- preprocess: cleans and engineers features
- synthetic: generates deterministic synthetic datasets used as fallbacks
- fairness: runs bias and coverage audits
- config: central paths, constants, parameters
"""

__all__ = [
    "config",
    "ingest",
    "preprocess",
    "synthetic",
    "fairness",
]
