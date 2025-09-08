#!/usr/bin/env python3
"""
Simple MCP Server Starter

Quick script to start the MCP Neo4j Data Modeling server with HTTP transport.
"""

import subprocess
import sys
import os


def start_mcp_data_modeling_server(port=8001):
    """Start the MCP server with the specified command"""
    
    print("🚀 Starting MCP Neo4j Data Modeling Server")
    print("=" * 45)
    print(f"🔗 Server URL: http://127.0.0.1:{port}/mcp/")
    print(f"📦 Transport: HTTP")
    print()
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "NEO4J_URI": "neo4j+s://b2b4aae0.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j", 
        "NEO4J_PASSWORD": "sIBdhIqkmmugcG2rB_7XhsbCbsAdCbT7mhUb54d7nQI",
        "NEO4J_DATABASE": "neo4j"
    })
    
    # Build command - exactly as specified by user
    cmd = [
        "uvx", 
        "mcp-neo4j-data-modeling@0.4.0", 
        "--transport", "http",
        "--server-port", str(port)
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print()
    print("📝 Press Ctrl+C to stop the server")
    print("-" * 30)
    
    try:
        # Run the command and let it handle its own output
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("❌ Error: 'uvx' command not found!")
        print("💡 Please install uv first: pip install uv")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Allow port to be specified as command line argument
    port = 8001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid port: {sys.argv[1]}")
            sys.exit(1)

    start_mcp_data_modeling_server(port)
