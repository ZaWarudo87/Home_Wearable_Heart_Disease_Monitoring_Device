**Home_Wearable_Heart_Disease_Monitoring_Device**

2025 NYCU EE Project
Real-Time ECG Processing Pipeline Based on Pan-Tompkins++

Overview

This project implements a real-time ECG processing pipeline designed for wearable health-monitoring applications.

The system performs:

ECG acquisition (wearable sensor / ESP32 / serial)

Noise filtering and preprocessing

R-peak detection using Pan-Tompkins++ (improved version)

ST-segment slope and elevation analysis

Beat-to-beat feature extraction

Real-time visualization and batch processing for recorded ECG files

The objective is to create a portable and low-cost biomonitoring platform for long-term home cardiac monitoring and early detection of abnormalities.

Algorithm Foundation: Pan-Tompkins++

This project incorporates and extends the algorithm originally proposed in:

Pan-Tompkins++: A Robust Approach to Detect R-peaks in ECG Signals
Khan & Imtiaz, IEEE BIBM 2022 (CBPBL Workshop)
Paper: https://arxiv.org/abs/2211.03171

If you use this algorithm in academic work, please cite the original authors:

```bibtex
@article{khan2022pan,
  title={Pan-Tompkins++: A Robust Approach to Detect R-peaks in ECG Signals},
  author={Khan, Naimul and Imtiaz, Md Niaz},
  journal={arXiv preprint arXiv:2211.03171},
  year={2022}
}
```

**Usage**

1. Install Dependencies
```bash
pip install numpy scipy matplotlib peakutils
```

2. Prepare ECG Data

Place your ECG CSV files into:
```bash
ECG_DATA/
```


Move processed or unwanted files into:
```bash
ECG_DATA/used/
```

3. Run Batch Processing (R-peak detection + plots)
```bash
cd Pan-Tompkins-Plus-Plus
python test.py
```

**Output Example**
Example Terminal Output
```bash
[1/4] exercise_ecg | fs≈160.10 Hz (dt_mean=6.249 ms, std=2.664 ms) | peaks=63
result : MAX HR=200.0 bpm, ST_label=Up, Oldpeak=-0.253 mV
```

ECG Example


![ECG Example](Pan-Tompkins-Plus-Plus/assets/Figure_1.png)

**Key Features**

**Robust R-Peak Detection**

Optimized for noisy wearable environments using Pan-Tompkins++.

**ST-Segment Analysis**

Real-time calculation of ST elevation/depression and slope (Up / Flat / Down).

**AI Integration**

Connects signal-processing results with a trained ML model for immediate risk assessment.



