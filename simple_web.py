from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
import json
import secrets
from pathlib import Path
from datetime import datetime
import uvicorn

app = FastAPI()

# Simple HTML page as a string
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Reflexive Vault</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
        input, button { padding: 10px; margin: 5px; }
        input { width: 70%; }
        button { background: blue; color: white; border: none; cursor: pointer; }
        .response { background: #f0f0f0; padding: 15px; margin-top: 20px; border-radius: 10px; }
        .trust { color: green; font-size: 24px; }
    </style>
</head>
<body>
    <h1>Reflexive Vault Agent</h1>
    <p>Agent ID: {{ agent_id }}</p>
    <p>Trust Score: <span class="trust">{{ trust_score }}/100</span></p>
    
    <form method="post">
        <input type="text" name="question" placeholder="Ask anything..." required>
        <button type="submit">Ask</button>
    </form>
    
    {% if answer %}
    <div class="response">
        <strong>Answer:</strong> {{ answer }}
    </div>
    {% endif %}
    
    {% if error %}
    <div class="response" style="background:#ffe0e0">
        <strong>Error:</strong> {{ error }}
    </div>
    {% endif %}
</body>
</html>
"""

# Setup AIM
AIM_DIR = Path.home() / ".opena2a" / "aim-core"
AIM_DIR.mkdir(parents=True, exist_ok=True)
IDENTITY_FILE = AIM_DIR / "identity.json"

def get_agent_id():
    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE) as f:
            return json.load(f)["agentId"][:20] + "..."
    else:
        aid = f"agent_{secrets.token_hex(16)}"
        with open(IDENTITY_FILE, 'w') as f:
            json.dump({"agentId": aid}, f)
        return aid[:20] + "..."

def get_trust():
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return 100
    with open(log_file) as f:
        lines = [l for l in f if l.strip()]
    total = len(lines)
    if total > 100:
        return 70
    elif total > 50:
        return 85
    return 100

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML.replace("{{ agent_id }}", get_agent_id()).replace("{{ trust_score }}", str(get_trust())).replace("{{ answer }}", "").replace("{{ error }}", "")

@app.post("/", response_class=HTMLResponse)
async def ask(question: str = Form(...)):
    # Log request
    log_file = AIM_DIR / "audit.log"
    with open(log_file, 'a') as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "action": "ask", "target": question[:50], "outcome": "pending"}) + '\n')
    
    # Call ClawRouter
    try:
        resp = requests.post(
            "http://127.0.0.1:8402/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={"model": "blockrun/free", "messages": [{"role": "user", "content": question}], "max_tokens": 500},
            timeout=30
        )
        
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"]
            outcome = "success"
            error = ""
        else:
            answer = ""
            outcome = "failed"
            error = f"API error: {resp.status_code}"
    except Exception as e:
        answer = ""
        outcome = "failed"
        error = str(e)
    
    # Log result
    with open(log_file, 'a') as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "action": "response", "outcome": outcome}) + '\n')
    
    html = HTML
    html = html.replace("{{ agent_id }}", get_agent_id())
    html = html.replace("{{ trust_score }}", str(get_trust()))
    html = html.replace("{{ answer }}", answer)
    html = html.replace("{{ error }}", error)
    
    return html

if __name__ == "__main__":
    print("Open http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)