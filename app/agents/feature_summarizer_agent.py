from agents import Agent, function_tool
from typing import Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup
import os
from .vector_store import VectorStore

DOCS_PATH = os.getenv("PD_DOCS_PATH", "./resource/pd_docs")

feature_store = VectorStore(table_name="pd_features")

summarizer_agent = Agent(
    name="FeatureSummarizer",
    instructions="""Create clear summaries of Product Designer features.

Format:
**Feature: [Name]**
**Description:** [2-3 sentences]
**Key Points:**
- Point 1
- Point 2
**Example:** [Simple example]

Keep concise and practical.""",
    model="gpt-4o-mini"
)

def read_file(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if file_path.suffix in [".html", ".htm"]:
        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    return content

def index_documents(docs_path: str = DOCS_PATH) -> Dict:
    path = Path(docs_path)
    if not path.exists():
        return {"status": "error", "message": f"Path not found: {docs_path}"}
    
    count = 0
    for file_path in path.rglob("*"):
        if file_path.suffix in [".html", ".htm", ".md", ".txt"]:
            try:
                content = read_file(file_path)
                doc_id = str(file_path.relative_to(path))
                
                feature_store.add(
                    doc_id=doc_id,
                    content=content,
                    metadata={"filename": file_path.name, "path": str(file_path)}
                )
                count += 1
            except Exception as e:
                print(f"Error: {e}")
    
    return {"status": "success", "indexed": count, "total": feature_store.count()}


def search_documentation(query: str) -> Dict:
    """Search PD documentation and return summary"""
    
    if feature_store.count() == 0:
        index_documents()
    
    docs = feature_store.search(query, limit=3)
    
    if not docs:
        return {"status": "no_results", "message": "No documentation found"}
    
    context = "\n\n".join([
        f"Source: {doc['metadata']['filename']}\n{doc['content'][:1000]}"
        for doc in docs
    ])
    
    result = summarizer_agent.run(f"Query: {query}\n\nContext:\n{context}")
    summary = result.final_output if hasattr(result, 'final_output') else str(result)
    
    return {
        "status": "success",
        "summary": summary,
        "sources": [doc["metadata"]["filename"] for doc in docs]
    }

@function_tool
def explain_feature(feature_name: str, detail_level: str = "standard") -> Dict:
    """Explain Product Designer features"""
    
    query = f"Product Designer {feature_name}"
    if detail_level == "detailed":
        query += " detailed with examples"
    elif detail_level == "brief":
        query += " brief overview"
    
    result = search_documentation(query)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "feature": feature_name,
            "explanation": result["summary"],
            "sources": result["sources"]
        }
    
    return {"status": "not_found", "feature": feature_name}

@function_tool
def add_approved_response(query: str, response: str) -> Dict:
    """Store approved responses for learning"""
    
    doc_id = f"approved_{hash(query)}"
    content = f"Query: {query}\nResponse: {response}"
    
    feature_store.add(
        doc_id=doc_id,
        content=content,
        metadata={"type": "approved", "query": query}
    )
    
    return {"status": "success", "message": "Stored for learning"}

@function_tool
def reindex_documentation(docs_path: Optional[str] = None) -> Dict:
    """Reindex all documentation"""
    return index_documents(docs_path or DOCS_PATH)