import os
import argparse
import pandas as pd


def split_csv_by_time(
    input_path: str,
    time_col: str = "timestamp",
    window_sec: int = 30,
    output_dir: str | None = None,
) -> None:
    if output_dir is None:
        output_dir = os.path.splitext(input_path)[0] + "_chunks"
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(input_path)

    if time_col not in df.columns:
        raise ValueError(f"Column '{time_col}' not found in CSV.")

    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    if df.empty:
        raise ValueError("No valid numeric time_stamp values found.")

    df = df.sort_values(time_col).reset_index(drop=True)

    start_time = df[time_col].iloc[0]
    # floor division to get window index
    df["_window_idx"] = ((df[time_col] - start_time) // window_sec).astype(int)

    base_name = os.path.splitext(os.path.basename(input_path))[0]

    for window_idx, group in df.groupby("_window_idx"):
        win_start_ts = group[time_col].iloc[0]
        win_end_ts = group[time_col].iloc[-1]

        out_name = f"{base_name}_chunk_{window_idx:04d}_{int(win_start_ts)}_{int(win_end_ts)}.csv"
        out_path = os.path.join(output_dir, out_name)

        group.drop(columns=["_window_idx"]).to_csv(out_path, index=False)
        print(f"Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Split CSV into 30-second chunks by UNIX time.")
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument(
        "--time-col",
        default="timestamp",
        help="Name of the UNIX time column (default: time_stamp).",
    )
    parser.add_argument(
        "--window-sec",
        type=int,
        default=30,
        help="Window size in seconds (default: 30).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save chunks (default: <input_basename>_chunks).",
    )

    args = parser.parse_args()

    split_csv_by_time(
        input_path=args.input_csv,
        time_col=args.time_col,
        window_sec=args.window_sec,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
