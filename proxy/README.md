# RetrOS Proxy (Skeleton)

This folder contains a minimal Flask-based proxy skeleton for US-2.1.

Prerequisites
- Python 3.9+
- (Recommended) Create a virtual environment

Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run
```powershell
python app.py
```

Health check
```powershell
Invoke-WebRequest http://127.0.0.1:9999/health
# or
curl http://127.0.0.1:9999/health
```

Notes
- The app listens on `127.0.0.1:9999` by default.
- CORS is enabled for development to allow the extension to call the proxy.
- `POST /api/generate-style` is a placeholder and returns `501 Not Implemented`.
