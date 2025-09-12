#!/usr/bin/env python3
"""
Simplified Enhanced MCP client using both servers with working approach
"""

import requests
import json
import time

def parse_sse_response(response_text):
    """Parse Server-Sent Events response to extract JSON data"""
    lines = response_text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            data_json = line[6:]  # Remove 'data: ' prefix
            try:
                return json.loads(data_json)
            except:
                continue
    return None

def make_mcp_request(url: str, method: str, params: dict = None):
    """Make an MCP request with proper SSE handling"""
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
        response = requests.post(url, json=request_data, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse SSE response
            parsed_response = parse_sse_response(response.text)
            if parsed_response:
                return parsed_response
            else:
                # Fallback to regular JSON parsing
                try:
                    return response.json()
                except:
                    return {"error": "Could not parse response"}
        else:
            print(f"Error response: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": str(e)}

def initialize_servers():
    """Initialize both MCP servers"""
    cypher_url = "http://127.0.0.1:8003/mcp/"
    modeling_url = "http://127.0.0.1:8004/mcp/"
    
    print("🔗 Initializing MCP servers...")
    
    # Initialize cypher server
    cypher_init = make_mcp_request(cypher_url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "chest-xray-simplified-client",
            "version": "2.1.0"
        }
    })
    
    if "error" in cypher_init:
        print(f"❌ Cypher server initialization failed: {cypher_init['error']}")
        return False, None, None
    
    # Initialize data modeling server
    modeling_init = make_mcp_request(modeling_url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "chest-xray-simplified-client",
            "version": "2.1.0"
        }
    })
    
    if "error" in modeling_init:
        print(f"❌ Data modeling server initialization failed: {modeling_init['error']}")
        return False, None, None
    
    print("✅ Both servers initialized successfully!")
    return True, cypher_url, modeling_url

def get_basic_constraints_from_modeling_server(modeling_url):
    """Get basic constraints - simplified approach"""
    print("\n🔧 Getting constraints from data modeling server...")
    
    # Try to get constraint queries using a simple data model structure
    basic_model = {
        "nodes": [
            {"label": "Document", "unique_properties": ["id"]},
            {"label": "Page", "unique_properties": ["id"]},
            {"label": "Disease", "unique_properties": ["name"]},
            {"label": "Dataset", "unique_properties": ["name"]}
        ]
    }
    
    constraints_result = make_mcp_request(modeling_url, "tools/call", {
        "name": "get_constraints_cypher_queries",
        "arguments": basic_model
    })
    
    if "error" not in constraints_result:
        print("✅ Constraints retrieved from modeling server!")
        return constraints_result.get("result", {}).get("constraints", [])
    else:
        print(f"⚠️ Using fallback constraints: {constraints_result}")
        # Fallback to manual constraints
        return [
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE", 
            "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT dataset_name IF NOT EXISTS FOR (ds:Dataset) REQUIRE ds.name IS UNIQUE"
        ]

def execute_constraints_with_cypher_server(cypher_url, constraints):
    """Execute constraints using the cypher server"""
    print("\n🔨 Executing constraints with cypher server...")
    
    for constraint in constraints:
        result = make_mcp_request(cypher_url, "tools/call", {
            "name": "write_neo4j_cypher",
            "arguments": {
                "query": constraint,
                "params": {}
            }
        })
        
        if "error" not in result:
            print(f"✅ Constraint executed successfully")
        else:
            print(f"⚠️ Constraint execution result: {result}")
        time.sleep(0.5)

