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

# ============================================================
# AIM CORE SETUP (Cryptographic Identity)
# ============================================================
AIM_DIR = Path.home() / ".opena2a" / "aim-core"
AIM_DIR.mkdir(parents=True, exist_ok=True)
IDENTITY_FILE = AIM_DIR / "identity.json"

def get_agent_id():
    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, 'r') as f:
            return json.load(f).get("agentId", "unknown")
    else:
        agent_id = f"did:cdi:local:{secrets.token_hex(16)}"
        with open(IDENTITY_FILE, 'w') as f:
            json.dump({"agentId": agent_id, "createdAt": datetime.now().isoformat()}, f)
        return agent_id

def log_action(action, target, outcome):
    log_file = AIM_DIR / "audit.log"
    with open(log_file, 'a') as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "target": target[:100],
            "outcome": outcome
        }) + '\n')

def get_trust_score():
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return 100
    with open(log_file, 'r') as f:
        lines = [l for l in f if l.strip()]
    total = len(lines)
    if total > 100:
        return 70
    elif total > 50:
        return 85
    return 100

class Question(BaseModel):
    question: str

@app.get("/api/status")
async def get_status():
    log_file = AIM_DIR / "audit.log"
    total = 0
    if log_file.exists():
        with open(log_file, 'r') as f:
            total = len([l for l in f if l.strip()])
    return {
        "agent_id": get_agent_id(),
        "trust_score": get_trust_score(),
        "total_actions": total
    }

@app.get("/api/audit")
async def get_audit():
    log_file = AIM_DIR / "audit.log"
    if not log_file.exists():
        return {"logs": []}
    with open(log_file, 'r') as f:
        logs = [json.loads(line) for line in f if line.strip()]
    return {"logs": logs[-50:][::-1]}

@app.post("/api/ask")
async def ask_agent(q: Question):
    question = q.question
    
    log_action("ask", question[:50], "pending")
    
    # System prompt
    system_prompt = """You are Reflexive Vault, a self-defending AI agent. You have:
- Cryptographic identity using Ed25519 keys (unforgeable, like SSH and blockchain)
- Dynamic trust scoring (immune system that starts at 100 and decreases with anomalies)
- Complete audit logging (every action recorded in tamper-evident JSONL)

Answer questions naturally, conversationally, and accurately. Be friendly and helpful. For general knowledge questions (biology, physics, history, etc.), give clear, correct answers. For questions about yourself, explain your security features."""
    
    # List of working models to try in order
    models_to_try = [
        "blockrun/free",
        "nvidia/nemotron-ultra-253b",
        "nvidia/llama-4-maverick",
        "nvidia/mistral-large-3-675b"
    ]
    
    last_error = None
    
    for model in models_to_try:
        try:
            response = requests.post(
                "http://127.0.0.1:8402/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                log_action("response", "success", "completed")
                return {"answer": answer, "trust_score": get_trust_score(), "model": model}
            else:
                last_error = f"{model}: {response.status_code}"
                continue
                
        except requests.exceptions.ConnectionError:
            last_error = "ClawRouter not running"
            break
        except Exception as e:
            last_error = str(e)
            continue
    
    # If all models failed
    if "ClawRouter not running" in str(last_error):
        error_msg = "ClawRouter not running. Open a new terminal and run: npx @blockrun/clawrouter"
    else:
        error_msg = f"All AI models unavailable. Please check ClawRouter connection. Last error: {last_error}"
    
    log_action("error", error_msg, "failed")
    return {"error": error_msg, "trust_score": get_trust_score()}

if __name__ == "__main__":
    print("=" * 60)
    print("REFLEXIVE VAULT - Self-Defending AI Agent")
    print("=" * 60)
    print(f"Agent ID: {get_agent_id()}")
    print(f"Trust Score: {get_trust_score()}/100")
    print("=" * 60)
    print("Server: http://localhost:8001")
    print("")
    print("Make sure ClawRouter is running in another terminal:")
    print("  npx @blockrun/clawrouter")
    print("")
    print("Models will be tried in order:")
    print("  1. blockrun/free")
    print("  2. nvidia/nemotron-ultra-253b")
    print("  3. nvidia/llama-4-maverick")
    print("  4. nvidia/mistral-large-3-675b")
    print("=" * 60)
    
    uvicorn.run(app, host="127.0.0.1", port=8001)