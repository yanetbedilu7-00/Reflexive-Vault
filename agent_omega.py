from openai import OpenAI
from agent_auth import authenticate_agent, get_token_from_vault
from trust_engine import TrustScoreEngine
import os

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize trust engine
trust_engine = TrustScoreEngine()

class AgentOmega:
    def __init__(self):
        self.token = authenticate_agent()
        self.name = "Agent Omega"
        self.scopes = ["read:data", "analyze:data"]
    
    def execute_action(self, action, params):
        """Execute an action with security checks"""
        
        # Check trust score first
        if not trust_engine.is_authorized(action["required_scope"]):
            return {
                "status": "denied",
                "reason": f"Trust score {trust_engine.trust_score} too low. Immune response active."
            }
        
        # Execute based on action type
        if action["type"] == "github":
            token = get_token_from_vault("github")
            result = {"message": f"GitHub action on {params.get('repo', 'unknown')} completed"}
        
        elif action["type"] == "calendar":
            token = get_token_from_vault("google-calendar")
            result = {"message": "Calendar accessed successfully"}
        
        else:
            result = {"message": f"Executed {action['type']}"}
        
        # Log the action
        trust_engine.log_action(
            action=action["type"],
            scope=action["required_scope"],
            confidence=0.95,
            outcome="success"
        )
        
        return {"status": "success", "result": result}