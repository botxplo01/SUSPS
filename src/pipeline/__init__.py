"""Data pipeline package for SUSPS.

Modules:
- ingest: fetches raw datasets (open/synthetic placeholders)
- preprocess: cleans and engineers features
- synthetic: generates bias-aware synthetic datasets
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
