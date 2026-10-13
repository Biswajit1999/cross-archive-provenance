"""Reproducible synthetic coverage and candidate-ranking stress test.

No live archive rows are simulated or described as observed Gaia objects.
Run: python scripts/analyze_astrometric_evidence.py --out results/astrometric-evidence
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from provenance.astrometric_evidence import (  # noqa: E402
    candidate_posteriors, fit_epoch_span, propagate_position_covariance,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "results/astrometric-evidence")
    parser.add_argument("--trials", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261013)
    args = parser.parse_args()
    if args.trials < 20:
        parser.error("--trials must be at least 20")
    rng = np.random.default_rng(args.seed)
    true_dt = 15.0
    pm = np.array([200., -100.])
    cov = np.array([[0.04, 0.005], [0.005, 0.09]])
    offsets = rng.multivariate_normal(true_dt * pm / 1000, cov, size=args.trials)
    estimates = [fit_epoch_span(y, pm, cov) for y in offsets]
    errors = np.array([e["epoch_years"] - true_dt for e in estimates])
    sigmas = np.array([e["epoch_sigma_years"] for e in estimates])
    cov4 = np.diag([1., 1., 0.1, 0.1])
    result = {
        "data_kind": "synthetic controlled Monte Carlo, NOT Gaia or SIMBAD observations",
        "seed": args.seed, "trials": args.trials, "true_epoch_years": true_dt,
        "empirical_epoch_bias_years": float(errors.mean()),
        "epoch_1sigma_coverage": float(np.mean(np.abs(errors) <= sigmas)),
        "epoch_2sigma_coverage": float(np.mean(np.abs(errors) <= 2 * sigmas)),
        "propagated_covariance_15yr_arcsec2": propagate_position_covariance(cov4, 15).tolist(),
        "example_candidate_weights": {
            k: v.tolist() if isinstance(v, np.ndarray) else v
            for k, v in candidate_posteriors(
                [[0.1, 0], [1.2, 0]], np.array([np.eye(2) * 0.2] * 2),
                [0.01, 0.01], 0.8,
            ).items()
        },
        "limitations": (
            "Fixed covariance, Gaussian errors, local Poisson background; "
            "no archive epoch or source ID validation."
        ),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
