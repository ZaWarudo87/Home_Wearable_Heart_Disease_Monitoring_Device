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

> Portainer (the profiler) dashboard URL: http://localhost:9000

Goto **Containers > heart-monitor-backend > Stats** to get the result.

1. If you are using Windows, download Docker Desktop and open it.
2. `cd docker`.
3. Ensure your docker fully stopped.
```bash
docker-compose down
```
4. Build the docker image and start.
```bash
docker-compose up --build
```
