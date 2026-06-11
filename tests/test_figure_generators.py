"""Fast unit tests for individual figure generators."""

from __future__ import annotations

from pathlib import Path

from src.experiment_config import VizConfig
from src.figures import (
    configure_viz,
    generate_expansion_figure,
    generate_observability_figure,
    generate_tamper_figure,
    generate_throughput_figure,
)

_SAMPLE_CSV = """\
condition,track_id,track_type,plaintext_bytes,expansion_ratio,pack_throughput_mib_s,unpack_seconds,manifest_bytes,observability_level,tamper_detected
small_tracks_r0,eeg,ento:timeseries.eeg,100,1.2,0.0,0.0,50,3,False
small_tracks_r0,vcf,ento:genomics.vcf,200,1.3,0.0,0.0,60,3,False
small_tracks_r0,eeg,ento:timeseries.eeg,100,1.1,0.0,0.0,40,0,False
small_tracks_r0,eeg,ento:timeseries.eeg,100,1.1,0.0,0.0,55,1,False
medium_tracks_r0,synthetic,ento:blockchain.proof,4096,1.4,12.5,0.01,70,3,False
medium_tracks_r0,synthetic,ento:blockchain.proof,4096,1.4,0.0,0.0,70,3,True
"""


def _write_sample_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "ento_benchmark_results.csv"
    csv_path.write_text(_SAMPLE_CSV, encoding="utf-8")
    return csv_path


def test_figure_generators_write_pngs(tmp_path: Path) -> None:
    configure_viz(VizConfig(dpi=100, figsize=(4, 3)))
    csv_path = _write_sample_csv(tmp_path)
    out_dir = tmp_path / "figures"
    generators = (
        generate_throughput_figure,
        generate_expansion_figure,
        generate_observability_figure,
        generate_tamper_figure,
    )
    for index, generator in enumerate(generators):
        png = generator(csv_path, out_dir / f"fig_{index}.png")
        assert png.is_file()
        assert png.stat().st_size > 0
