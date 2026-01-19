import os
import argparse
from collections import Counter

import numpy as np
import wfdb
import importlib


# ----------------------------------------------------------------------
# Helpers for reading local EDB records/annotations
# ----------------------------------------------------------------------

def get_edb_record_list(base_dir: str):
    """
    Read the local RECORDS file from the EDB folder and return a list
    of record names.
    """
    records_file = os.path.join(base_dir, "RECORDS")
    with open(records_file, "r") as f:
        records = [ln.strip() for ln in f if ln.strip()]
    return records


def load_st_peaks_edb_local(record_name: str, base_dir: str):
    """
    Load ST-episode peak annotations (AST...) from the local .atr file
    of an EDB record.

    Returns a list of dicts:
        { "sample": int, "signal": int (0 or 1), "sign": "Up" or "Down" }

    We parse annotations like:
        "AST0+600"  -> channel 0, ST elevation  -> sign = "Up"
        "AST1-150"  -> channel 1, ST depression -> sign = "Down"
    """
    recpath = os.path.join(base_dir, record_name)
    ann = wfdb.rdann(recpath, "atr")  # local read

    peaks = []

    for samp, aux in zip(ann.sample, ann.aux_note):
        if aux is None:
            continue
        txt = aux.strip()
        if not txt:
            continue

        # Only true ST-episode peaks: uppercase 'AST...' (axis shifts use lowercase)
        if not txt.startswith("AST"):
            continue
        if "ST" not in txt:
            continue

        i = txt.find("ST")
        if i < 0 or i + 4 > len(txt):
            continue

        # Signal index: 'ST0', 'ST1'
        ch_char = txt[i + 2]
        if not ch_char.isdigit():
            continue
        ch = int(ch_char)

        # Direction: '+' or '-'
        sign_char = txt[i + 3]
        if sign_char == "+":
            sign = "Up"
        elif sign_char == "-":
            sign = "Down"
        else:
            continue

        peaks.append(
            {
                "sample": int(samp),
                "signal": ch,
                "sign": sign,
            }
        )

    return peaks


# ----------------------------------------------------------------------
# Evaluation on a single record
# ----------------------------------------------------------------------

def evaluate_record(
    record_name: str,
    base_dir: str,
    detector_module,
    slope_thr: float,
    plot_dir: str | None = None,
    plot_max_per_record: int = 0,
):
    """
    Evaluate ST-slope classification for a single EDB record.

    `detector_module` is a Python module that must provide:
        - robust_r_peaks(sig, fs) -> np.ndarray of R-peak indices
        - st_slope_for_beat(sig, fs, r_idx, ...) -> (st_offset, st_slope)
        - classify_slope(slope, thr=0.5) -> 'Up'/'Down'/'Flat'

    If `plot_dir` is not None and the detector_module provides
    `plot_st_slope_beat(...)`, up to `plot_max_per_record` beats will
    be plotted and saved to that folder.
    """
    recpath = os.path.join(base_dir, record_name)
    record = wfdb.rdrecord(recpath)  # local read
    fs = float(record.fs)

    # p_signal: shape (nsamp, n_sig)
    sig = record.p_signal.T          # -> (n_sig, nsamp)

    st_peaks = load_st_peaks_edb_local(record_name, base_dir=base_dir)
    results = []

    # check if this detector has plotting support
    can_plot = plot_dir is not None and hasattr(detector_module, "plot_st_slope_beat")
    plotted = 0  # how many beats we have plotted for this record

    for ch in range(record.n_sig):
        sig_ch = sig[ch]
        ch_peaks = [ep for ep in st_peaks if ep["signal"] == ch]
        if not ch_peaks:
            continue

        # R-peaks from detector module
        r_peaks = detector_module.robust_r_peaks(sig_ch, fs)
        if r_peaks.size == 0:
            continue

        for ep_idx, ep in enumerate(ch_peaks):
            # Find nearest R-peak to the ST peak annotation sample
            idx = int(np.argmin(np.abs(r_peaks - ep["sample"])))
            r_idx = int(r_peaks[idx])

            # ST slope via detector module
            _, slope = detector_module.st_slope_for_beat(sig_ch, fs, r_idx)
            pred_label = detector_module.classify_slope(slope, thr=slope_thr)
            true_label = ep["sign"]

            results.append(
                (true_label, pred_label, slope, record_name, ch)
            )

            # Optional plotting
            if can_plot and plotted < plot_max_per_record:
                detector_module.plot_st_slope_beat(
                    sig=sig_ch,
                    fs=fs,
                    r_idx=r_idx,
                    slope=slope,
                    pred_label=pred_label,
                    true_label=true_label,
                    out_dir=plot_dir,
                    rec_name=record_name,
                    ch=ch,
                    beat_idx=ep_idx,
                )
                plotted += 1

    return results


