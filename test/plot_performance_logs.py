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


def save_temperature_chart(df_health: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(df_health["time"], df_health["temp_c"], color="#d62728", linewidth=2.2, label="Temperature (C)")

    ax.set_title("Device Temperature Over Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (C)")

    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter("%H:%M:%S")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    ax.legend(loc="upper left")
    ax.grid(alpha=0.25)

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

    save_temperature_chart(health_df, out_dir / "device_temperature.png")
    save_docker_cpu_chart(docker_df, out_dir / "docker_cpu_usage.png")

    print("Saved charts:")
    print(f"- {out_dir / 'device_temperature.png'}")
    print(f"- {out_dir / 'docker_cpu_usage.png'}")


if __name__ == "__main__":
    main()