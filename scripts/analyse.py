#!/usr/bin/env python3
"""Plot VAMPIRE Curie-temperature sweeps and estimate Tc.

Usage: python3 scripts/analyse.py results/Fe_bcc results/Co_fcc

Two estimates of Tc for each case:
  1. peak of the longitudinal susceptibility chi(T)
  2. fit of m(T) = (1 - T/Tc)^beta below Tc (the fit used in the VAMPIRE papers)
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Columns written by VAMPIRE for the outputs requested in the input files:
# T [K], mean |m|, mean chi_x, chi_y, chi_z, chi_|m|  (chi in 1/T)
T_COL, M_COL, CHI_COL = 0, 1, 5
EXPERIMENT_TC = {"Fe_bcc": 1043, "Co_fcc": 1388}


def fit_critical(T, m, tc_guess):
    """Least-squares grid fit of m = (1 - T/Tc)^beta for T < 0.95 * tc_guess."""
    sel = (T > 0) & (T < 0.95 * tc_guess)
    best = (np.inf, None, None)
    for tc in np.arange(0.8 * tc_guess, 1.2 * tc_guess, 1.0):
        x = 1 - T[sel] / tc
        if np.any(x <= 0):
            continue
        for beta in np.arange(0.20, 0.50, 0.005):
            err = np.sum((m[sel] - x**beta) ** 2)
            if err < best[0]:
                best = (err, tc, beta)
    return best[1], best[2]


def main(dirs):
    fig, (ax_m, ax_chi) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    colors = ["#1f5fa8", "#c2571a", "#2a8a4a"]
    rows = []
    for d, c in zip(map(Path, dirs), colors):
        name = d.name
        data = np.loadtxt(d / "output", comments="#")
        T, m, chi = data[:, T_COL], data[:, M_COL], data[:, CHI_COL]
        tc_chi = T[np.argmax(chi)]
        tc_fit, beta = fit_critical(T, m, tc_chi)
        rows.append((name, tc_chi, tc_fit, beta, EXPERIMENT_TC.get(name)))

        label = name.replace("_", " ")
        ax_m.plot(T, m, "o", ms=4, color=c, label=f"{label} (VAMPIRE)")
        Tf = np.linspace(0, tc_fit, 300)
        ax_m.plot(Tf, (1 - Tf / tc_fit) ** beta, "-", lw=1.2, color=c,
                  label=f"fit: Tc = {tc_fit:.0f} K, β = {beta:.2f}")
        ax_chi.plot(T, chi / chi.max(), "o-", ms=3, lw=1, color=c, label=label)
        ax_chi.axvline(tc_chi, color=c, ls=":", lw=1)

    ax_m.set_xlabel("Temperature (K)")
    ax_m.set_ylabel("Mean magnetisation |m| / m(0)")
    ax_m.set_ylim(0, 1.05)
    ax_m.legend(frameon=False, fontsize=8)
    ax_m.set_title("Magnetisation vs temperature")
    ax_chi.set_xlabel("Temperature (K)")
    ax_chi.set_ylabel("Susceptibility χ (normalised)")
    ax_chi.legend(frameon=False, fontsize=8)
    ax_chi.set_title("Susceptibility peak marks Tc")
    for ax in (ax_m, ax_chi):
        ax.spines[["top", "right"]].set_visible(False)

    out = Path("results")
    out.mkdir(exist_ok=True)
    fig.savefig(out / "curie_temperature.png", dpi=200)

    lines = ["| System | Tc from χ peak (K) | Tc from fit (K) | β | Experiment (K) |",
             "|---|---|---|---|---|"]
    for name, tc_chi, tc_fit, beta, exp in rows:
        lines.append(f"| {name} | {tc_chi:.0f} | {tc_fit:.0f} | {beta:.2f} | {exp} |")
    table = "\n".join(lines)
    (out / "tc_summary.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main(sys.argv[1:] or ["results/Fe_bcc", "results/Co_fcc"])
