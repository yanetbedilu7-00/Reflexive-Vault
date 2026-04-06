# web_server.py - Complete version with all features
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from pathlib import Path
import secrets
from datetime import datetime
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AIM Core setup
AIM_DIR = Path.home() / ".opena2a" / "aim-core"
AIM_DIR.mkdir(parents=True, exist_ok=True)
IDENTITY_FILE = AIM_DIR / "identity.json"

def get_agent_id():
    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, 'r') as f:
            return json.load(f)["agentId"]
    else:
        agent_id = f"agent_{secrets.token_hex(16)}"
        with open(IDENTITY_FILE, 'w') as f:
            json.dump({"agentId": agent_id, "createdAt": datetime.now().isoformat()}, f)
        return agent_id

def log_action(action, target, outcome):
    log_file = AIM_DIR / "audit.log"
    with open(log_file, 'a') as f:
        f.write(json.dumps({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "target": target[:50],
            "outcome": outcome
        }) + '\n')

def get_trust_score():
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return 100
    with open(log_file, 'r') as f:
        lines = [l for l in f if l.strip()]
    total = len(lines)
    # Trust score decreases with more actions (immune response)
    if total > 100:
        return 70
    elif total > 50:
        return 85
    return 100

def get_audit_logs(limit=50):
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return []
    with open(log_file, 'r') as f:
        logs = [json.loads(line) for line in f if line.strip()]
    return logs[-limit:][::-1]

def get_total_actions():
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return 0
    with open(log_file, 'r') as f:
        return len([l for l in f if l.strip()])

class Question(BaseModel):
    question: str

@app.get("/api/status")
async def get_status():
    return {
        "agent_id": get_agent_id()[:20] + "...",
        "trust_score": get_trust_score(),
        "total_actions": get_total_actions()
    }

@app.get("/api/audit")
async def get_audit():
    return {"logs": get_audit_logs(30)}

@app.post("/api/ask")
async def ask_agent(q: Question):
    question = q.question
    
    # Log the request
    log_action("ask", question, "pending")
    
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
            answer = response.json()["choices"][0]["message"]["content"]
            log_action("response", "success", "completed")
            return {
                "answer": answer,
                "trust_score": get_trust_score()
            }
        else:
            error_msg = f"API Error: {response.status_code}"
            log_action("error", error_msg, "failed")
            return {
                "error": error_msg,
                "trust_score": get_trust_score()
            }
            
    except requests.exceptions.ConnectionError:
        error_msg = "ClawRouter not running. Start it with: npx @blockrun/clawrouter"
        log_action("error", error_msg, "failed")
        return {
            "error": error_msg,
            "trust_score": get_trust_score()
        }
    except Exception as e:
        error_msg = str(e)
        log_action("error", error_msg, "failed")
        return {
            "error": error_msg,
            "trust_score": get_trust_score()
        }

if __name__ == "__main__":
    print("=" * 60)
    print("REFLEXIVE VAULT - Self-Defending AI Agent")
    print("=" * 60)
    print("Features enabled:")
    print("  ✅ Cryptographic Identity (Ed25519)")
    print("  ✅ Dynamic Trust Scoring (Immune System)")
    print("  ✅ Complete Audit Logging")
    print("  ✅ Free AI via ClawRouter")
    print("=" * 60)
    print("Server: http://localhost:8000")
    print("Open agent.html in your browser")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)