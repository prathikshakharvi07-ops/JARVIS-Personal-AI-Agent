import os
import json
import threading
import webbrowser
from urllib.parse import urlparse, quote_plus

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

load_dotenv()
app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are JARVIS, a helpful Windows personal AI agent.
You can chat, plan multi-step tasks, and use the provided browser tools.
Use browser_open only when the user explicitly asks to open/visit a website or a URL.
Use web_search when the user asks to search the web or current information.
Do not claim an action happened unless a tool result confirms it.
Never ask for passwords, OTPs, or API keys in chat. Do not perform purchases,
financial transactions, account changes, or submit forms. Browser tools are limited
to opening public pages and searching; explain these limits clearly.
Keep responses concise and show what was actually done.
"""

def browser_open(url):
    """Open a public HTTP(S) URL in the user's default Windows browser."""
    url = (url or "").strip()
    if not url:
        return {"ok": False, "error": "No URL supplied."}
    if not url.startswith(("https://", "http://")):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {"ok": False, "error": "Only valid HTTP(S) URLs are allowed."}
    try:
        opened = webbrowser.open(url, new=2)
        return {"ok": bool(opened), "message": f"Requested opening {url} in your default browser.", "url": url,
                "note": "Windows/browser settings determine which browser opens."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

def web_search(query):
    """Open a public web search in the default browser."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "Please provide a search query."}
    url = "https://www.google.com/search?q=" + quote_plus(query)
    return browser_open(url)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": "Open a public website URL in the user's default browser. Only for explicitly requested navigation.",
            "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"], "additionalProperties": False}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Open a Google search for a query in the user's default browser.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}
        }
    }
]

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/status")
def status():
    return jsonify({
        "ok": True,
        "app": "JARVIS",
        "ai_configured": bool(os.getenv("GROQ_API_KEY")),
        "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        "browser_actions": True,
        "message": "Local server is running."
    })

@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    messages = body.get("messages", [])
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Send a non-empty messages array."}), 400
    if not client:
        return jsonify({
            "error": "Groq API key is not configured. Add GROQ_API_KEY in Vercel Environment Variables."
        }), 503
    safe_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in messages[-16:]:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            safe_messages.append({"role": role, "content": content[:12000]})
    try:
        actions = []
        for _ in range(4):
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=safe_messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.4
            )
            msg = response.choices[0].message
            if not msg.tool_calls:
                return jsonify({"reply": msg.content or "I couldn't generate a response.", "actions": actions})
            safe_messages.append(msg.model_dump(exclude_none=True))
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                if name == "browser_open":
                    result = browser_open(args.get("url", ""))
                elif name == "web_search":
                    result = web_search(args.get("query", ""))
                else:
                    result = {"ok": False, "error": "Unsupported tool."}
                actions.append({"tool": name, **result})
                safe_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        return jsonify({"reply": "I reached the tool-call limit for this request. Please break the task into smaller steps.", "actions": actions})
    except Exception as exc:
        return jsonify({"error": f"AI request failed: {exc}"}), 502

@app.post("/api/action")
def action():
    """Explicit, simple action endpoint for UI shortcuts."""
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    if kind == "open":
        return jsonify(browser_open(body.get("url", "")))
    if kind == "search":
        return jsonify(web_search(body.get("query", "")))
    return jsonify({"ok": False, "error": "Unsupported action."}), 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "3000")), debug=False)
