## Project Overview

Home Wearable Heart Disease Monitoring Device is an end-to-end ECG analytics system that connects a wearable sensor to a web dashboard and runs real-time feature extraction plus ML-based risk assessment. The project covers signal processing (Pan‑Tompkins++), feature engineering (ST/Oldpeak, HR), model training and ensembling, and a web UI for visualization and user onboarding.

### What This Project Does

- Collects ECG data from an ESP32 device and streams it to the backend
- Extracts physiological features (R‑peak, HR, ST/Oldpeak, ST‑Slope)
- Trains and evaluates multiple ML models, then ensembles top models for prediction
- Serves a web dashboard with authentication, live ECG, and health summary

### Technical Highlights

- **Signal Processing:** Pan‑Tompkins++ with ST‑focused filtering and fixed 160 Hz pipeline for stability  
- **Feature Pipeline:** Resting ECG classification (Normal / ST / LVH), HR metrics, ST slope  
- **Modeling:** CatBoost / Logistic Regression / Gradient Boosting + probability‑mean ensemble  
- **Backend:** Flask APIs + WebSocket streaming for ECG  
- **Frontend:** Static web dashboard with Google OAuth and charts  

### Key Components

- `backend/pan_tompkins_plus_plus`: ECG feature extraction, model training, prediction
- `backend/ecg_wifi.py`: real‑time ECG ingestion and streaming
- `frontend/`: dashboard UI, login, charts
- `ESP32/`: device code (data acquisition)

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
