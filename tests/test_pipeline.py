from pathlib import Path

from src.pipeline import ingest, preprocess, synthetic, fairness


def test_pipeline_end_to_end(tmp_path: Path, monkeypatch):
    # Redirect data dirs to a temp folder to avoid polluting repo data/
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    # Monkeypatch config module constants used inside pipeline modules
    monkeypatch.setattr("src.pipeline.config.RAW_DIR", raw_dir, raising=False)
    monkeypatch.setattr(
        "src.pipeline.config.PROCESSED_DIR", processed_dir, raising=False
    )

    # Run steps
    ingest.main()
    assert (raw_dir / "worldpop_summary.csv").exists()
    assert (raw_dir / "energy_demand.csv").exists()

    preprocess.main()
    assert (processed_dir / "worldpop_features.csv").exists()
    assert (processed_dir / "energy_features.csv").exists()

    synthetic.main()
    syn = processed_dir / "synthetic_demographics.csv"
    assert syn.exists()

    # Fairness audits (will create a simple report)
    fairness.main()
    report = processed_dir / "fairness_report.csv"
    assert report.exists()
