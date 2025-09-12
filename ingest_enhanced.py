#!/usr/bin/env python3
"""
Enhanced MCP client using both neo4j-cypher and neo4j-data-modeling servers
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
            "name": "chest-xray-enhanced-client",
            "version": "2.0.0"
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
            "name": "chest-xray-enhanced-client",
            "version": "2.0.0"
        }
    })
    
    if "error" in modeling_init:
        print(f"❌ Data modeling server initialization failed: {modeling_init['error']}")
        return False, None, None
    
    print("✅ Both servers initialized successfully!")
    return True, cypher_url, modeling_url

def design_schema_with_modeling_server(modeling_url):
    """Use data modeling server to design the schema"""
    print("\n🎨 Designing schema with data modeling server...")
    
    # Define our data model structure
    data_model = {
        "nodes": [
            {
                "label": "Document",
                "properties": {
                    "id": {"type": "string", "unique": True, "required": True},
                    "title": {"type": "string", "required": True},
                    "author": {"type": "string"},
                    "creation_date": {"type": "string"},
                    "type": {"type": "string"},
                    "page_count": {"type": "integer"}
                }
            },
            {
                "label": "Page",
                "properties": {
                    "id": {"type": "string", "unique": True, "required": True},
                    "number": {"type": "string", "required": True},
                    "text": {"type": "string"},
                    "word_count": {"type": "integer"}
                }
            },
            {
                "label": "Disease",
                "properties": {
                    "name": {"type": "string", "unique": True, "required": True},
                    "category": {"type": "string"},
                    "index": {"type": "integer"}
                }
            },
            {
                "label": "Dataset",
                "properties": {
                    "name": {"type": "string", "unique": True, "required": True},
                    "size": {"type": "integer"},
                    "format": {"type": "string"},
                    "resolution": {"type": "string"},
                    "patients": {"type": "integer"},
                    "description": {"type": "string"}
                }
            }
        ],
        "relationships": [
            {
                "type": "HAS_PAGE",
                "from": "Document",
                "to": "Page"
            },
            {
                "type": "DESCRIBES",
                "from": "Document",
                "to": "Dataset"
            },
            {
                "type": "CONTAINS",
                "from": "Dataset",
                "to": "Disease"
            }
        ]
    }
    
    # Validate the data model
    print("📋 Validating data model...")
    validation_result = make_mcp_request(modeling_url, "tools/call", {
        "name": "validate_data_model",
        "arguments": {
            "data_model": data_model
        }
    })
    
    if "error" not in validation_result:
        print("✅ Data model validation successful!")
        print(f"Validation result: {validation_result}")
    else:
        print(f"⚠️ Data model validation warning: {validation_result}")
    
    return data_model

def generate_constraints_with_modeling_server(modeling_url, data_model):
    """Generate constraints using the data modeling server"""
    print("\n🔧 Generating constraints with data modeling server...")
    
    constraints_result = make_mcp_request(modeling_url, "tools/call", {
        "name": "get_constraints_cypher_queries",
        "arguments": {
            "data_model": data_model
        }
    })
    
    if "error" not in constraints_result:
        print("✅ Constraints generated successfully!")
        return constraints_result.get("result", {}).get("constraints", [])
    else:
        print(f"❌ Constraint generation failed: {constraints_result}")
        return []

def execute_constraints_with_cypher_server(cypher_url, constraints):
    """Execute constraints using the cypher server"""
    print("\n🔨 Executing constraints with cypher server...")
    
    for constraint in constraints:
        result = make_mcp_request(cypher_url, "tools/call", {
            "name": "write_neo4j_cypher",
            "arguments": {
                "query": constraint
            }
        })
        
        if "error" not in result:
            print(f"✅ Constraint executed successfully")
        else:
            print(f"⚠️ Constraint execution result: {result}")
        time.sleep(0.5)

def generate_ingestion_queries_with_modeling_server(modeling_url, data_model):
    """Generate optimized ingestion queries using data modeling server"""
    print("\n📝 Generating ingestion queries with data modeling server...")
    
    ingestion_queries = {}
    
    # Generate node ingestion queries for each entity
    for node in data_model["nodes"]:
        print(f"Generating ingestion query for {node['label']} nodes...")
        
        query_result = make_mcp_request(modeling_url, "tools/call", {
            "name": "get_node_cypher_ingest_query",
            "arguments": {
                "node_label": node["label"],
                "properties": list(node["properties"].keys())
            }
        })
        
        if "error" not in query_result:
            ingestion_queries[node["label"]] = query_result.get("result", {}).get("query", "")
            print(f"✅ {node['label']} ingestion query generated")
        else:
            print(f"❌ Failed to generate {node['label']} query: {query_result}")
    
    # Generate relationship ingestion queries
    for rel in data_model["relationships"]:
        print(f"Generating ingestion query for {rel['type']} relationships...")
        
        rel_query_result = make_mcp_request(modeling_url, "tools/call", {
            "name": "get_relationship_cypher_ingest_query",
            "arguments": {
                "relationship_type": rel["type"],
                "from_label": rel["from"],
                "to_label": rel["to"]
            }
        })
        
        if "error" not in rel_query_result:
            ingestion_queries[rel["type"]] = rel_query_result.get("result", {}).get("query", "")
            print(f"✅ {rel['type']} relationship query generated")
        else:
            print(f"❌ Failed to generate {rel['type']} relationship query: {rel_query_result}")
    
    return ingestion_queries

def ingest_data_with_enhanced_workflow():
    """Enhanced data ingestion workflow using both MCP servers"""
    print("🚀 Starting enhanced data ingestion with dual MCP servers...")
    print("=" * 70)
    
    # Step 1: Initialize both servers
    success, cypher_url, modeling_url = initialize_servers()
    if not success:
        return False
    
    # Step 2: Design schema with data modeling server
    data_model = design_schema_with_modeling_server(modeling_url)
    
    # Step 3: Generate constraints with modeling server
    constraints = generate_constraints_with_modeling_server(modeling_url, data_model)
    
    # Step 4: Execute constraints with cypher server
    if constraints:
        execute_constraints_with_cypher_server(cypher_url, constraints)
    
    # Step 5: Generate optimized ingestion queries with modeling server
    ingestion_queries = generate_ingestion_queries_with_modeling_server(modeling_url, data_model)
    
    # Step 6: Load content data
    try:
        with open("extracted_content.json", "r", encoding="utf-8") as f:
            content = json.load(f)
    except FileNotFoundError:
        print("❌ extracted_content.json not found")
        return False
    
    # Step 7: Perform data ingestion using cypher server with generated queries
    print("\n📊 Performing data ingestion...")
    
    # Create document using generated query or fallback
    doc_query = ingestion_queries.get("Document", """
        CREATE (d:Document {
            id: $id,
            title: $title,
            author: $author,
            creation_date: $creation_date,
            type: $type,
            page_count: $page_count
        })
        RETURN d.title as title, d.page_count as pages
    """)
    
    print("📄 Creating document node...")
    doc_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": doc_query,
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
        print(f"✅ Document created: {doc_result}")
    else:
        print(f"❌ Document creation failed: {doc_result}")
        return False
    
    # Create pages using generated query or fallback
    page_query = ingestion_queries.get("Page", """
        MATCH (d:Document {id: $doc_id})
        CREATE (p:Page {
            id: $id,
            number: $number,
            text: $text,
            word_count: $word_count
        })
        CREATE (d)-[:HAS_PAGE]->(p)
        RETURN p.number as page_number, p.word_count as words
    """)
    
    print("\n📝 Creating page nodes...")
    for page in content["pages"]:
        page_result = make_mcp_request(cypher_url, "tools/call", {
            "name": "write_neo4j_cypher",
            "arguments": {
                "query": page_query,
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
    disease_query = ingestion_queries.get("Disease", """
        CREATE (dis:Disease {
            name: $name,
            category: $category,
            index: $index
        })
        RETURN dis.name as name, dis.index as index
    """)
    
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
                "query": disease_query,
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
    dataset_query = ingestion_queries.get("Dataset", """
        CREATE (ds:Dataset {
            name: $name,
            size: $size,
            format: $format,
            resolution: $resolution,
            patients: $patients,
            description: $description
        })
        RETURN ds.name as name, ds.size as size
    """)
    
    print("\n📊 Creating dataset node...")
    dataset_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": dataset_query,
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
        print(f"✅ Dataset created: {dataset_result}")
    else:
        print(f"❌ Dataset creation failed: {dataset_result}")
    
    # Create relationships
    print("\n🔗 Creating relationships...")
    
    # Document DESCRIBES Dataset
    describes_query = ingestion_queries.get("DESCRIBES", """
        MATCH (d:Document {id: $doc_id})
        MATCH (ds:Dataset {name: $dataset_name})
        CREATE (d)-[:DESCRIBES]->(ds)
        RETURN count(*) as relationships_created
    """)
    
    describes_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": describes_query,
            "params": {
                "doc_id": "chestxray_readme",
                "dataset_name": "NIH ChestX-ray Dataset"
            }
        }
    })
    
    if "error" not in describes_result:
        print(f"✅ DESCRIBES relationship created: {describes_result}")
    else:
        print(f"❌ DESCRIBES relationship failed: {describes_result}")
    
    # Dataset CONTAINS Disease
    contains_query = ingestion_queries.get("CONTAINS", """
        MATCH (ds:Dataset {name: $dataset_name})
        MATCH (dis:Disease)
        CREATE (ds)-[:CONTAINS]->(dis)
        RETURN count(*) as relationships_created
    """)
    
    contains_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "write_neo4j_cypher",
        "arguments": {
            "query": contains_query,
            "params": {
                "dataset_name": "NIH ChestX-ray Dataset"
            }
        }
    })
    
    if "error" not in contains_result:
        print(f"✅ CONTAINS relationships created: {contains_result}")
    else:
        print(f"❌ CONTAINS relationships failed: {contains_result}")
    
    return True

def verify_enhanced_ingestion(cypher_url):
    """Verify the enhanced ingestion using cypher server"""
    print("\n🔍 Verifying enhanced data ingestion...")
    
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
        "arguments": {"query": count_query}
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
        "arguments": {"query": rel_query}
    })
    
    print(f"🔗 Relationships: {rel_result}")
    
    # Sample data
    sample_query = """
    MATCH (d:Document)-[:DESCRIBES]->(ds:Dataset)-[:CONTAINS]->(dis:Disease)
    RETURN d.title, ds.name, count(dis) as disease_count
    """
    
    sample_result = make_mcp_request(cypher_url, "tools/call", {
        "name": "read_neo4j_cypher",
        "arguments": {"query": sample_query}
    })
    
    print(f"📋 Sample data: {sample_result}")
    
    return count_result, rel_result, sample_result

if __name__ == "__main__":
    print("🚀 ChestX-ray Enhanced Ingestion with Dual MCP Servers")
    print("=" * 70)
    
    success = ingest_data_with_enhanced_workflow()
    
    if success:
        # Get cypher URL for verification
        _, cypher_url, _ = initialize_servers()
        if cypher_url:
            verify_enhanced_ingestion(cypher_url)
        print("\n🎉 Enhanced ingestion completed successfully!")
    else:
        print("\n❌ Enhanced ingestion failed!")
