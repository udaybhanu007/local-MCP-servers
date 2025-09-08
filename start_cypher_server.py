#!/usr/bin/env python3
"""
MCP Neo4j Cyphe    print(f"🔧 Command: {' '.join(cmd)}")
    print(f"🌐 Server URL: http://127.0.0.1:8002/mcp/")
    print(f"🔐 Environment: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD set")
    print()
    print("📝 Press Ctrl+C to stop the server")
    print("-" * 65)er with HTTP Transport (Fixed Implementation)

This script starts the MCP Neo4j Cypher server using the correct configuration
based on PyPI documentation analysis.
"""

import subprocess
import sys
import os


def start_cypher_server_http():
    """Start the MCP Neo4j Cypher server with correct HTTP transport configuration"""
    
    print("🚀 Starting MCP Neo4j Cypher Server (FIXED - HTTP Transport)")
    print("=" * 65)
    print("🔗 Transport: HTTP")
    print("🏷️  Package: mcp-neo4j-cypher (latest)")
    print("🏢 Database: neo4j+s://b2b4aae0.databases.neo4j.io")
    print("🔌 Port: 8002")
    print("📍 Path: /mcp/ (default)")
    print("✅ Configuration based on working tests")
    print()
    
    # Set environment variables (preferred method per PyPI docs)
    env = os.environ.copy()
    env.update({
        "NEO4J_URI": "neo4j+s://b2b4aae0.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "sIBdhIqkmmugcG2rB_7XhsbCbsAdCbT7mhUb54d7nQI",
        "NEO4J_DATABASE": "neo4j"
    })
    
    # Build command using correct parameters
    cmd = [
        "uvx",
        "mcp-neo4j-cypher",  # Use latest version
        "--transport", "http",
        "--server-port", "8002"
        # Remove --server-path to use default /mcp/
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print(f"🌐 Server URL: http://127.0.0.1:8002/api/mcp/")
    print(f"� Environment: NEO4J_URI, NEO4J_USERNAME, etc. set")
    print()
    print("📝 Press Ctrl+C to stop the server")
    print("-" * 65)
    
    try:
        # Run the command with environment variables
        subprocess.run(cmd, check=True, text=True, env=env)
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
    print("🖥️  MCP Neo4j Cypher Server (HTTP Transport)")
    print("=" * 50)
    print("⚙️  Configuration:")
    print("   • Transport: HTTP (Streamable-HTTP)")
    print("   • Port: 8002")
    print("   • Database: neo4j+s://b2b4aae0.databases.neo4j.io")
    print("   • URL: http://127.0.0.1:8002/mcp/")
    print("   • Status: ✅ Fixed Configuration")
    print()
    
    start_cypher_server_http()
