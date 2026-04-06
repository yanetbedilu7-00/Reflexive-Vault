import requests
import os
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv('AUTH0_DOMAIN')
CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET')

def authenticate_agent():
    """Get authentication token for the agent"""
    url = f"https://{DOMAIN}/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": f"https://{DOMAIN}/api/v2/",
        "grant_type": "client_credentials"
    }
    response = requests.post(url, json=payload)
    return response.json().get("access_token")

def get_token_from_vault(service):
    """Get service-specific token from Auth0 Token Vault"""
    agent_token = authenticate_agent()
    
    url = f"https://{DOMAIN}/oauth/token"
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "subject_token": agent_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": f"https://{service}.api.com"
    }
    response = requests.post(url, json=payload)
    return response.json().get("access_token")