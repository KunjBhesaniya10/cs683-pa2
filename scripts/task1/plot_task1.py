#Task 1 plots for baseline, IP-stride and SPP.

import csv
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "results", "task1")
TRACES = ["trace1", "trace2", "trace3"]
CONFIGS = [("baseline", "Baseline", "gray"), ("ipstride", "IP-stride", "steelblue"), ("spp", "SPP", "darkorange")]


def parse(trace, config):
    text = open(os.path.join(RESULTS, "final", f"{trace}_{config}.txt")).read()
    load = re.search(r"^L1D LOAD\s+ACCESS:\s+\d+\s+HIT:\s+\d+\s+MISS:\s+(\d+).*MPKI: ([\d.]+)", text, re.M)
    acc = re.search(r"^L1D USEFUL LOAD PREFETCHES:.*ACCURACY: ([\d.]+)", text, re.M)
    return {
        "ipc": float(re.search(r"^CPU 0 cumulative IPC: ([\d.]+)", text, re.M).group(1)),
        "misses": int(load.group(1)),
        "mpki": float(load.group(2)),
        "accuracy": float(acc.group(1)) if config != "baseline" else None,
    }


def bar_plot(name, ylabel, title, series, fmt, ylim=None, baseline_line=False):
    """series: list of (label, color, values per trace)."""
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    width = 0.8 / len(series)
    for i, (label, color, values) in enumerate(series):
        xs = [x + (i - (len(series) - 1) / 2) * width for x in range(len(TRACES))]
        ax.bar(xs, values, width - 0.03, color=color, label=label)
        for x, v in zip(xs, values):
            ax.annotate(fmt.format(v), (x, v), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=7)
    if baseline_line:
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Baseline (no prefetching)")
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xticks(range(len(TRACES)))
    ax.set_xticklabels(TRACES)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "plots", f"{name}.png"), dpi=200)
    plt.close(fig)


def main():
    os.makedirs(os.path.join(RESULTS, "plots"), exist_ok=True)
    data = {(t, c): parse(t, c) for t in TRACES for c, _, _ in CONFIGS}

    # speedup = IPC / baseline IPC; 
    # coverage = (baseline misses - misses) / baseline misses
    for t in TRACES:
        base = data[(t, "baseline")]
        for c, _, _ in CONFIGS:
            d = data[(t, c)]
            d["speedup"] = d["ipc"] / base["ipc"]
            d["coverage"] = 100.0 * (base["misses"] - d["misses"]) / base["misses"]

    with open(os.path.join(RESULTS, "final_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trace", "config", "ipc", "speedup", "l1d_load_mpki", "accuracy_pct", "coverage_pct"])
        for t in TRACES:
            for c, _, _ in CONFIGS:
                d = data[(t, c)]
                prefetching = c != "baseline"
                w.writerow([t, c, f"{d['ipc']:.6f}", f"{d['speedup']:.4f}", f"{d['mpki']:.4f}",
                            f"{d['accuracy']:.2f}" if prefetching else "",
                            f"{d['coverage']:.2f}" if prefetching else ""])

    prefetchers = CONFIGS[1:]
    bar_plot("speedup", "Speedup", "Speedup of L1D prefetchers over baseline (no prefetching)",
             [(lbl, col, [data[(t, c)]["speedup"] for t in TRACES]) for c, lbl, col in prefetchers], "{:.4f}",
             ylim=(0.99, 1.03), baseline_line=True)
    bar_plot("l1d_mpki", "L1D load MPKI", "L1D load MPKI",
             [(lbl, col, [data[(t, c)]["mpki"] for t in TRACES]) for c, lbl, col in CONFIGS], "{:.2f}")
    bar_plot("accuracy", "L1D prefetch accuracy (%)", "L1D prefetch accuracy",
             [(lbl, col, [data[(t, c)]["accuracy"] for t in TRACES]) for c, lbl, col in prefetchers], "{:.2f}")
    bar_plot("coverage", "L1D prefetch coverage (%)", "L1D prefetch coverage",
             [(lbl, col, [data[(t, c)]["coverage"] for t in TRACES]) for c, lbl, col in prefetchers], "{:.2f}")


if __name__ == "__main__":
    main()
