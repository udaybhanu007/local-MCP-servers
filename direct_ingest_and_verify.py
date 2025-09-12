#!/usr/bin/env python3
"""
Direct Neo4j ingestion to verify data can be stored, then test MCP access
"""

import json
from dotenv import load_dotenv
import os

def ingest_directly_to_neo4j():
    """Ingest data directly to Neo4j using the neo4j driver"""
    print("🔄 Ingesting data directly to Neo4j...")
    
    # Load environment variables
    load_dotenv('.env.dev')
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME') 
        password = os.getenv('NEO4J_PASSWORD')
        database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        print(f"Connecting to: {uri}")
        
        # Load extracted content
        with open("extracted_content.json", "r", encoding="utf-8") as f:
            content = json.load(f)
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session(database=database) as session:
            
            # Clear existing data for clean start
            print("🧹 Clearing existing ChestX-ray data...")
            session.run("""
                MATCH (n) 
                WHERE n.id STARTS WITH 'chestxray' OR n.name = 'NIH ChestX-ray Dataset'
                DETACH DELETE n
            """)
            
            # Create constraints
            print("🔧 Creating constraints...")
            constraints = [
                "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"  ✅ Constraint created")
                except Exception as e:
                    print(f"  ⚠️  Constraint exists or error: {e}")
            
            # Create document
            print("📄 Creating document...")
            doc_result = session.run("""
                CREATE (d:Document {
                    id: 'chestxray_readme',
                    title: $title,
                    author: $author,
                    creation_date: $creation_date,
                    type: 'medical_research_documentation',
                    page_count: $page_count
                })
                RETURN d.title as title, d.page_count as pages
            """, 
                title=content["document_info"]["title"],
                author=content["document_info"]["author"],
                creation_date=content["document_info"]["creation_date"],
                page_count=content["metadata"]["total_pages"]
            )
            
            doc_record = doc_result.single()
            print(f"  ✅ Document created: {doc_record['title']} ({doc_record['pages']} pages)")
            
            # Create pages
            print("📝 Creating pages...")
            for page in content["pages"]:
                page_result = session.run("""
                    MATCH (d:Document {id: 'chestxray_readme'})
                    CREATE (p:Page {
                        id: 'chestxray_page_' + $page_number,
                        number: $page_number,
                        text: $text,
                        word_count: $word_count
                    })
                    CREATE (d)-[:HAS_PAGE]->(p)
                    RETURN p.number as page_number
                """,
                    page_number=str(page["page_number"]),
                    text=page["text"][:2000],  # Limit text length for storage
                    word_count=page["word_count"]
                )
                
                page_record = page_result.single()
                print(f"  ✅ Page {page_record['page_number']} created")
            
            # Create diseases
            print("🏥 Creating diseases...")
            diseases = [
                "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass", "Nodule",
                "Pneumonia", "Pneumothorax", "Consolidation", "Edema", "Emphysema", 
                "Fibrosis", "Pleural_Thickening", "Hernia"
            ]
            
            for i, disease in enumerate(diseases, 1):
                disease_result = session.run("""
                    CREATE (dis:Disease {
                        name: $name,
                        category: 'thoracic_pathology',
                        index: $index
                    })
                    RETURN dis.name as name
                """, name=disease, index=i)
                
                disease_record = disease_result.single()
                print(f"  ✅ Disease '{disease_record['name']}' created")
            
            # Create dataset
            print("📊 Creating dataset...")
            dataset_result = session.run("""
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
            """)
            
            dataset_record = dataset_result.single()
            print(f"  ✅ Dataset created: {dataset_record['name']} ({dataset_record['size']} images)")
            
            # Link diseases to dataset
            print("🔗 Linking diseases to dataset...")
            link_result = session.run("""
                MATCH (ds:Dataset {name: 'NIH ChestX-ray Dataset'})
                MATCH (dis:Disease)
                CREATE (ds)-[:CONTAINS]->(dis)
                RETURN count(*) as linked_diseases
            """)
            
            link_record = link_result.single()
            print(f"  ✅ {link_record['linked_diseases']} diseases linked to dataset")
            
            print("\n✅ Direct ingestion completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error during direct ingestion: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

def verify_via_neo4j():
    """Verify ingestion using direct Neo4j connection"""
    print("\n🔍 Verifying ingestion via Neo4j...")
    
    load_dotenv('.env.dev')
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv('NEO4J_URI')
        username = os.getenv('NEO4J_USERNAME')
        password = os.getenv('NEO4J_PASSWORD')
        database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session(database=database) as session:
            
            # Count nodes
            count_result = session.run("""
                RETURN 
                    size((:Document)) as documents,
                    size((:Page)) as pages,
                    size((:Disease)) as diseases,
                    size((:Dataset)) as datasets
            """)
            
            count_record = count_result.single()
            print(f"📊 Node counts:")
            print(f"  Documents: {count_record['documents']}")
            print(f"  Pages: {count_record['pages']}")
            print(f"  Diseases: {count_record['diseases']}")
            print(f"  Datasets: {count_record['datasets']}")
            
            # Get relationships
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            
            print(f"\n🔗 Relationships:")
            for record in rel_result:
                print(f"  {record['relationship_type']}: {record['count']}")
            
            # Sample query
            sample_result = session.run("""
                MATCH (d:Document)-[:DESCRIBES]->(ds:Dataset)-[:CONTAINS]->(dis:Disease)
                RETURN d.title as document_title, ds.name as dataset_name, count(dis) as disease_count
            """)
            
            sample_record = sample_result.single()
            if sample_record:
                print(f"\n📋 Sample data:")
                print(f"  Document: {sample_record['document_title']}")
                print(f"  Dataset: {sample_record['dataset_name']}")
                print(f"  Diseases: {sample_record['disease_count']}")
            
            # Test a complex query
            complex_result = session.run("""
                MATCH (d:Document)-[:HAS_PAGE]->(p:Page)
                RETURN d.title as document, 
                       count(p) as total_pages,
                       sum(p.word_count) as total_words
            """)
            
            complex_record = complex_result.single()
            if complex_record:
                print(f"\n📖 Document statistics:")
                print(f"  Total pages: {complex_record['total_pages']}")
                print(f"  Total words: {complex_record['total_words']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

def test_mcp_access_to_data():
    """Test if MCP servers can access the ingested data"""
    print("\n🧪 Testing MCP server access to ingested data...")
    
    import requests
    
    cypher_url = "http://127.0.0.1:8003/mcp/"
    
    # Test query to check if data exists
    test_query = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "run_cypher",
            "arguments": {
                "query": "MATCH (d:Document {id: 'chestxray_readme'}) RETURN d.title as title, d.page_count as pages"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        print("  Querying via MCP Cypher server...")
        response = requests.post(cypher_url, json=test_query, headers=headers, timeout=10)
        
        print(f"  Response status: {response.status_code}")
        print(f"  Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Handle potential SSE response
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' in content_type:
                print("  SSE response detected, parsing...")
                lines = response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        try:
                            result = json.loads(data)
                            print(f"  ✅ MCP query successful: {result}")
                            return True
                        except json.JSONDecodeError:
                            continue
            else:
                result = response.json()
                print(f"  ✅ MCP query successful: {result}")
                return True
        else:
            print(f"  ❌ MCP query failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing MCP access: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Direct Neo4j Ingestion and MCP Verification")
    print("=" * 60)
    
    # Step 1: Direct ingestion
    success = ingest_directly_to_neo4j()
    
    if success:
        # Step 2: Verify via Neo4j
        verify_via_neo4j()
        
        # Step 3: Test MCP access
        test_mcp_access_to_data()
        
        print("\n🎉 Complete ingestion and verification finished!")
    else:
        print("\n❌ Ingestion failed!")
