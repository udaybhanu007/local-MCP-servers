#!/usr/bin/env python3
"""
Use both MCP servers to create data model and ingest the ChestX-ray dataset documentation
"""

import requests
import json
import time
from typing import Dict, Any, List

# MCP Server configurations
CYPHER_SERVER_URL = "http://127.0.0.1:8003/mcp/"
DATA_MODELING_SERVER_URL = "http://127.0.0.1:8004/mcp/"

def make_mcp_request(url: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make an MCP request to a server"""
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=request_data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def create_data_model():
    """Use the data modeling server to create the schema"""
    print("🏗️  Creating data model using Data Modeling Server...")
    
    # Define the schema for our ChestX-ray documentation
    schema_description = """
    Create a Neo4j data model for a medical research dataset documentation with:
    
    1. Document node with properties: title, author, creation_date, type, page_count
    2. Page nodes with properties: number, text, word_count  
    3. Disease nodes with properties: name, category, frequency
    4. Author nodes with properties: name, affiliation, email
    5. Citation nodes with properties: title, year, venue, authors
    6. Dataset nodes with properties: name, size, format, description
    
    Relationships:
    - Document HAS_PAGE Page
    - Document HAS_AUTHOR Author  
    - Document CITES Citation
    - Document DESCRIBES Dataset
    - Dataset CONTAINS Disease
    - Page MENTIONS Disease
    """
    
    # Try to use the data modeling server to create schema
    result = make_mcp_request(
        DATA_MODELING_SERVER_URL,
        "tools/call",
        {
            "name": "create_schema",
            "arguments": {
                "description": schema_description,
                "domain": "medical_research"
            }
        }
    )
    
    print(f"Data modeling result: {result}")
    return result

def create_schema_with_cypher():
    """Create the schema using direct Cypher queries"""
    print("🔧 Creating schema with Cypher queries...")
    
    # Create constraints and indexes
    constraints_queries = [
        "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE", 
        "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
        "CREATE CONSTRAINT citation_id IF NOT EXISTS FOR (c:Citation) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT dataset_name IF NOT EXISTS FOR (ds:Dataset) REQUIRE ds.name IS UNIQUE"
    ]
    
    for query in constraints_queries:
        result = make_mcp_request(
            CYPHER_SERVER_URL,
            "tools/call",
            {
                "name": "run_cypher",
                "arguments": {"query": query}
            }
        )
        print(f"Constraint result: {result.get('result', result)}")
        time.sleep(0.5)  # Small delay between queries
    
    return True

def ingest_document_data():
    """Ingest the extracted PDF content into Neo4j"""
    print("📥 Ingesting document data...")
    
    # Load extracted content
    try:
        with open("extracted_content.json", "r", encoding="utf-8") as f:
            content = json.load(f)
    except FileNotFoundError:
        print("❌ extracted_content.json not found. Please run extract_pdf_content.py first.")
        return False
    
    # Create main document node
    doc_query = """
    CREATE (d:Document {
        id: 'chestxray_readme',
        title: $title,
        author: $author,
        creation_date: $creation_date,
        type: 'medical_research_documentation',
        page_count: $page_count,
        subject: $subject
    })
    RETURN d
    """
    
    doc_result = make_mcp_request(
        CYPHER_SERVER_URL,
        "tools/call",
        {
            "name": "run_cypher",
            "arguments": {
                "query": doc_query,
                "parameters": {
                    "title": content["document_info"]["title"],
                    "author": content["document_info"]["author"],
                    "creation_date": content["document_info"]["creation_date"],
                    "page_count": content["metadata"]["total_pages"],
                    "subject": content["document_info"]["subject"]
                }
            }
        }
    )
    print(f"Document creation result: {doc_result}")
    
    # Create page nodes
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
        RETURN p
        """
        
        page_result = make_mcp_request(
            CYPHER_SERVER_URL,
            "tools/call",
            {
                "name": "run_cypher",
                "arguments": {
                    "query": page_query,
                    "parameters": {
                        "page_number": str(page["page_number"]),
                        "text": page["text"][:1000],  # Limit text length
                        "word_count": page["word_count"]
                    }
                }
            }
        )
        print(f"Page {page['page_number']} creation result: {page_result.get('result', {}).get('summary', 'Created')}")
    
    # Create disease nodes for the 14 chest diseases mentioned
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
        RETURN dis
        """
        
        disease_result = make_mcp_request(
            CYPHER_SERVER_URL,
            "tools/call",
            {
                "name": "run_cypher",
                "arguments": {
                    "query": disease_query,
                    "parameters": {
                        "name": disease,
                        "index": i
                    }
                }
            }
        )
        print(f"Disease '{disease}' creation result: {disease_result.get('result', {}).get('summary', 'Created')}")
    
    # Create dataset node
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
    RETURN ds
    """
    
    dataset_result = make_mcp_request(
        CYPHER_SERVER_URL,
        "tools/call",
        {
            "name": "run_cypher",
            "arguments": {"query": dataset_query}
        }
    )
    print(f"Dataset creation result: {dataset_result}")
    
    # Link diseases to dataset
    link_diseases_query = """
    MATCH (ds:Dataset {name: 'NIH ChestX-ray Dataset'})
    MATCH (dis:Disease)
    CREATE (ds)-[:CONTAINS]->(dis)
    RETURN count(*) as linked_diseases
    """
    
    link_result = make_mcp_request(
        CYPHER_SERVER_URL,
        "tools/call",
        {
            "name": "run_cypher",
            "arguments": {"query": link_diseases_query}
        }
    )
    print(f"Disease linking result: {link_result}")
    
    return True

def verify_ingestion():
    """Verify that the data was successfully ingested"""
    print("🔍 Verifying data ingestion...")
    
    # Count nodes
    count_query = """
    RETURN 
        size((:Document)) as documents,
        size((:Page)) as pages,
        size((:Disease)) as diseases,
        size((:Dataset)) as datasets
    """
    
    count_result = make_mcp_request(
        CYPHER_SERVER_URL,
        "tools/call",
        {
            "name": "run_cypher",
            "arguments": {"query": count_query}
        }
    )
    
    print(f"Node counts: {count_result}")
    
    # Get relationships
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as relationship_type, count(r) as count
    ORDER BY count DESC
    """
    
    rel_result = make_mcp_request(
        CYPHER_SERVER_URL,
        "tools/call",
        {
            "name": "run_cypher",
            "arguments": {"query": rel_query}
        }
    )
    
    print(f"Relationship counts: {rel_result}")
    
    # Sample data query
    sample_query = """
    MATCH (d:Document)-[:HAS_PAGE]->(p:Page)
    RETURN d.title, p.number, p.word_count
    LIMIT 3
    """
    
    sample_result = make_mcp_request(
        CYPHER_SERVER_URL,
        "tools/call",
        {
            "name": "run_cypher",
            "arguments": {"query": sample_query}
        }
    )
    
    print(f"Sample data: {sample_result}")
    
    return count_result, rel_result, sample_result

if __name__ == "__main__":
    print("🚀 Starting ChestX-ray documentation ingestion...")
    print("=" * 60)
    
    # Step 1: Create data model
    # create_data_model()  # Try data modeling server first
    
    # Step 2: Create schema with Cypher (fallback)
    create_schema_with_cypher()
    
    # Step 3: Ingest data
    success = ingest_document_data()
    
    if success:
        # Step 4: Verify ingestion
        verify_ingestion()
        print("\n✅ Ingestion completed successfully!")
    else:
        print("\n❌ Ingestion failed!")
