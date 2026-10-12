"""Generate the Gaia DR3 proper-motion validation table and figure."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scienceplots  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from provenance.proper_motion import analyze_discrepancies  # noqa: E402


def main() -> None:
    discrepancies = pd.read_csv(ROOT / "results/default/position_discrepancies.csv")
    candidates = pd.read_csv(ROOT / "data/gaia_dr3_discrepancy_candidates.csv")
    results = analyze_discrepancies(discrepancies, candidates).sort_values(
        "original_separation_arcsec", ascending=False
    )
    out = ROOT / "results/gaia-proper-motion"
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out / "proper_motion_validation.csv", index=False)
    validated = results[results.status == "validated"].copy()
    spans = np.linspace(0, 20, 161)
    sweep_rows = []
    for span in spans:
        residuals = np.sqrt(
            validated.cross_track_residual_arcsec**2
            + (
                (span - validated.implied_epoch_span_years)
                * validated.gaia_total_pm_mas_per_year
                / 1000
            )
            ** 2
        )
        sweep_rows.append(
            {
                "epoch_span_years": span,
                "median_residual_arcsec": float(np.median(residuals)),
                "maximum_residual_arcsec": float(np.max(residuals)),
            }
        )
    sweep = pd.DataFrame(sweep_rows)
    sweep.to_csv(out / "epoch_span_sensitivity.csv", index=False)
    summary = {
        "data_kind": "real NEA, SIMBAD, and Gaia DR3 archive products",
        "n_flagged": len(results),
        "n_with_plausible_gaia_motion": len(validated),
        "n_fixed_16yr_residual_below_1_arcsec": int((results.fixed_16yr_residual_arcsec < 1).sum()),
        "median_implied_epoch_span_years": float(validated.implied_epoch_span_years.median()),
        "median_offset_explained_fraction": float(validated.offset_explained_fraction.median()),
        "maximum_fixed_16yr_residual_arcsec": float(validated.fixed_16yr_residual_arcsec.max()),
        "limitations": (
            "A Gaia motion is accepted only when the nearest candidate lies within 1 arcsec "
            "of the NEA position and has finite proper motion. A large nearest/second "
            "candidate margin is evidence against confusion, not an identifier proof. The "
            "uncertainty column propagates Gaia errors only; NEA/SIMBAD coordinate errors and "
            "their exact reference epochs are unavailable here, so no full significance is claimed."
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with plt.style.context(["science", "no-latex", "bright"]):
        fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4), constrained_layout=True)
        points = axes[0].scatter(
            results.original_separation_arcsec,
            results.fixed_16yr_residual_arcsec,
            c=results.gaia_total_pm_mas_per_year,
            cmap="viridis",
            s=55,
        )
        limit = max(results.original_separation_arcsec) * 1.05
        axes[0].plot([0, limit], [0, limit], "--", color="0.55", label="No improvement")
        axes[0].set(
            xlabel="Original NEA--SIMBAD separation [arcsec]",
            ylabel="Residual after Gaia 16 yr motion [arcsec]",
            title="(a) Epoch-propagation test",
            xlim=(0, limit),
            ylim=(0, limit),
        )
        axes[0].legend(frameon=False)
        for row in results.itertuples():
            if row.fixed_16yr_residual_arcsec > 2:
                axes[0].annotate(
                    row.hostname,
                    (row.original_separation_arcsec, row.fixed_16yr_residual_arcsec),
                    fontsize=6,
                )

        axes[1].plot(
            sweep.epoch_span_years,
            sweep.median_residual_arcsec,
            lw=2,
            label="Median residual",
        )
        axes[1].plot(
            sweep.epoch_span_years,
            sweep.maximum_residual_arcsec,
            lw=1.5,
            label="Maximum residual",
        )
        axes[1].axvline(15.5, color="0.35", ls=":", label="15.5 yr")
        axes[1].axvline(16, color="0.35", ls="--", label="J2000 to Gaia DR3 epoch")
        axes[1].set(
            xlabel="Tested epoch span [yr]",
            ylabel="Position residual [arcsec]",
            title="(b) Epoch-span sensitivity",
            yscale="log",
        )
        axes[1].legend(frameon=False)
        colorbar = fig.colorbar(points, ax=axes[0], shrink=0.82)
        colorbar.set_label("Gaia total proper motion [mas yr$^{-1}$]")
        fig.suptitle("Cross-archive position discrepancies tested with Gaia DR3")
        fig.savefig(out / "proper_motion_validation.png", dpi=240)
        fig.savefig(out / "proper_motion_validation.pdf")
        plt.close(fig)


if __name__ == "__main__":
    main()
