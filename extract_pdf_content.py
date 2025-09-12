#!/usr/bin/env python3
"""
Extract content from README_CHESTXRAY.pdf and prepare for Neo4j ingestion
"""

import pdfplumber
import json
import re
from typing import Dict, List, Any

def extract_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """Extract structured content from the PDF"""
    
    content = {
        "document_info": {},
        "pages": [],
        "sections": [],
        "metadata": {
            "total_pages": 0,
            "extraction_status": "success"
        }
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            content["metadata"]["total_pages"] = len(pdf.pages)
            
            # Extract text from each page
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    page_content = {
                        "page_number": page_num,
                        "text": page_text.strip(),
                        "word_count": len(page_text.split())
                    }
                    content["pages"].append(page_content)
                    
                    # Try to identify sections based on formatting
                    lines = page_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and (
                            line.isupper() or 
                            re.match(r'^[A-Z][^.]*[A-Z]$', line) or
                            re.match(r'^\d+\.?\s+[A-Z]', line)
                        ):
                            content["sections"].append({
                                "title": line,
                                "page": page_num,
                                "type": "section_header"
                            })
            
            # Extract document metadata if available
            if pdf.metadata:
                content["document_info"] = {
                    "title": pdf.metadata.get('Title', 'README_CHESTXRAY'),
                    "author": pdf.metadata.get('Author', ''),
                    "subject": pdf.metadata.get('Subject', ''),
                    "creator": pdf.metadata.get('Creator', ''),
                    "creation_date": str(pdf.metadata.get('CreationDate', ''))
                }
                
    except Exception as e:
        content["metadata"]["extraction_status"] = f"error: {str(e)}"
        print(f"Error extracting PDF: {e}")
    
    return content

def analyze_content_structure(content: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the content to determine the best data model"""
    
    analysis = {
        "document_type": "research_paper",
        "key_entities": [],
        "relationships": [],
        "suggested_schema": {}
    }
    
    # Analyze text for key entities and concepts
    all_text = " ".join([page["text"] for page in content["pages"]])
    
    # Look for research paper elements
    research_keywords = {
        "dataset": ["dataset", "data", "NIH", "ChestX-ray", "chest x-ray", "medical imaging"],
        "methods": ["method", "algorithm", "deep learning", "CNN", "neural network", "model"],
        "results": ["accuracy", "performance", "result", "evaluation", "precision", "recall"],
        "authors": ["author", "researcher", "NIH", "Clinical Center"],
        "references": ["reference", "citation", "arxiv", "doi", "paper"]
    }
    
    for category, keywords in research_keywords.items():
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in all_text.lower():
                found_keywords.append(keyword)
        if found_keywords:
            analysis["key_entities"].append({
                "category": category,
                "keywords": found_keywords
            })
    
    # Suggest Neo4j schema
    analysis["suggested_schema"] = {
        "nodes": [
            {
                "label": "Document",
                "properties": ["title", "type", "page_count", "creation_date"]
            },
            {
                "label": "Page", 
                "properties": ["number", "text", "word_count"]
            },
            {
                "label": "Section",
                "properties": ["title", "type", "content"]
            },
            {
                "label": "Keyword",
                "properties": ["term", "category", "frequency"]
            }
        ],
        "relationships": [
            {"type": "HAS_PAGE", "from": "Document", "to": "Page"},
            {"type": "CONTAINS_SECTION", "from": "Page", "to": "Section"},
            {"type": "MENTIONS", "from": "Section", "to": "Keyword"},
            {"type": "MENTIONS", "from": "Page", "to": "Keyword"}
        ]
    }
    
    return analysis

if __name__ == "__main__":
    pdf_path = "README_CHESTXRAY.pdf"
    
    print("🔍 Extracting content from PDF...")
    content = extract_pdf_content(pdf_path)
    
    print(f"📄 Extracted {content['metadata']['total_pages']} pages")
    print(f"📝 Found {len(content['sections'])} sections")
    
    print("\n🧠 Analyzing content structure...")
    analysis = analyze_content_structure(content)
    
    # Save extracted content
    with open("extracted_content.json", "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    
    with open("content_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print("✅ Content extraction complete!")
    print(f"📊 Identified {len(analysis['key_entities'])} entity categories")
    print(f"🔗 Suggested {len(analysis['suggested_schema']['nodes'])} node types")
    print(f"🔗 Suggested {len(analysis['suggested_schema']['relationships'])} relationship types")
    
    # Print summary
    print("\n📋 Content Summary:")
    for page in content["pages"][:2]:  # Show first 2 pages
        print(f"Page {page['page_number']}: {page['word_count']} words")
        print(f"Preview: {page['text'][:200]}...")
        print("-" * 50)
