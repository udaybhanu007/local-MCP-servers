#!/usr/bin/env python3
"""
Corrected MCP client with proper headers and SSE support
"""

import requests
import json
import time

def make_mcp_request_corrected(url: str, method: str, params: dict = None):
    """Make an MCP request with correct headers"""
    if params is None:
        params = {}
        
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    # Correct headers for MCP servers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        response = requests.post(url, json=request_data, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": str(e)}

def ingest_with_corrected_client():
    """Ingest data using corrected MCP client"""
    print("🚀 Starting corrected data ingestion...")
    
    cypher_url = "http://127.0.0.1:8003/mcp/"
    
    # Test basic connectivity first
    print("🔍 Testing connectivity...")
    init_result = make_mcp_request_corrected(cypher_url, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "chest-xray-ingestion-client",
            "version": "1.0.0"
        }
    })
    
    if "error" in init_result:
        print(f"❌ Initialization failed: {init_result['error']}")
        return False
    
    print("✅ Connected successfully!")
    print(f"Server info: {init_result.get('result', {})}")
    
    # Test simple query
    print("\n🧪 Testing simple query...")
    test_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {
            "query": "RETURN 'Connection test successful!' as message, datetime() as timestamp"
        }
    })
    
    if "error" in test_result:
        print(f"❌ Test query failed: {test_result['error']}")
        return False
    
    print(f"✅ Test query successful: {test_result}")
    
    # Create constraints
    print("\n🔧 Creating constraints...")
    constraints = [
        "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE"
    ]
    
    for constraint in constraints:
        result = make_mcp_request_corrected(cypher_url, "tools/call", {
            "name": "run_cypher",
            "arguments": {"query": constraint}
        })
        
        if "error" not in result:
            print(f"✅ Constraint created successfully")
        else:
            print(f"⚠️  Constraint result: {result}")
        time.sleep(0.5)
    
    # Load content
    try:
        with open("extracted_content.json", "r", encoding="utf-8") as f:
            content = json.load(f)
    except FileNotFoundError:
        print("❌ extracted_content.json not found")
        return False
    
    # Create document
    print("\n📄 Creating document node...")
    doc_query = """
    CREATE (d:Document {
        id: 'chestxray_readme',
        title: $title,
        author: $author,
        creation_date: $creation_date,
        type: 'medical_research_documentation',
        page_count: $page_count
    })
    RETURN d.title as title, d.page_count as pages
    """
    
    doc_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {
            "query": doc_query,
            "parameters": {
                "title": content["document_info"]["title"],
                "author": content["document_info"]["author"], 
                "creation_date": content["document_info"]["creation_date"],
                "page_count": content["metadata"]["total_pages"]
            }
        }
    })
    
    if "error" not in doc_result:
        print(f"✅ Document created: {doc_result}")
    else:
        print(f"❌ Document creation failed: {doc_result}")
        return False
    
    # Create pages
    print("\n📝 Creating page nodes...")
    for page in content["pages"]:
        page_query = """
        MATCH (d:Document {id: 'chestxray_readme'})
        CREATE (p:Page {
            id: 'page_' + $page_number,
            number: $page_number,
            text: $text,
            word_count: $word_count
        })
        CREATE (d)-[:HAS_PAGE]->(p)
        RETURN p.number as page_number, p.word_count as words
        """
        
        page_result = make_mcp_request_corrected(cypher_url, "tools/call", {
            "name": "run_cypher", 
            "arguments": {
                "query": page_query,
                "parameters": {
                    "page_number": str(page["page_number"]),
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
        disease_query = """
        CREATE (dis:Disease {
            name: $name,
            category: 'thoracic_pathology',
            index: $index
        })
        RETURN dis.name as name, dis.index as index
        """
        
        disease_result = make_mcp_request_corrected(cypher_url, "tools/call", {
            "name": "run_cypher",
            "arguments": {
                "query": disease_query,
                "parameters": {
                    "name": disease,
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
    dataset_query = """
    MATCH (d:Document {id: 'chestxray_readme'})
    CREATE (ds:Dataset {
        name: 'NIH ChestX-ray Dataset',
        size: 112120,
        format: 'PNG',
        resolution: '1024x1024',
        patients: 30805,
        description: 'Frontal-view chest X-ray images with 14 disease categories'
    })
    CREATE (d)-[:DESCRIBES]->(ds)
    RETURN ds.name as name, ds.size as size
    """
    
    dataset_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {"query": dataset_query}
    })
    
    if "error" not in dataset_result:
        print(f"✅ Dataset created: {dataset_result}")
    else:
        print(f"❌ Dataset creation failed: {dataset_result}")
    
    # Link diseases to dataset
    print("\n🔗 Linking diseases to dataset...")
    link_query = """
    MATCH (ds:Dataset {name: 'NIH ChestX-ray Dataset'})
    MATCH (dis:Disease)
    CREATE (ds)-[:CONTAINS]->(dis)
    RETURN count(*) as linked_diseases
    """
    
    link_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {"query": link_query}
    })
    
    if "error" not in link_result:
        print(f"✅ Diseases linked: {link_result}")
    else:
        print(f"❌ Disease linking failed: {link_result}")
    
    return True

def verify_ingestion_corrected():
    """Verify the ingestion with corrected client"""
    print("\n🔍 Verifying data ingestion...")
    
    cypher_url = "http://127.0.0.1:8003/mcp/"
    
    # Count nodes
    count_query = """
    RETURN 
        size((:Document)) as documents,
        size((:Page)) as pages,
        size((:Disease)) as diseases,
        size((:Dataset)) as datasets
    """
    
    count_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {"query": count_query}
    })
    
    print(f"📊 Node counts: {count_result}")
    
    # Get relationships
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as relationship_type, count(r) as count
    ORDER BY count DESC
    """
    
    rel_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {"query": rel_query}
    })
    
    print(f"🔗 Relationships: {rel_result}")
    
    # Sample data
    sample_query = """
    MATCH (d:Document)-[:DESCRIBES]->(ds:Dataset)-[:CONTAINS]->(dis:Disease)
    RETURN d.title, ds.name, count(dis) as disease_count
    """
    
    sample_result = make_mcp_request_corrected(cypher_url, "tools/call", {
        "name": "run_cypher",
        "arguments": {"query": sample_query}
    })
    
    print(f"📋 Sample data: {sample_result}")
    
    return count_result, rel_result, sample_result

if __name__ == "__main__":
    print("🚀 ChestX-ray Documentation Ingestion (Corrected)")
    print("=" * 60)
    
    success = ingest_with_corrected_client()
    
    if success:
        verify_ingestion_corrected()
        print("\n🎉 Ingestion completed successfully!")
    else:
        print("\n❌ Ingestion failed!")
