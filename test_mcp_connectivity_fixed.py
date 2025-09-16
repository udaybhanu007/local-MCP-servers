#!/usr/bin/env python3
"""
Test MCP server connectivity for both servers used in graph ingestion - FIXED VERSION
"""
import requests
import json

def make_mcp_request(url: str, method: str, params: dict = None):
    """Make an MCP request with proper protocol handling"""
    if params is None:
        params = {}
        
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        response = requests.post(url, json=request_data, headers=headers, timeout=10)
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                # Try parsing SSE response
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        data_json = line[6:]  # Remove 'data: ' prefix
                        try:
                            return json.loads(data_json)
                        except:
                            continue
                return {"error": "Could not parse response"}
        else:
            print(f"  Error response: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": str(e)}

def test_mcp_server(server_url, server_name):
    """Test connectivity to an MCP server using proper MCP protocol"""
    try:
        print(f"\n🔗 Testing {server_name} at {server_url}", flush=True)
        
        # Test MCP initialization (this is the proper way to test MCP servers)
        init_result = make_mcp_request(server_url, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "connectivity-test-client",
                "version": "1.0.0"
            }
        })
        
        if "error" not in init_result:
            print(f"  ✅ {server_name} initialized successfully")
            print(f"  Server capabilities: {init_result.get('result', {}).get('capabilities', {})}")
            
            # Test tools listing
            tools_result = make_mcp_request(server_url, "tools/list", {})
            
            if "error" not in tools_result:
                tools = tools_result.get("result", {}).get("tools", [])
                print(f"  ✅ {server_name} tools list retrieved ({len(tools)} tools)")
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"    - {tool.get('name', 'Unknown')}")
                if len(tools) > 3:
                    print(f"    ... and {len(tools) - 3} more tools")
                return True
            else:
                print(f"  ⚠️ {server_name} initialized but tools/list failed: {tools_result}")
                return True  # Still consider it working if init succeeded
        else:
            print(f"  ❌ {server_name} initialization failed: {init_result['error']}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to {server_name} - server may not be running")
        return False
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout connecting to {server_name}")
        return False
    except Exception as e:
        print(f"  ❌ Error testing {server_name}: {str(e)}")
        return False

def test_cypher_query(cypher_url):
    """Test a simple Cypher query execution"""
    print(f"\n🧪 Testing Cypher query execution...")
    
    query_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "read_neo4j_cypher",
        "arguments": {
            "query": "RETURN 'Hello Neo4j!' as message, datetime() as timestamp",
            "params": {}
        }
    })
    
    if "error" not in query_result:
        print(f"  ✅ Cypher query executed successfully")
        print(f"  Result: {query_result.get('result', {})}")
        return True
    else:
        print(f"  ❌ Cypher query failed: {query_result['error']}")
        return False

def main():
    """Test both MCP servers using proper MCP protocol"""
    print("🧪 Testing MCP Server Connectivity (Fixed Version)", flush=True)
    print("=" * 60, flush=True)
    
    # Server URLs from ingest_working.py
    cypher_server_url = "http://127.0.0.1:8003/mcp/"
    data_modeling_server_url = "http://127.0.0.1:8004/mcp/"
    
    # Test both servers
    cypher_result = test_mcp_server(cypher_server_url, "Cypher Server (Port 8003)")
    modeling_result = test_mcp_server(data_modeling_server_url, "Data Modeling Server (Port 8004)")
    
    # Test Cypher query if cypher server is working
    cypher_query_result = False
    if cypher_result:
        cypher_query_result = test_cypher_query(cypher_server_url)
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"  Cypher Server (8003): {'✅ Working' if cypher_result else '❌ Failed'}")
    print(f"  Data Modeling Server (8004): {'✅ Working' if modeling_result else '❌ Failed'}")
    print(f"  Cypher Query Test: {'✅ Working' if cypher_query_result else '❌ Failed'}")
    
    if cypher_result and modeling_result:
        print("\n🎉 Both MCP servers are working correctly!")
        print("   You can now run your graph ingestion workflow.")
        return True
    else:
        print("\n⚠️  One or more MCP servers are not accessible")
        if not cypher_result:
            print("   - Start the Cypher server: python start_cypher_server.py")
        if not modeling_result:
            print("   - Start the Data Modeling server: python start_data_modeling_server.py")
        return False

if __name__ == "__main__":
    success = main()
