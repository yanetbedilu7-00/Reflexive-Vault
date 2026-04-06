# web_agent.py - WORKING VERSION
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import secrets
from datetime import datetime
import requests
import uvicorn

app = FastAPI(title="Reflexive Vault Agent")

# Create templates directory
TEMPLATES_DIR = Path("templates")
TEMPLATES_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory="templates")

# Create HTML template file if it doesn't exist
HTML_FILE = TEMPLATES_DIR / "index.html"
if not HTML_FILE.exists():
    HTML_CONTENT = '''<!DOCTYPE html>
<html>
<head>
    <title>Reflexive Vault Agent</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .trust-good {
            color: #28a745;
            font-size: 28px;
            font-weight: bold;
        }
        .trust-bad {
            color: #dc3545;
            font-size: 28px;
            font-weight: bold;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .answer {
            background: #e9ecef;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .error {
            color: red;
        }
        .audit-log {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            max-height: 200px;
            overflow-y: auto;
            font-size: 12px;
        }
        h1, h2, h3 {
            color: #333;
        }
    </style>
</head>
<body>
    <h1>Reflexive Vault Agent</h1>
    <p>Self-Defending AI Agent with Cryptographic Identity</p>

    <div class="card">
        <h2>Agent Status</h2>
        <p><strong>Agent ID:</strong> {{ agent_id }}</p>
        <p><strong>Trust Score:</strong> <span class="trust-good">{{ trust_score }}/100</span></p>
        <p><strong>Status:</strong> {{ trust_status }}</p>
        <p><strong>Total Actions:</strong> {{ total_actions }}</p>
    </div>

    <div class="card">
        <h2>Ask Your Agent</h2>
        <form method="post" action="/ask">
            <input type="text" name="question" placeholder="Type your question here..." required>
            <button type="submit">Ask</button>
        </form>

        {% if last_answer %}
        <div class="answer">
            <strong>You asked:</strong> {{ last_question }}<br><br>
            <strong>Agent Response:</strong> {{ last_answer }}
        </div>
        {% endif %}

        {% if error %}
        <div class="answer error">
            <strong>Error:</strong> {{ error }}
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h3>Audit Log</h3>
        <div class="audit-log">
            {% for log in audit_logs %}
            <p><strong>{{ log.timestamp[:19] }}</strong> - {{ log.action }} [{{ log.outcome }}]</p>
            {% endfor %}
            {% if not audit_logs %}
            <p>No actions logged yet. Ask a question to see audit entries.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>'''
    
    with open(HTML_FILE, 'w') as f:
        f.write(HTML_CONTENT)

# AIM Core setup
AIM_DIR = Path.home() / ".opena2a" / "aim-core"
AIM_DIR.mkdir(parents=True, exist_ok=True)
IDENTITY_FILE = AIM_DIR / "identity.json"

def get_identity():
    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, 'r') as f:
            return json.load(f)
    else:
        identity = {
            "agentId": f"agent_{secrets.token_hex(16)}",
            "agentName": "reflexive-vault",
            "createdAt": datetime.now().isoformat()
        }
        with open(IDENTITY_FILE, 'w') as f:
            json.dump(identity, f)
        return identity

def log_action(action, target, outcome):
    log_file = AIM_DIR / "audit.log"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "target": target,
        "outcome": outcome
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def get_trust_score():
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return 100
    
    with open(log_file, 'r') as f:
        logs = [json.loads(line) for line in f if line.strip()]
    
    total_actions = len(logs)
    if total_actions > 100:
        return 70
    elif total_actions > 50:
        return 85
    else:
        return 100

def get_audit_logs(limit=20):
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return []
    
    with open(log_file, 'r') as f:
        logs = [json.loads(line) for line in f if line.strip()]
    
    return logs[-limit:][::-1]

def ask_agent(question):
    """Call ClawRouter to get AI response"""
    try:
        response = requests.post(
            "http://127.0.0.1:8402/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "blockrun/free",
                "messages": [{"role": "user", "content": question}],
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data["choices"][0]["message"]["content"]
        else:
            return False, f"ClawRouter error: Status {response.status_code} - {response.text[:100]}"
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to ClawRouter. Make sure it's running in another terminal."
    except Exception as e:
        return False, f"Error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    identity = get_identity()
    trust_score = get_trust_score()
    logs = get_audit_logs(10)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "agent_id": identity["agentId"][:20] + "...",
        "trust_score": trust_score,
        "trust_status": "Healthy" if trust_score >= 70 else "Compromised",
        "total_actions": len(logs),
        "audit_logs": logs,
        "last_question": None,
        "last_answer": None,
        "error": None
    })

@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, question: str = Form(...)):
    identity = get_identity()
    
    # Log the request
    log_action("ai_request", question[:50], "pending")
    
    # Get AI response
    success, result = ask_agent(question)
    
    if success:
        log_action("ai_response", "success", "completed")
        error = None
        answer = result
    else:
        log_action("error", result[:50], "failed")
        error = result
        answer = None
    
    trust_score = get_trust_score()
    logs = get_audit_logs(10)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "agent_id": identity["agentId"][:20] + "...",
        "trust_score": trust_score,
        "trust_status": "Healthy" if trust_score >= 70 else "Compromised",
        "total_actions": len(logs),
        "audit_logs": logs,
        "last_question": question,
        "last_answer": answer,
        "error": error
    })

if __name__ == "__main__":
    print("=" * 50)
    print("Reflexive Vault Web Interface")
    print("=" * 50)
    print("Open http://localhost:8001 in your browser")
    print("Make sure ClawRouter is running in another terminal!")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8001)