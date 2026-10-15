
import os
import json
import webbrowser
from urllib.parse import urlparse, quote_plus

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

# Load local .env variables when running on your own computer.
# Vercel supplies environment variables through project settings.
load_dotenv()

app = Flask(__name__)

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

client = (
    OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    if GROQ_API_KEY
    else None
)

SYSTEM_PROMPT = """You are JARVIS, a helpful personal AI assistant.
You can chat, plan tasks, and use the provided browser tools.

Use browser_open only when the user explicitly asks to open a
website or URL. Use web_search when the user asks to search the
web or find current information.

Never claim an action happened unless the tool result confirms it.
Never ask for passwords, OTPs, or API keys.
Do not perform purchases, financial transactions, account changes,
or submit forms.

Browser tools are limited to opening public pages and initiating
Google searches. Explain these limitations clearly.
Keep responses concise and helpful.
"""


def browser_open(url):
    """Validate a public HTTP(S) URL and request opening it."""
    url = (url or "").strip()

    if not url:
        return {"ok": False, "error": "No URL supplied."}

    if not url.startswith(("https://", "http://")):
        url = "https://" + url

    parsed = urlparse(url)

    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
    ):
        return {
            "ok": False,
            "error": "Only valid public HTTP(S) URLs are allowed.",
        }

    try:
        opened = webbrowser.open(url, new=2)

        return {
            "ok": bool(opened),
            "url": url,
            "message": (
                f"Requested opening {url} in the server's browser."
                if opened
                else "The server could not open the URL automatically."
            ),
            "note": (
                "When hosted on Vercel, this does not open a browser "
                "on your personal Windows computer."
            ),
        }
    except Exception:
        return {
            "ok": False,
            "url": url,
            "error": "Unable to open the URL from the server.",
        }


def web_search(query):
    """Create a Google search URL and request opening it."""
    query = (query or "").strip()

    if not query:
        return {"ok": False, "error": "Please provide a search query."}

    search_url = (
        "https://www.google.com/search?q=" + quote_plus(query)
    )

    return browser_open(search_url)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": (
                "Request opening a public website when the user "
                "explicitly asks to visit a URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Initiate a Google search when the user asks "
                "to search for information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify({
        "ok": True,
        "app": "JARVIS",
        "ai_configured": bool(GROQ_API_KEY),
        "model": GROQ_MODEL,
        "browser_actions": True,
        "message": "JARVIS server is running.",
    })


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    messages = body.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return jsonify({
            "error": "Send a non-empty messages array."
        }), 400

    if client is None:
        return jsonify({
            "error": (
                "Groq API key is not configured. "
                "Add GROQ_API_KEY in Vercel Environment Variables."
            )
        }), 503

    safe_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    for item in messages[-16:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role in ("user", "assistant") and isinstance(content, str):
            safe_messages.append({
                "role": role,
                "content": content[:12000],
            })

    if len(safe_messages) == 1:
        return jsonify({
            "error": "No valid chat messages were supplied."
        }), 400

    actions = []

    try:
        # Allow a maximum of four model/tool-calling rounds.
        for _ in range(4):
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=safe_messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.4,
            )

            msg = response.choices[0].message

            # The model has finished responding.
            if not msg.tool_calls:
                return jsonify({
                    "reply": (
                        msg.content
                        or "I couldn't generate a response."
                    ),
                    "actions": actions,
                })

            # Add the assistant's tool-call message to the conversation.
            safe_messages.append(
                msg.model_dump(exclude_none=True)
            )

            # Run each tool requested by the model.
            for tool_call in msg.tool_calls:
                name = tool_call.function.name

                try:
                    args = json.loads(
                        tool_call.function.arguments or "{}"
                    )
                except (json.JSONDecodeError, TypeError):
                    args = {}

                if not isinstance(args, dict):
                    args = {}

                if name == "browser_open":
                    result = browser_open(args.get("url", ""))
                elif name == "web_search":
                    result = web_search(args.get("query", ""))
                else:
                    result = {
                        "ok": False,
                        "error": "Unsupported tool.",
                    }

                actions.append({
                    "tool": name,
                    **result,
                })

                safe_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

        return jsonify({
            "reply": (
                "I reached the tool-call limit. "
                "Please break the task into smaller steps."
            ),
            "actions": actions,
        })

    except Exception as exc:
        # The exception is returned for troubleshooting.
        # Never include the API key in an error message.
        print(f"JARVIS AI request failed: {type(exc).__name__}: {exc}")

        return jsonify({
            "error": (
                "The AI request failed. Check your Groq API key, "
                "model availability, usage limits, and deployment logs."
            )
        }), 502


@app.post("/api/action")
def action():
    """Handle explicit navigation and search shortcut requests."""
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")

    if kind == "open":
        return jsonify(browser_open(body.get("url", "")))

    if kind == "search":
        return jsonify(web_search(body.get("query", "")))

    return jsonify({
        "ok": False,
        "error": "Unsupported action.",
    }), 400


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "3000")),
        debug=False,
    )
