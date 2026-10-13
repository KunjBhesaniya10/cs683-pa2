import csv
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = Path(__file__).resolve().parents[2] / "results" / "task2"
A = RESULTS / "task2a"
B = RESULTS / "task2b"
BASELINE = "lru"

PATTERNS = {
    "IPC": r"^CPU 0 cumulative IPC: ([\d.]+)",
    "L2C load MPKI": r"^L2C LOAD\s+ACCESS:.*MPKI: ([\d.]+)",
    "L2C instruction MPKI": r"^L2C INSTRUCTION LOAD MPKI: ([\d.]+)",
    "L2C data MPKI": r"^L2C DATA LOAD MPKI: ([\d.]+)",
    "I-RRIP mode (%)": r"^I-RRIP mode: ([\d.]+)%",
    "Switches": r"^I-RRIP mode: .* (\d+) switches",
}
METRICS = ["IPC", "Speedup", "L2C load MPKI", "L2C instruction MPKI", "L2C data MPKI"]
TITLES = {
    "IPC": "IPC",
    "Speedup": "Speedup over baseline (LRU)",
    "L2C load MPKI": "L2C load MPKI",
    "L2C instruction MPKI": "L2C instruction load MPKI",
    "L2C data MPKI": "L2C data load MPKI",
}
LABELS = {
    "lru": "LRU", "rrip": "RRIP", "irrip": "I-RRIP",
    "dyn_t0.30": "T=0.30", "dyn_t0.40": "T=0.40", "dyn_t0.45": "T=0.45", "dyn_t0.50": "T=0.50", "dyn_t0.60": "T=0.60", "dyn_t0.70": "T=0.70",
    "dyn_ls16": "16 leader sets", "dyn_ls32": "32 leader sets", "dyn_ls64": "64 leader sets",
    "dyn_psel6": "6-bit PSEL", "dyn_psel8": "8-bit PSEL", "dyn_psel10": "10-bit PSEL", "dyn_psel12": "12-bit PSEL",
}
COLORS = ["steelblue", "darkorange", "seagreen", "mediumpurple", "firebrick", "goldenrod"]

PLOTS = [
    ([A], ["lru", "rrip", "irrip"], A / "plots", {}),
    ([B / "threshold", A], ["lru", "rrip", "irrip", "dyn_t0.45"], B / "plots", {"dyn_t0.45": "Dynamic I-RRIP"}),
]

DYN_COLUMNS = METRICS + ["I-RRIP mode (%)", "Switches"]

TABLES = [
    ([A / "insertion_promotion", A],
     ["lru", "ins1_nopromo", "ins1_hit0", "ins1_hit1", "ins0_nopromo", "ins0_hit0", "ins0_hit1"],
     METRICS, A / "insertion_promotion" / "results.csv"),
    ([B / "threshold", A], ["lru", "dyn_t0.30", "dyn_t0.40", "dyn_t0.45", "dyn_t0.50", "dyn_t0.60", "dyn_t0.70"],
     DYN_COLUMNS, B / "threshold" / "results.csv"),
    ([B / "leader_sets", A], ["lru", "dyn_ls16", "dyn_ls32", "dyn_ls64"], DYN_COLUMNS, B / "leader_sets" / "results.csv"),
    ([B / "psel_bits", A], ["lru", "dyn_psel6", "dyn_psel8", "dyn_psel10", "dyn_psel12"], DYN_COLUMNS,
     B / "psel_bits" / "results.csv"),
]


def read(path):
    text = path.read_text(errors="replace")
    matches = {name: re.search(pattern, text, re.M) for name, pattern in PATTERNS.items()}
    return {name: float(m.group(1)) for name, m in matches.items() if m}


def load(folders):
    runs = {}
    for folder in folders:
        for path in sorted(folder.glob("*_*.txt")):
            trace, config = path.stem.split("_", 1)
            runs.setdefault(config, {})[trace] = read(path)
    for traces in runs.values():
        for trace, stats in traces.items():
            stats["Speedup"] = stats["IPC"] / runs[BASELINE][trace]["IPC"]
    return runs


def geomean(values):
    return math.exp(sum(math.log(v) for v in values) / len(values))


def cell(stats, column):
    if column not in stats:
        return ""
    return int(stats[column]) if column == "Switches" else f"{stats[column]:.4f}"


def write_csv(runs, configs, traces, columns, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trace", "config"] + columns)
        for config in configs:
            rows = [runs[config][t] for t in traces]
            for trace, stats in zip(traces, rows):
                writer.writerow([trace, config] + [cell(stats, c) for c in columns])
            mean = {m: geomean([stats[m] for stats in rows]) for m in METRICS}
            writer.writerow(["geomean", config] + [cell(mean, c) for c in columns])


def plot(runs, configs, traces, metric, labels, path):
    shown = [c for c in configs if metric != "Speedup" or c != BASELINE]
    colors = iter(COLORS)
    fmt = "{:.4f}"
    rotation = 90 if len(shown) > 4 else 0
    width = 0.8 / len(shown)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    values = []
    for i, config in enumerate(shown):
        ys = [runs[config][t][metric] for t in traces]
        xs = [x + (i - (len(shown) - 1) / 2) * width for x in range(len(traces))]
        color = "gray" if config == BASELINE else next(colors)
        ax.bar(xs, ys, width - 0.03, color=color, label=labels.get(config, config))
        for x, y in zip(xs, ys):
            ax.annotate(fmt.format(y), (x, y), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, rotation=rotation)
        values += ys
    if metric == "Speedup":
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Baseline (LRU)")
        values.append(1)
    lo, hi = min(values), max(values)
    pad = 0.1 * (hi - lo) or 0.01 * abs(hi) or 1
    ax.set_ylim(max(lo - pad, 0), hi + (4 if rotation else 2) * pad)
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.set_xticks(range(len(traces)))
    ax.set_xticklabels(traces)
    ax.set_ylabel(metric)
    ax.set_title(TITLES[metric])
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    for folders, configs, out, override in PLOTS:
        runs = load(folders)
        traces = sorted(runs[BASELINE])
        out.mkdir(parents=True, exist_ok=True)
        write_csv(runs, configs, traces, METRICS, out / "results.csv")
        for metric in METRICS:
            name = re.sub(r"\W+", "_", metric).strip("_").lower()
            plot(runs, configs, traces, metric, {**LABELS, **override}, out / f"{name}.png")
        print("Wrote", out)
    for folders, configs, columns, path in TABLES:
        runs = load(folders)
        write_csv(runs, configs, sorted(runs[BASELINE]), columns, path)
        print("Wrote", path)


if __name__ == "__main__":
    main()
