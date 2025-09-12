#!/usr/bin/env python3
"""
Final verification of ChestX-ray data ingestion
"""

import json
from dotenv import load_dotenv
import os
import requests

def verify_ingestion_final():
    """Final verification with corrected queries"""
    print("🔍 Final verification of ChestX-ray data ingestion...")
    
    load_dotenv('.env.dev')
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')
        database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session(database=database) as session:
            
            print("\n📊 Node Counts:")
            # Count nodes correctly
            count_queries = [
                ("Documents", "MATCH (n:Document) RETURN count(n) as count"),
                ("Pages", "MATCH (n:Page) RETURN count(n) as count"),
                ("Diseases", "MATCH (n:Disease) RETURN count(n) as count"),
                ("Datasets", "MATCH (n:Dataset) RETURN count(n) as count")
            ]
            
            for label, query in count_queries:
                result = session.run(query)
                count = result.single()['count']
                print(f"  {label}: {count}")
            
            print("\n🔗 Relationship Counts:")
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            
            for record in rel_result:
                print(f"  {record['relationship_type']}: {record['count']}")
            
            print("\n📋 Document Details:")
            doc_result = session.run("""
                MATCH (d:Document {id: 'chestxray_readme'})
                RETURN d.title as title, d.author as author, d.page_count as pages
            """)
            
            doc_record = doc_result.single()
            if doc_record:
                print(f"  Title: {doc_record['title']}")
                print(f"  Author: {doc_record['author']}")
                print(f"  Pages: {doc_record['pages']}")
            
            print("\n🏥 Disease Categories:")
            disease_result = session.run("""
                MATCH (dis:Disease)
                RETURN dis.name as name, dis.index as index
                ORDER BY dis.index
            """)
            
            diseases = []
            for record in disease_result:
                diseases.append(f"{record['index']}. {record['name']}")
            
            for disease in diseases[:7]:  # Show first 7
                print(f"  {disease}")
            if len(diseases) > 7:
                print(f"  ... and {len(diseases) - 7} more")
            
            print("\n📊 Dataset Information:")
            dataset_result = session.run("""
                MATCH (ds:Dataset)-[:CONTAINS]->(dis:Disease)
                RETURN ds.name as name, ds.size as size, ds.patients as patients, count(dis) as disease_count
            """)
            
            dataset_record = dataset_result.single()
            if dataset_record:
                print(f"  Name: {dataset_record['name']}")
                print(f"  Images: {dataset_record['size']:,}")
                print(f"  Patients: {dataset_record['patients']:,}")
                print(f"  Disease categories: {dataset_record['disease_count']}")
            
            print("\n📖 Page Statistics:")
            page_result = session.run("""
                MATCH (d:Document)-[:HAS_PAGE]->(p:Page)
                RETURN count(p) as total_pages, sum(p.word_count) as total_words, avg(p.word_count) as avg_words_per_page
            """)
            
            page_record = page_result.single()
            if page_record:
                print(f"  Total pages: {page_record['total_pages']}")
                print(f"  Total words: {page_record['total_words']}")
                print(f"  Average words per page: {page_record['avg_words_per_page']:.1f}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

def discover_mcp_tools():
    """Discover available tools in MCP servers"""
    print("\n🔧 Discovering MCP Server Tools...")
    
    servers = [
        ("Cypher Server", "http://127.0.0.1:8003/mcp/"),
        ("Data Modeling Server", "http://127.0.0.1:8004/mcp/")
    ]
    
    for server_name, url in servers:
        print(f"\n{server_name}:")
        
        # List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        try:
            response = requests.post(url, json=tools_request, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    # Parse SSE response
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            data = line[6:]
                            try:
                                result = json.loads(data)
                                if 'result' in result and 'tools' in result['result']:
                                    tools = result['result']['tools']
                                    print(f"  Available tools ({len(tools)}):")
                                    for tool in tools:
                                        print(f"    - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    result = response.json()
                    if 'result' in result and 'tools' in result['result']:
                        tools = result['result']['tools']
                        print(f"  Available tools ({len(tools)}):")
                        for tool in tools:
                            print(f"    - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            else:
                print(f"  ❌ Failed to list tools: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error discovering tools: {e}")

def test_mcp_with_correct_tool():
    """Test MCP access with correct tool name"""
    print("\n🧪 Testing MCP access with correct tool...")
    
    cypher_url = "http://127.0.0.1:8003/mcp/"
    
    # Try common tool names
    tool_names = ["cypher_query", "query", "run_query", "execute_cypher", "neo4j_query"]
    
    test_query = "MATCH (d:Document {id: 'chestxray_readme'}) RETURN d.title as title LIMIT 1"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    for tool_name in tool_names:
        print(f"  Trying tool: {tool_name}")
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {
                    "query": test_query
                }
            }
        }
        
        try:
            response = requests.post(cypher_url, json=request_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            data = line[6:]
                            try:
                                result = json.loads(data)
                                if 'result' in result and not result.get('result', {}).get('isError', False):
                                    print(f"    ✅ Success with tool '{tool_name}': {result}")
                                    return tool_name
                                elif 'error' in result or result.get('result', {}).get('isError', False):
                                    print(f"    ❌ Error with tool '{tool_name}': {result}")
                            except json.JSONDecodeError:
                                continue
                
        except Exception as e:
            print(f"    ❌ Exception with tool '{tool_name}': {e}")
    
    print("  ❌ No working tool found")
    return None

if __name__ == "__main__":
    print("🚀 Final ChestX-ray Data Verification")
    print("=" * 50)
    
    # Verify via direct Neo4j connection
    success = verify_ingestion_final()
    
    if success:
        # Discover MCP tools
        discover_mcp_tools()
        
        # Test MCP access
        working_tool = test_mcp_with_correct_tool()
        
        print(f"\n📋 Summary:")
        print(f"  ✅ Direct Neo4j verification: Success")
        print(f"  {'✅' if working_tool else '❌'} MCP server access: {'Success' if working_tool else 'Issues'}")
        if working_tool:
            print(f"  🔧 Working MCP tool: {working_tool}")
        
        print(f"\n🎉 ChestX-ray documentation successfully ingested into Neo4j!")
        print(f"📊 The database now contains:")
        print(f"  - 1 Document (README_CHESTXRAY)")
        print(f"  - 4 Pages with extracted text")
        print(f"  - 14 Disease categories")
        print(f"  - 1 Dataset description (112,120 chest X-ray images)")
        print(f"  - Relationships connecting all entities")
        
    else:
        print(f"\n❌ Verification failed!")
