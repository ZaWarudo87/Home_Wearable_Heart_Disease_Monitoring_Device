## Project Overview

Home Wearable Heart Disease Monitoring Device is an end-to-end ECG analytics system for continuous heart monitoring on an edge-device workflow. The system connects ECG acquisition hardware to a backend service, extracts structured physiological features in real time, performs ML-based heart disease risk assessment, and streams live results to a web dashboard. The current version also includes AF screening based on RR-interval coefficient-of-variation logic for longer-duration rhythm monitoring.

### What This Project Does

- Collects ECG data from an ESP32 device or simulator and streams it to the backend
- Detects R-peaks and extracts physiological features such as heart rate, ST slope, Oldpeak, and RestingECG status
- Screens AF from streaming ECG chunks using RR-interval CV with temporal persistence logic
- Trains and evaluates multiple ML models, then uses an ensemble for heart disease risk prediction
- Serves a web dashboard with authentication, live ECG, AF status, and health summary

### Technical Highlights

- **Signal Processing:** Pan-Tompkins++ based ECG processing with a fixed 160 Hz pipeline
- **Feature Pipeline:** Structured feature extraction for MaxHR, Oldpeak, ST slope, RestingECG, and related risk inputs
- **AF Detection:** Streaming RR-based AF screening with refractory filtering, rolling windows, and persistence-based decision logic
- **Modeling:** CatBoost / Logistic Regression / Gradient Boosting ensemble for heart disease risk prediction
- **Backend:** Flask APIs + WebSocket streaming for live ECG, mode status, and AF payloads
- **Frontend:** Modular web dashboard with Google OAuth, charts, risk view, and real-time ECG display

### Attribution

- The `Pan-Tompkins++` R-peak detection module used in this project is adapted from the authors' public implementation accompanying:
  - Khan, N., and Imtiaz, M. N. (2022). `Pan-Tompkins++: A Robust Approach to Detect R-peaks in ECG Signals`. arXiv:2211.03171
- Our version is trimmed and integrated for this project's ECG feature extraction pipeline and deployment workflow.

### Key Components

- `backend/pan_tompkins_plus_plus`: ECG feature extraction, model training, and risk prediction
- `backend/AF_detection.py`: streaming AF screening logic based on RR interval variation
- `backend/ecg_wifi.py`: real-time ECG ingestion, feature updates, AF updates, and WebSocket data source
- `backend/backend_main.py`: API server and WebSocket endpoint
- `frontend/`: modular dashboard UI, authentication flow, charts, ECG, and risk views
- `ESP32/`: device-side data acquisition and ECG simulation utilities

## Environment Settings

> Please at least use a virtual environment to keep your Python environment clean!

### venv Usage

1. If you haven't install Python, pip, or venv, you can try these commands on your Linux system (or WSL if you are using Windows OS). However, I recommend you asking LLM for how to do these on your OS because I'm not sure how to keep your python command as `python` and the version is 3.1X.
```bash
sudo apt update
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3-venv
```
2. Construct an empty venv. You can name your venv yourself but I strongly recommand you just keep it named "venv". **Please make sure your path is under this project's root.**
```bash
python -m venv venv
```
3. Activate the venv. After this step, you will successfully entered your virtual environment. You can happily install Python packages and never ruin your environment on your PC.
```bash
python -m venv venv
```
4. Install our Python packages.
```bash
pip install -r requirements.txt
```
5. If you add or remove any packages, please run this to let us can standardize our environment.
```bash
pip freeze > requirements.txt
```

### Docker Usage

Under construction.

> Portainer (the profiler) dashboard URL: http://localhost:9000

Goto **Containers > heart-monitor-backend > Stats** to get the result.

1. If you are using Windows, download Docker Desktop and open it.
2. `cd docker`.
3. Log in to ghcr.io with your GitHub account.
```bash
export CR_PAT=YOUR_GITHUB_TOKEN
echo $CR_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```
4. Pull the docker image.
```bash
docker pull ghcr.io/YOUR_GITHUB_USERNAME/home_wearable_heart_disease_monitoring_device:latest
```
5. Check the image name in `docker-compose.yml` line 7 is same as the image you pulled.
6. Ensure your docker fully stopped.
```bash
docker-compose down
```
7. Build the docker image and start.
```bash
docker-compose up
```
