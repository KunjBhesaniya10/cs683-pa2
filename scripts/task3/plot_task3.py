#Task 3 tables and plots for SPP with prefetch-aware dynamic I-RRIP.

import csv
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = Path(__file__).resolve().parents[2] / "results" / "task3"
TRACES = ["trace1", "trace2", "trace3"]
BASELINE = "baseline"
CONFIGS = ["baseline", "spp", "dyn", "spp_dyn"]
PREFETCHING = {"spp", "spp_dyn"}
LABELS = {"baseline": "Baseline (no pref, LRU)", "spp": "SPP + LRU", "dyn": "Dyn I-RRIP",
          "spp_dyn": "SPP + prefetch-aware Dyn I-RRIP"}
COLORS = {"baseline": "gray", "spp": "darkorange", "dyn": "steelblue", "spp_dyn": "seagreen"}

PATTERNS = {
    "IPC": r"^CPU 0 cumulative IPC: ([\d.]+)",
    "L1D load misses": r"^L1D LOAD\s+ACCESS:\s+\d+\s+HIT:\s+\d+\s+MISS:\s+(\d+)",
    "L1D load MPKI": r"^L1D LOAD\s+ACCESS:.*MPKI: ([\d.]+)",
    "L1D accuracy (%)": r"^L1D USEFUL LOAD PREFETCHES:.*ACCURACY: ([\d.]+)",
    "L2C load MPKI": r"^L2C LOAD\s+ACCESS:.*MPKI: ([\d.]+)",
    "L2C instruction MPKI": r"^L2C INSTRUCTION LOAD MPKI: ([\d.]+)",
    "L2C data MPKI": r"^L2C DATA LOAD MPKI: ([\d.]+)",
    "I-RRIP mode (%)": r"^I-RRIP mode: ([\d.]+)%",
}
COLUMNS = ["IPC", "Speedup", "L1D load MPKI", "L1D accuracy (%)", "L1D coverage (%)",
           "L2C load MPKI", "L2C instruction MPKI", "L2C data MPKI", "I-RRIP mode (%)"]
GEOMEAN = ["IPC", "Speedup"]
PLOTS = {
    "IPC": "IPC",
    "Speedup": "Speedup over baseline (no prefetching, LRU)",
    "L1D load MPKI": "L1D load MPKI",
    "L1D accuracy (%)": "L1D prefetch accuracy",
    "L1D coverage (%)": "L1D prefetch coverage",
    "L2C load MPKI": "L2C load MPKI",
    "L2C instruction MPKI": "L2C instruction load MPKI",
    "L2C data MPKI": "L2C data load MPKI",
}


def read(path):
    text = path.read_text(errors="replace")
    matches = {name: re.search(pattern, text, re.M) for name, pattern in PATTERNS.items()}
    return {name: float(m.group(1)) for name, m in matches.items() if m}


def load():
    runs = {c: {t: read(RESULTS / f"{t}_{c}.txt") for t in TRACES} for c in CONFIGS}
    # speedup = IPC / baseline IPC; coverage = (baseline misses - misses) / baseline misses
    for config, traces in runs.items():
        for trace, stats in traces.items():
            base = runs[BASELINE][trace]
            stats["Speedup"] = stats["IPC"] / base["IPC"]
            if config in PREFETCHING:
                stats["L1D coverage (%)"] = 100.0 * (base["L1D load misses"] - stats["L1D load misses"]) / base["L1D load misses"]
            else:
                stats.pop("L1D accuracy (%)", None)
    return runs


def geomean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def write_csv(runs):
    with open(RESULTS / "results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trace", "config"] + COLUMNS)
        for config in CONFIGS:
            for trace in TRACES:
                stats = runs[config][trace]
                writer.writerow([trace, config] + [f"{stats[c]:.4f}" if c in stats else "" for c in COLUMNS])
            mean = {m: geomean([runs[config][t][m] for t in TRACES]) for m in GEOMEAN}
            writer.writerow(["geomean", config] + [f"{mean[c]:.4f}" if c in mean else "" for c in COLUMNS])


def plot(runs, metric, path):
    shown = [c for c in CONFIGS if metric in runs[c][TRACES[0]] and not (metric == "Speedup" and c == BASELINE)]
    width = 0.8 / len(shown)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    values = []
    for i, config in enumerate(shown):
        ys = [runs[config][t][metric] for t in TRACES]
        xs = [x + (i - (len(shown) - 1) / 2) * width for x in range(len(TRACES))]
        ax.bar(xs, ys, width - 0.03, color=COLORS[config], label=LABELS[config])
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:.3f}" if y < 10 else f"{y:.1f}", (x, y), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=6, rotation=90)
        values += ys
    if metric == "Speedup":
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Baseline")
        values.append(1)
    lo, hi = min(values), max(values)
    pad = 0.1 * (hi - lo) or 0.01 * abs(hi) or 1
    ax.set_ylim(max(lo - pad, 0), hi + 4 * pad)
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.set_xticks(range(len(TRACES)))
    ax.set_xticklabels(TRACES)
    ax.set_ylabel(metric)
    ax.set_title(PLOTS[metric])
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    runs = load()
    write_csv(runs)
    out = RESULTS / "plots"
    out.mkdir(exist_ok=True)
    for metric in PLOTS:
        name = re.sub(r"\W+", "_", metric).strip("_").lower()
        plot(runs, metric, out / f"{name}.png")
    print("Wrote", RESULTS / "results.csv", "and", out)


if __name__ == "__main__":
    main()