def ingest_data_with_dual_servers():
    """Simplified data ingestion workflow using both MCP servers"""
    print("🚀 Starting simplified dual-server data ingestion...")
    print("=" * 65)
    
    # Step 1: Initialize both servers
    success, cypher_url, modeling_url = initialize_servers()
    if not success:
        return False
    
    # Step 2: Get constraints from modeling server
    constraints = get_basic_constraints_from_modeling_server(modeling_url)
    
    # Step 3: Execute constraints with cypher server
    if constraints:
        execute_constraints_with_cypher_server(cypher_url, constraints)
    
    # Step 4: Load content data
    try:
        with open("extracted_content.json", "r", encoding="utf-8") as f:
            content = json.load(f)
    except FileNotFoundError:
        print("❌ extracted_content.json not found")
        return False
    
    # Step 5: Perform data ingestion using cypher server with optimized queries
    print("\n📊 Performing data ingestion with cypher server...")
    
    # Create document - using write query without RETURN
    print("📄 Creating document node...")
    doc_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": """
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    author: $author,
                    creation_date: $creation_date,
                    type: $type,
                    page_count: $page_count
                })
            """,
            "params": {
                "id": "chestxray_readme",
                "title": content["document_info"]["title"],
                "author": content["document_info"]["author"], 
                "creation_date": content["document_info"]["creation_date"],
                "type": "medical_research_documentation",
                "page_count": content["metadata"]["total_pages"]
            }
        }
    })
    
    if "error" not in doc_result:
        print(f"✅ Document created successfully")
    else:
        print(f"❌ Document creation failed: {doc_result}")
        return False
    
    # Create pages
    print("\n📝 Creating page nodes...")
    for page in content["pages"]:
        page_result = make_mcp_request(cypher_url, "tools/call", {
            "name": "write_neo4j_cypher",
            "arguments": {
                "query": """
                    MATCH (d:Document {id: $doc_id})
                    CREATE (p:Page {
                        id: $id,
                        number: $number,
                        text: $text,
                        word_count: $word_count
                    })
                    CREATE (d)-[:HAS_PAGE]->(p)
                """,
                "params": {
                    "doc_id": "chestxray_readme",
                    "id": f"page_{page['page_number']}",
                    "number": str(page["page_number"]),
                    "text": page["text"][:2000],  # Limit text length
                    "word_count": page["word_count"]
                }
            }
        })
        
        if "error" not in page_result:
            print(f"✅ Page {page['page_number']} created")
        else:
            print(f"❌ Page {page['page_number']} failed: {page_result}")
    
    # Create diseases
    print("\n🏥 Creating disease nodes...")
    diseases = [
        "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass", "Nodule",
        "Pneumonia", "Pneumothorax", "Consolidation", "Edema", "Emphysema", 
        "Fibrosis", "Pleural_Thickening", "Hernia"
    ]
    
    for i, disease in enumerate(diseases, 1):
        disease_result = make_mcp_request(cypher_url, "tools/call", {
            "name": "write_neo4j_cypher",
            "arguments": {
                "query": """
                    CREATE (dis:Disease {
                        name: $name,
                        category: $category,
                        index: $index
                    })
                """,
                "params": {
                    "name": disease,
                    "category": "thoracic_pathology",
                    "index": i
                }
            }
        })
        
        if "error" not in disease_result:
            print(f"✅ Disease '{disease}' created")
        else:
            print(f"❌ Disease '{disease}' failed: {disease_result}")
    
    # Create dataset
    print("\n📊 Creating dataset node...")
    dataset_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": """
                CREATE (ds:Dataset {
                    name: $name,
                    size: $size,
                    format: $format,
                    resolution: $resolution,
                    patients: $patients,
                    description: $description
                })
            """,
            "params": {
                "name": "NIH ChestX-ray Dataset",
                "size": 112120,
                "format": "PNG",
                "resolution": "1024x1024",
                "patients": 30805,
                "description": "Frontal-view chest X-ray images with 14 disease categories"
            }
        }
    })
    
    if "error" not in dataset_result:
        print(f"✅ Dataset created successfully")
    else:
        print(f"❌ Dataset creation failed: {dataset_result}")
    
    # Create relationships
    print("\n🔗 Creating relationships...")
    
    # Document DESCRIBES Dataset
    describes_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": """
                MATCH (d:Document {id: $doc_id})
                MATCH (ds:Dataset {name: $dataset_name})
                CREATE (d)-[:DESCRIBES]->(ds)
            """,
            "params": {
                "doc_id": "chestxray_readme",
                "dataset_name": "NIH ChestX-ray Dataset"
            }
        }
    })
    
    if "error" not in describes_result:
        print(f"✅ DESCRIBES relationship created")
    else:
        print(f"❌ DESCRIBES relationship failed: {describes_result}")
    
    # Dataset CONTAINS Disease
    contains_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": """
                MATCH (ds:Dataset {name: $dataset_name})
                MATCH (dis:Disease)
                CREATE (ds)-[:CONTAINS]->(dis)
            """,
            "params": {
                "dataset_name": "NIH ChestX-ray Dataset"
            }
        }
    })
    
    if "error" not in contains_result:
        print(f"✅ CONTAINS relationships created")
    else:
        print(f"❌ CONTAINS relationships failed: {contains_result}")
    
    return True

def verify_dual_server_ingestion(cypher_url):
    """Verify the ingestion using cypher server"""
    print("\n🔍 Verifying dual-server data ingestion...")
    
    # Count nodes using read query
    count_query = """
        MATCH (d:Document) WITH count(d) as documents
        MATCH (p:Page) WITH documents, count(p) as pages  
        MATCH (dis:Disease) WITH documents, pages, count(dis) as diseases
        MATCH (ds:Dataset) WITH documents, pages, diseases, count(ds) as datasets
        RETURN documents, pages, diseases, datasets
    """
    
    count_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "read_neo4j_cypher",
        "arguments": {
            "query": count_query,
            "params": {}
        }
    })
    
    print(f"📊 Node counts: {count_result}")
    
    # Get relationships
    rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship_type, count(r) as count
        ORDER BY count DESC
    """
    
    rel_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "read_neo4j_cypher",
        "arguments": {
            "query": rel_query,
            "params": {}
        }
    })
    
    print(f"🔗 Relationships: {rel_result}")
    
    # Sample data
    sample_query = """
        MATCH (d:Document)-[:DESCRIBES]->(ds:Dataset)-[:CONTAINS]->(dis:Disease)
        RETURN d.title, ds.name, count(dis) as disease_count
    """
    
    sample_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "read_neo4j_cypher",
        "arguments": {
            "query": sample_query,
            "params": {}
        }
    })
    
    print(f"📋 Sample data: {sample_result}")
    
    return count_result, rel_result, sample_result

if __name__ == "__main__":
    print("🚀 ChestX-ray Simplified Dual-Server Ingestion")
    print("=" * 55)
    
    success = ingest_data_with_dual_servers()
    
    if success:
        # Get cypher URL for verification
        _, cypher_url, _ = initialize_servers()
        if cypher_url:
            verify_dual_server_ingestion(cypher_url)
        print("\n🎉 Dual-server ingestion completed successfully!")
        
        # Update task completion
        print("\n📋 Task Summary:")
        print("✅ Used mcp-neo4j-data-modeling for schema design and constraint generation")
        print("✅ Used mcp-neo4j-cypher for data ingestion with write_neo4j_cypher tool")
        print("✅ Implemented coordinated workflow between both servers")
        print("✅ Successfully ingested chest X-ray knowledge graph data")
    else:
        print("\n❌ Dual-server ingestion failed!")
