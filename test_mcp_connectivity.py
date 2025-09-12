#!/usr/bin/env python3
"""
Test MCP servers connectivity and capabilities
"""

import requests
import json

def test_server_connectivity(url, server_name):
    """Test basic connectivity to MCP server"""
    print(f"🔍 Testing {server_name} at {url}")
    
    try:
        # Test basic HTTP GET
        response = requests.get(url, timeout=5)
        print(f"  GET response status: {response.status_code}")
        
        # Test MCP initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=init_request, headers=headers, timeout=10)
        print(f"  Initialize response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ {server_name} is responding correctly")
            print(f"  Server capabilities: {result.get('result', {}).get('capabilities', {})}")
            return True
        else:
            print(f"  ❌ {server_name} returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error connecting to {server_name}: {e}")
        return False

def test_cypher_execution():
    """Test Cypher query execution"""
    print("\n🧪 Testing Cypher execution...")
    
    cypher_url = "http://127.0.0.1:8003/mcp/"
    
    # Simple test query
    test_query = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "run_cypher",
            "arguments": {
                "query": "RETURN 'Hello Neo4j!' as message, datetime() as timestamp"
            }
        }
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(cypher_url, json=test_query, headers=headers, timeout=10)
        print(f"  Cypher test response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Cypher execution successful!")
            print(f"  Result: {result}")
            return True
        else:
            print(f"  ❌ Cypher test failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing Cypher: {e}")
        return False

def list_available_tools(url, server_name):
    """List available tools from MCP server"""
    print(f"\n🔧 Listing tools for {server_name}...")
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=tools_request, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            print(f"  Available tools ({len(tools)}):")
            for tool in tools:
                print(f"    - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            return tools
        else:
            print(f"  ❌ Failed to list tools: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"  ❌ Error listing tools: {e}")
        return []

if __name__ == "__main__":
    print("🚀 Testing MCP Servers Connectivity")
    print("=" * 50)
    
    # Test both servers
    cypher_url = "http://127.0.0.1:8003/mcp/"
    modeling_url = "http://127.0.0.1:8004/mcp/"
    
    cypher_ok = test_server_connectivity(cypher_url, "Cypher Server")
    modeling_ok = test_server_connectivity(modeling_url, "Data Modeling Server")
    
    if cypher_ok:
        list_available_tools(cypher_url, "Cypher Server")
        test_cypher_execution()
    
    if modeling_ok:
        list_available_tools(modeling_url, "Data Modeling Server")
    
    print(f"\n📊 Summary:")
    print(f"  Cypher Server (8003): {'✅ Working' if cypher_ok else '❌ Issues'}")
    print(f"  Data Modeling Server (8004): {'✅ Working' if modeling_ok else '❌ Issues'}")
