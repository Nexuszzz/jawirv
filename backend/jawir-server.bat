@echo off
cd /d D:\expo\jawirv3\jawirv2\jawirv2\backend
echo Starting JAWIR Backend Server...
D:\expo\jawirv3\jawirv2\jawirv2\backend\venv_fresh\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
