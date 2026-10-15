@echo off
title JARVIS Personal AI Agent
cd /d "%~dp0"
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo JARVIS is starting at http://127.0.0.1:3000
echo If you have not configured your OpenAI key, edit .env first.
echo Press Ctrl+C to stop the server.
start "" http://127.0.0.1:3000
python app.py
pause
