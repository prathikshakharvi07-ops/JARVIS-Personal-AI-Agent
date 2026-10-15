# JARVIS — Personal AI Agent

A local Windows web dashboard inspired by the supplied NEXYRA concept: deep navy surfaces, cyan neon accents, AI chat, task activity, quick browser actions, and an OpenAI-powered assistant.

## Features in this starter

- Responsive dashboard + text chat.
- OpenAI chat completions with tool calling.
- Browser actions: ask JARVIS to open a public URL or search Google; these actions launch your Windows default browser.
- Task activity panel reports tool actions and errors.
- Status and integrations/settings screens.
- API key is stored locally in `.env`, not in frontend JavaScript.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- OpenAI API key with API access and billing/credits as applicable
- Internet connection for package installation, OpenAI API calls, and web search

## Quick start (Windows)

1. Extract the ZIP to a folder, for example `C:\JARVIS`.
2. Double-click `run_windows.bat`.
3. The first launch creates a Python virtual environment and installs dependencies.
4. Open `.env` in Notepad and replace `put_your_openai_api_key_here` with your own key.
5. Stop the server with Ctrl+C and run `run_windows.bat` again.
6. Visit `http://127.0.0.1:3000`.

You can also configure it manually:

```powershell
cd path\to\JARVIS_Personal_AI_Agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python app.py
```

Then visit `http://127.0.0.1:3000`.

## Example prompts

- `Open https://github.com in my browser`
- `Search the web for beginner AI/ML project ideas`
- `Help me plan a multi-step workflow to organize a coding project`
- `Open https://docs.python.org and explain what I should learn first`

## What works and what needs more setup

| Capability | Status |
|---|---|
| Dashboard and chat UI | Included |
| OpenAI-powered responses | Requires a valid `OPENAI_API_KEY` |
| Open public website in default browser | Included; Windows/browser settings apply |
| Google search in default browser | Included |
| Basic tool-call action log and error reporting | Included |
| Read/search content from pages automatically | Not included |
| Click buttons or submit forms on arbitrary websites | Not included |
| Sign in to websites, access email/calendar, or make purchases | Not included |
| Native Windows app control / file operations | Not included |
| Remote Android/device synchronization | Not included |
| Persistent task history / user accounts | Not included |

This is a runnable starter agent, not a fully autonomous cross-app operator. Browser launching is a real action, but it does not inspect the resulting page or verify that a website finished loading. The task monitor reports the browser-open request rather than confirming page content.

## Security notes

- Keep `.env` private and never commit it to GitHub.
- Do not paste API keys, passwords, or OTPs into chat.
- The server binds to `127.0.0.1` only. Do not change this to `0.0.0.0` unless you understand the security implications.
- The app intentionally does not submit forms, perform purchases, or operate authenticated sessions.
- OpenAI API usage can cost money. Review your provider usage limits.
- Google Fonts are loaded from the internet; the dashboard remains usable if the font request is blocked.

## Project structure

```text
JARVIS_Personal_AI_Agent/
├── app.py
├── requirements.txt
├── .env.example
├── run_windows.bat
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```

## Troubleshooting

- **`py` not recognized:** install Python from python.org and enable “Add Python to PATH”.
- **OpenAI key missing:** edit `.env`; ensure the file is named `.env`, not `.env.txt`.
- **Invalid key / API error:** verify the key and account API access. A ChatGPT subscription does not automatically include API credits.
- **Port 3000 is busy:** change `PORT=3000` in `.env` to another port, then restart.
- **Browser does not open:** check Windows default browser settings and whether the server process can launch applications.