# ----------------------------------------------------------------------
# Evaluation on the whole EDB (or subset)
# ----------------------------------------------------------------------

def evaluate_edb(
    base_dir: str,
    detector_module,
    max_records: int | None = None,
    slope_thr: float = 0.5,
    plot_dir: str | None = None,
    plot_max_per_record: int = 0,
):
    """
    Loop through local EDB records and compute a confusion matrix...

    If plot_dir is provided and the detector has `plot_st_slope_beat`,
    up to `plot_max_per_record` beats per record will be plotted.
    """
    record_list = get_edb_record_list(base_dir=base_dir)
    if max_records is not None:
        record_list = record_list[:max_records]

    all_results = []

    for i, rec in enumerate(record_list):
        print(f"[{i+1}/{len(record_list)}] Processing record {rec} ...")
        try:
            res = evaluate_record(
                rec,
                base_dir=base_dir,
                detector_module=detector_module,
                slope_thr=slope_thr,
                plot_dir=plot_dir,
                plot_max_per_record=plot_max_per_record,
            )
            all_results.extend(res)
        except Exception as e:
            print(f"  -> Error on {rec}: {e}")

    cm = Counter()
    for true_sign, pred_label, slope, rec, ch in all_results:
        cm[(true_sign, pred_label)] += 1

    print("\n=== ST Segment Classification (episode peaks) ===")
    print(f"Total episodes used: {sum(cm.values())}")
    print(f"Slope threshold: {slope_thr:.3f} mV/s\n")

    labels_pred = ["Up", "Down"]
    labels_true = ["Up", "Down"]

    header = "True\\Pred".ljust(10) + "".join(p.ljust(10) for p in labels_pred)
    print(header)
    print("-" * len(header))

    correct = 0
    total_for_acc = 0

    for t in labels_true:
        row = t.ljust(10)
        for p in labels_pred:
            c = cm[(t, p)]
            row += str(c).ljust(10)
        print(row)

        c_correct = cm[(t, t)]
        c_total_t = sum(cm[(t, p)] for p in labels_pred)
        correct += c_correct
        total_for_acc += c_total_t

    if total_for_acc > 0:
        acc = correct / total_for_acc * 100.0
        print(
            f"\nAccuracy: "
            f"{acc:.2f}%"
        )
    else:
        print("\nNo episodes found for accuracy computation.")

    return cm, all_results


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate ST-slope detector on PhysioNet EDB."
    )
    parser.add_argument(
        "--dl_dir",
        default="physionet.org/files/",
        help="Base directory where wfdb.dl_database('edb', dl_dir=...) stored the database.",
    )
    parser.add_argument(
        "--db",
        default="edb",
        help="Database name (default: edb).",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Database version (default: 1.0.0).",
    )
    parser.add_argument(
        "--detector",
        default="st_slope_detector_baseline",
        help="Detector module name (without .py). "
             "Must provide robust_r_peaks, st_slope_for_beat, classify_slope.",
    )
    parser.add_argument(
        "--max_records",
        type=int,
        default=None,
        help="Maximum number of records to evaluate (default: all).",
    )
    parser.add_argument(
        "--slope_thr",
        type=float,
        default=0.0,
        help="Slope threshold (mV/s) used inside classify_slope.",
    )
    parser.add_argument(
        "--plot_dir",
        default=None,
        help="If set, save beat-level ST plots into this folder (only "
             "for detectors that implement plot_st_slope_beat).",
    )
    parser.add_argument(
        "--plot_max_per_record",
        type=int,
        default=0,
        help="Maximum number of beats to plot per record (default: 0, no plots).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    base_dir = os.path.join(args.dl_dir, args.db, args.version)
    print(f"Using EDB base dir: {base_dir}")

    # Import detector module dynamically
    print(f"Importing detector module: {args.detector}")
    detector_module = importlib.import_module(args.detector)

    # Optional: sanity check that required functions exist
    for func_name in ["robust_r_peaks", "st_slope_for_beat", "classify_slope"]:
        if not hasattr(detector_module, func_name):
            raise AttributeError(
                f"Detector module '{args.detector}' is missing required "
                f"function '{func_name}'."
            )

    evaluate_edb(
        base_dir=base_dir,
        detector_module=detector_module,
        max_records=args.max_records,
        slope_thr=args.slope_thr,
        plot_dir=args.plot_dir,
        plot_max_per_record=args.plot_max_per_record,
    )


if __name__ == "__main__":
    main()
