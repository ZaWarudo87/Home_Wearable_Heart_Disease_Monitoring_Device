from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


HEALTH_PATTERN = re.compile(
    r"^(?P<time>\d{2}:\d{2}:\d{2}),\s*temp=(?P<temp>[\d.]+)'C,\s*throttled=(?P<throttle>0x[0-9a-fA-F]+)$"
)
DOCKER_TIME_PATTERN = re.compile(r"^(?P<time>\d{2}:\d{2}:\d{2})$")
DOCKER_CPU_PATTERN = re.compile(
    r"^heart-monitor-backend\s+(?P<cpu>[\d.]+)%\s+(?P<mem_used>\S+)\s*/\s*(?P<mem_limit>\S+)$"
)


def parse_health_log(path: Path) -> pd.DataFrame:
    rows: list[dict] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            match = HEALTH_PATTERN.match(line)
            if not match:
                continue

            t = datetime.strptime(match.group("time"), "%H:%M:%S")
            throttle_raw = int(match.group("throttle"), 16)

            rows.append(
                {
                    "time": t,
                    "temp_c": float(match.group("temp")),
                    "throttle_raw": throttle_raw,
                    "is_throttled_now": int(bool(throttle_raw & 0x4)),
                    "is_undervoltage_now": int(bool(throttle_raw & 0x1)),
                }
            )

    if not rows:
        raise ValueError(f"No valid rows parsed from {path}")

    return pd.DataFrame(rows).sort_values("time").reset_index(drop=True)


def parse_docker_stats_log(path: Path) -> pd.DataFrame:
    rows: list[dict] = []
    current_time: datetime | None = None

    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("NAME"):
                continue

            time_match = DOCKER_TIME_PATTERN.match(line)
            if time_match:
                current_time = datetime.strptime(time_match.group("time"), "%H:%M:%S")
                continue

            cpu_match = DOCKER_CPU_PATTERN.match(line)
            if cpu_match and current_time is not None:
                rows.append(
                    {
                        "time": current_time,
                        "cpu_pct": float(cpu_match.group("cpu")),
                        "mem_used": cpu_match.group("mem_used"),
                        "mem_limit": cpu_match.group("mem_limit"),
                    }
                )

    if not rows:
        raise ValueError(f"No valid rows parsed from {path}")

    return pd.DataFrame(rows).sort_values("time").reset_index(drop=True)


def save_health_chart(df_health: pd.DataFrame, out_path: Path) -> None:
    fig, ax_temp = plt.subplots(figsize=(12, 5))
    ax_flag = ax_temp.twinx()

    ax_temp.plot(df_health["time"], df_health["temp_c"], color="#d62728", linewidth=2.0, label="Temperature (C)")
    ax_flag.step(
        df_health["time"],
        df_health["is_throttled_now"],
        where="post",
        color="#1f77b4",
        linewidth=1.6,
        alpha=0.9,
        label="Throttled now (0/1)",
    )
    ax_flag.step(
        df_health["time"],
        df_health["is_undervoltage_now"],
        where="post",
        color="#2ca02c",
        linewidth=1.4,
        alpha=0.8,
        label="Under-voltage now (0/1)",
    )

    ax_temp.set_title("Device Temperature and Throttle Flags")
    ax_temp.set_xlabel("Time")
    ax_temp.set_ylabel("Temperature (C)")
    ax_flag.set_ylabel("Throttle flags")
    ax_flag.set_ylim(-0.1, 1.2)

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter("%H:%M:%S")
    ax_temp.xaxis.set_major_locator(locator)
    ax_temp.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    lines_1, labels_1 = ax_temp.get_legend_handles_labels()
    lines_2, labels_2 = ax_flag.get_legend_handles_labels()
    ax_temp.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")
    ax_temp.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def save_docker_cpu_chart(df_docker: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df_docker["time"], df_docker["cpu_pct"], color="#9467bd", linewidth=1.8)

    ax.set_title("Docker Backend CPU Usage")
    ax.set_xlabel("Time")
    ax.set_ylabel("CPU %")
    ax.grid(alpha=0.25)

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter("%H:%M:%S")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def save_combined_chart(df_health: pd.DataFrame, df_docker: pd.DataFrame, out_path: Path) -> None:
    merged = pd.merge_asof(
        df_docker.sort_values("time"),
        df_health[["time", "temp_c"]].sort_values("time"),
        on="time",
        direction="nearest",
        tolerance=pd.Timedelta("15s"),
    ).dropna(subset=["temp_c"])

    if merged.empty:
        raise ValueError("Could not align health and docker logs for combined chart")

    fig, ax_cpu = plt.subplots(figsize=(12, 5))
    ax_temp = ax_cpu.twinx()

    ax_cpu.plot(merged["time"], merged["cpu_pct"], color="#1f77b4", linewidth=1.8, label="CPU %")
    ax_temp.plot(merged["time"], merged["temp_c"], color="#d62728", linewidth=1.8, label="Temperature (C)")

    ax_cpu.set_title("CPU Usage vs Device Temperature")
    ax_cpu.set_xlabel("Time")
    ax_cpu.set_ylabel("CPU %")
    ax_temp.set_ylabel("Temperature (C)")
    ax_cpu.grid(alpha=0.25)

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter("%H:%M:%S")
    ax_cpu.xaxis.set_major_locator(locator)
    ax_cpu.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    lines_1, labels_1 = ax_cpu.get_legend_handles_labels()
    lines_2, labels_2 = ax_temp.get_legend_handles_labels()
    ax_cpu.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot health and docker performance logs.")
    parser.add_argument("--health", type=Path, default=Path("test/health.log"), help="Path to health log")
    parser.add_argument("--docker", type=Path, default=Path("test/docker_stats.log"), help="Path to docker stats log")
    parser.add_argument("--out-dir", type=Path, default=Path("test/plots"), help="Output directory for chart images")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    health_df = parse_health_log(args.health)
    docker_df = parse_docker_stats_log(args.docker)

    save_health_chart(health_df, out_dir / "health_temp_throttle.png")
    save_docker_cpu_chart(docker_df, out_dir / "docker_cpu_usage.png")
    save_combined_chart(health_df, docker_df, out_dir / "cpu_vs_temp.png")

    print("Saved charts:")
    print(f"- {out_dir / 'health_temp_throttle.png'}")
    print(f"- {out_dir / 'docker_cpu_usage.png'}")
    print(f"- {out_dir / 'cpu_vs_temp.png'}")


if __name__ == "__main__":
    main()