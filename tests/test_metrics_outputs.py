import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_metrics_and_evidence_outputs_are_complete():
    results = json.loads((ROOT / "results.json").read_text())

    assert results["dataset"]["synthetic"] is True
    assert results["test_rows"] == 10_000
    assert set(results["metrics"]) == {
        "gradient_boosting_model",
        "rules_only_baseline",
    }
    for metric_set in results["metrics"].values():
        for name in ("precision", "recall", "f1", "macro_f1"):
            assert 0 <= metric_set[name] <= 1

    latency = results["milliseconds_per_decision"]
    assert latency["unit"] == "milliseconds"
    assert latency["median"] > 0
    assert latency["p99"] >= latency["median"]
    assert latency["samples"] >= 1_000

    for filename in ("confusion_matrix.png", "feature_importance.png"):
        path = ROOT / "evidence" / filename
        assert path.exists()
        assert path.stat().st_size > 10_000
