# 🔧 Quick Fix: Python Environment

## Problem Detected
All Python installations broken with error:
```
No Python at 'C:\Users\NAUFAL\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe'
```

## Solution Options

### Option 1: Fresh Python Install (RECOMMENDED)
```powershell
# 1. Download Python 3.11 or 3.12 from python.org
# 2. Install with "Add to PATH" checked
# 3. Test:
python --version
pip --version

# 4. Install dependencies:
cd D:\expo\jawirv3\jawirv2\jawirv2\backend
pip install -r requirements.txt
```

### Option 2: Create Fresh venv
```powershell
cd D:\expo\jawirv3\jawirv2\jawirv2\backend

# Create new venv
python -m venv venv_fresh

# Activate
.\venv_fresh\Scripts\Activate.ps1

# Install
pip install fastapi uvicorn httpx pydantic langchain-core langchain-google-genai

# Test Polinema API
cd polinema-connector
python polinema_api_server.py
```

### Option 3: Use Anaconda/Miniconda
```powershell
# If you have Conda:
conda create -n jawir python=3.11
conda activate jawir
pip install fastapi uvicorn httpx pydantic
```

## After Fix, Run:
```powershell
cd D:\expo\jawirv3\jawirv2\jawirv2\backend\polinema-connector
.\test_polinema_api.ps1
```

This will test all endpoints automatically!
