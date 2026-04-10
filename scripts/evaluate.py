#!/usr/bin/env python3
"""
Evaluate VID-Fusion trajectory against EuRoC ground truth using evo.
Saves stats to JSON and trajectory/error plots to PDF.

Usage:
  python3 scripts/evaluate.py                             # defaults
  python3 scripts/evaluate.py --est /tmp/vid_out/vins_result.csv \
                               --gt  .../groundtruth/data.csv \
                               --out /tmp/vid_out --seq MH_01_easy
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")  # headless — no display needed
import matplotlib.pyplot as plt

from evo.core import metrics, sync, trajectory
from evo.tools import file_interface, plot


def load_vid_csv(path):
    """Read VID-Fusion result CSV (same layout as EuRoC but without # header)."""
    import numpy as np
    data = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("time"):
                continue
            data.append([float(x) for x in line.split(",")])
    data = np.array(data)
    stamps = data[:, 0] / 1e9          # ns -> s
    xyz    = data[:, 1:4]
    quat   = data[:, 4:8]              # qw qx qy qz
    return trajectory.PoseTrajectory3D(xyz, quat, stamps)


def evaluate(gt_path, est_path, out_dir, seq):
    os.makedirs(out_dir, exist_ok=True)

    gt  = file_interface.read_euroc_csv_trajectory(gt_path)
    est = load_vid_csv(est_path)

    gt_sync, est_sync = sync.associate_trajectories(gt, est)

    results = {}

    for name, pose_relation in [
        ("APE_translation", metrics.PoseRelation.translation_part),
        ("APE_rotation",    metrics.PoseRelation.rotation_angle_deg),
    ]:
        metric = metrics.APE(pose_relation)
        metric.process_data((gt_sync, est_sync))
        stats = metric.get_all_statistics()
        results[name] = stats
        print(f"\n{name}")
        for k, v in stats.items():
            print(f"  {k:10s}: {v:.4f}")

        # Error plot
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(metric.error)
        ax.set_title(f"{seq} — {name}")
        ax.set_xlabel("Frame")
        ax.set_ylabel("Error (m)" if "translation" in name else "Error (deg)")
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"{name}_{seq}.pdf"))
        plt.close(fig)

    # Trajectory plot
    fig = plt.figure(figsize=(8, 8))
    ax = plot.prepare_axis(fig, plot.PlotMode.xy)
    plot.traj(ax, plot.PlotMode.xy, gt_sync,  style="--", color="gray",  label="GT")
    plot.traj(ax, plot.PlotMode.xy, est_sync, style="-",  color="blue",  label="VID-Fusion")
    ax.legend()
    ax.set_title(f"{seq} — trajectory (xy)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, f"trajectory_{seq}.pdf"))
    plt.close(fig)

    # Save stats
    stats_path = os.path.join(out_dir, f"stats_{seq}.json")
    with open(stats_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nStats saved to {stats_path}")
    print(f"Plots saved to {out_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--est", default="/tmp/vid_out/vins_result.csv")
    parser.add_argument("--gt",  default="/catkin_ws/src/realflight_modules/VID-Fusion/data/machine_hall/MH_01_easy/groundtruth/data.csv")
    parser.add_argument("--out", default="/tmp/vid_out")
    parser.add_argument("--seq", default="MH_01_easy")
    args = parser.parse_args()
    evaluate(args.gt, args.est, args.out, args.seq)
