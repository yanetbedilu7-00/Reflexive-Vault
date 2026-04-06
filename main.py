from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_omega import AgentOmega
from trust_engine import TrustScoreEngine

# Initialize
app = FastAPI()
agent = AgentOmega()
trust_engine = TrustScoreEngine()

# Enable CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ActionRequest(BaseModel):
    action_type: str
    params: dict
    justification: str = None

# API Endpoint 1: Execute action
@app.post("/api/agent/act")
async def agent_act(request: ActionRequest):
    action_map = {
        "read_github": {"type": "github", "required_scope": "read:data", "params": request.params},
        "write_github": {"type": "github", "required_scope": "write:data", "params": request.params},
        "get_calendar": {"type": "calendar", "required_scope": "read:data", "params": request.params}
    }
    
    if request.action_type not in action_map:
        raise HTTPException(status_code=400, detail="Unknown action")
    
    result = agent.execute_action(action_map[request.action_type], request.params)
    return result

# API Endpoint 2: Check trust score
@app.get("/api/agent/trust-score")
async def get_trust_score():
    score = trust_engine.calculate_trust_score()
    return {
        "trust_score": score,
        "threshold": 70,
        "status": "HEALTHY" if score >= 70 else "COMPROMISED",
        "message": "Agent immune system active" if score < 70 else "Agent operating normally"
    }

# API Endpoint 3: View audit log
@app.get("/api/agent/audit-log")
async def get_audit_log():
    cursor = trust_engine.conn.cursor()
    cursor.execute('''
        SELECT timestamp, action, scope_requested, confidence, outcome 
        FROM agent_actions 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''')
    logs = cursor.fetchall()
    
    return {"audit_log": [
        {
            "timestamp": l[0], 
            "action": l[1], 
            "scope": l[2], 
            "confidence": l[3], 
            "outcome": l[4]
        } 
        for l in logs
    ]}

# API Endpoint 4: Home page
@app.get("/")
async def home():
    return {
        "agent": "Agent Omega",
        "status": "running",
        "features": ["Token Vault", "Trust Score", "Immune Response", "Audit Log"],
        "endpoints": ["/api/agent/act", "/api/agent/trust-score", "/api/agent/audit-log"]
    }

# Run the server
if __name__ == "__main__":
    import uvicorn
    print("🚀 Agent Omega starting...")
    print("📍 Trust Score endpoint: http://localhost:8000/api/agent/trust-score")
    print("📍 Audit Log endpoint: http://localhost:8000/api/agent/audit-log")
    print("📍 Act endpoint: http://localhost:8000/api/agent/act")
    uvicorn.run(app, host="0.0.0.0", port=8000)