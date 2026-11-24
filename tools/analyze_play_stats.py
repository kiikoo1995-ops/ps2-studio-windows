"""Analyze real Play! one-second counters without omitting zero samples."""
import argparse
import json
from pathlib import Path
from statistics import mean, median

def analyze_stats(text, warmup=3, target=60):
    if warmup < 0 or target <= 0:
        raise ValueError("Invalid warmup or target")
    counts = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.strip().split("\t")
        if len(fields) != 2 or any(not x.isascii() or not x.isdecimal() for x in fields):
            raise ValueError("Invalid counter row: " + line)
        counts.append(int(fields[0]))
    measured = counts[warmup:]
    if not measured:
        raise ValueError("No post-warmup samples")
    ordered = sorted(measured)
    return {
        "total_samples": len(counts), "warmup_excluded": warmup,
        "measured_samples": len(measured),
        "mean_frames_per_interval": round(mean(measured), 2),
        "median_frames_per_interval": median(measured),
        "min_frames_per_interval": min(measured),
        "max_frames_per_interval": max(measured),
        "p05_frames_per_interval": ordered[max(0,(len(ordered)*5+99)//100-1)],
        "zero_intervals": measured.count(0),
        "below_90_percent_target": sum(v < 0.9*target for v in measured),
        "target_nominal_fps": target,
        "limitations": "Nominal 1-second counter intervals, not individual frame times or proof of smoothness."
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stats", type=Path)
    p.add_argument("--warmup", type=int, default=3)
    p.add_argument("--target", type=float, default=60)
    a = p.parse_args()
    print(json.dumps(analyze_stats(a.stats.read_text(encoding="utf-8-sig"), a.warmup, a.target), indent=2))
