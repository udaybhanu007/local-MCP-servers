#!/usr/bin/env python3
"""
Neo4j OAuth Helper

Helper script to authenticate with Neo4j using OAuth credentials
and obtain connection details for MCP servers.
"""

import os
import requests
from dotenv import load_dotenv


def get_neo4j_oauth_token():
    """Get Neo4j OAuth token using client credentials"""
    load_dotenv()
    
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in .env file")
    
    # Neo4j OAuth endpoint for AuraDB
    token_url = "https://api.neo4j.io/oauth/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    return response.json()["access_token"]


def get_neo4j_credentials():
    """Get Neo4j username and password using OAuth"""
    load_dotenv()
    
    try:
        token = get_neo4j_oauth_token()
        # For AuraDB, you can use the token as password with username "neo4j"
        return "neo4j", token
    except Exception as e:
        print(f"❌ OAuth authentication failed: {e}")
        print("💡 Falling back to environment variables NEO4J_USERNAME and NEO4J_PASSWORD")
        return os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")


if __name__ == "__main__":
    try:
        username, password = get_neo4j_credentials()
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password) if password else 'None'}")
    except Exception as e:
        print(f"Error: {e}")
