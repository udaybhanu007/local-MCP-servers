#!/usr/bin/env python3
"""
MCP Neo4j Data Modeling Server Starter

Simple script to start the MCP Neo4j Data Modeling server with HTTP transport.
Uses OAuth credentials from .env file.
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

try:
    from oauth_helper import get_neo4j_credentials
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False


def start_mcp_data_modeling_server(port=None):
    """Start the MCP Neo4j Data Modeling server with HTTP transport"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get port from environment variable if not provided
    if port is None:
        port = int(os.getenv("DATA_MODELING_SERVER_PORT", 8004))
    
    print("🚀 Starting MCP Neo4j Data Modeling Server")
    print("=" * 45)
    print(f"🔗 Server URL: http://127.0.0.1:{port}/mcp/")
    print(f"📦 Transport: HTTP")
    print()
    
    # Get Neo4j connection details
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_database = os.getenv("NEO4J_DATABASE")
    
    # Try OAuth first, then fall back to username/password
    if OAUTH_AVAILABLE and os.getenv("CLIENT_ID") and os.getenv("CLIENT_SECRET"):
        print("🔐 Using OAuth authentication")
        try:
            neo4j_username, neo4j_password = get_neo4j_credentials()
        except Exception as e:
            print(f"⚠️  OAuth failed: {e}")
            print("🔑 Falling back to username/password authentication")
            neo4j_username = os.getenv("NEO4J_USERNAME")
            neo4j_password = os.getenv("NEO4J_PASSWORD")
    else:
        print("🔑 Using username/password authentication")
        neo4j_username = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_username, neo4j_password]):
        print("❌ Error: Missing required Neo4j credentials")
        print("💡 Please ensure .env contains either:")
        print("   • CLIENT_ID & CLIENT_SECRET for OAuth, OR")
        print("   • NEO4J_USERNAME & NEO4J_PASSWORD for basic auth")
        sys.exit(1)
    
    # Build command using the installed executable
    venv_path = os.path.dirname(sys.executable)
    mcp_executable = os.path.join(venv_path, "mcp-neo4j-data-modeling.exe")
    
    # Data modeling server uses environment variables, not command line args for DB connection
    env = os.environ.copy()
    env.update({
        "NEO4J_URI": neo4j_uri,
        "NEO4J_USERNAME": neo4j_username,
        "NEO4J_PASSWORD": neo4j_password,
        "NEO4J_DATABASE": neo4j_database or "neo4j"
    })
    
    cmd = [
        mcp_executable,
        "--transport", "http",
        "--server-host", "127.0.0.1",
        "--server-port", str(port),
        "--server-path", "/mcp/"
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print(f"🌍 Environment: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD set")
    print()
    print("📝 Press Ctrl+C to stop the server")
    print("-" * 30)
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("❌ Error: MCP Neo4j Data Modeling executable not found!")
        print("💡 Please install it first: pip install mcp-neo4j-data-modeling")
        print(f"💡 Looking for: {mcp_executable}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Load environment variables to get default port
    load_dotenv()
    default_port = int(os.getenv("DATA_MODELING_SERVER_PORT", 8004))
    
    # Allow port to be specified as command line argument
    port = default_port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid port: {sys.argv[1]}")
            sys.exit(1)

    start_mcp_data_modeling_server(port)
