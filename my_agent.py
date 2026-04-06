# my_agent.py - CORRECTED VERSION
import json
import os
from pathlib import Path
from openai import OpenAI

# AIM Core directory
AIM_DIR = Path.home() / ".opena2a" / "aim-core"
AIM_DIR.mkdir(parents=True, exist_ok=True)
IDENTITY_FILE = AIM_DIR / "identity.json"

def get_or_create_identity():
    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, 'r') as f:
            return json.load(f)
    else:
        import secrets
        identity = {
            "agentId": f"agent_{secrets.token_hex(16)}",
            "agentName": "hackathon-agent",
            "createdAt": __import__('datetime').datetime.now().isoformat()
        }
        with open(IDENTITY_FILE, 'w') as f:
            json.dump(identity, f)
        return identity

def log_action(action, target, outcome):
    log_file = AIM_DIR / "audit.log"
    import datetime
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "target": target,
        "outcome": outcome
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def calculate_trust_score():
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

# Get agent identity
identity = get_or_create_identity()
print(f"🤖 Agent ID: {identity['agentId']}")
print(f"📛 Agent Name: {identity['agentName']}")
print(f"🛡️ Trust Score: {calculate_trust_score()}/100")

# Connect to ClawRouter
client = OpenAI(
    base_url="http://127.0.0.1:8402/v1/",
    api_key="x402"
)

print("\n✅ Agent is ready! Type 'exit' to quit")
print("-" * 40)

while True:
    user_input = input("\n💬 You: ")
    if user_input.lower() == 'exit':
        break
    
    try:
        log_action("ai_request", user_input[:50], "pending")
        
        # USE ONE OF THESE WORKING MODEL NAMES:
        # Option 1: FREE model (recommended)
        response = client.chat.completions.create(
            model="blockrun/free",  # ✅ WORKING FREE MODEL
            messages=[{"role": "user", "content": user_input}],
            max_tokens=500
        )
        
        # Option 2: Automatic routing (starts with free models)
        # response = client.chat.completions.create(
        #     model="blockrun/free",  # Forces only free models
        #     messages=[{"role": "user", "content": user_input}],
        #     max_tokens=500
        # )
        
        result = response.choices[0].message.content
        print(f"\n🤖 Agent: {result}")
        
        log_action("ai_response", "success", "completed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        log_action("error", str(e), "failed")

print("\n👋 Goodbye!")