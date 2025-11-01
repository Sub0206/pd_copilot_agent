"""
Manual script to index Product Designer documentation into the vector store.
Run this script to process HTML files from resource/pd_docs/ directory.

Usage:
    python scripts/index_documents.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.vector_store import vector_store
from app.core.document_processor import doc_processor

def main():
    print("\n" + "=" * 60)
    print("📚 PD Copilot Document Indexer")
    print("=" * 60)
    
    try:
        # Check if vector store is connected
        if not vector_store.is_connected():
            print("⚠️  Connecting to vector store...")
            vector_store._ensure_connection()
        
        print("✓ Vector store connected")
        
        # Check for new documents
        print("\n🔍 Checking for documents to index...")
        
        if not doc_processor.has_new_documents():
            print("✓ No new documents found in resource/pd_docs/")
            
            # Show current stats
            total = vector_store.count()
            features = vector_store.count(doc_type="feature")
            config = vector_store.count(doc_type="config")
            general = vector_store.count(doc_type="general")
            
            print(f"\n📊 Current Vector Store Statistics:")
            print(f"   Total documents: {total}")
            print(f"   Feature docs: {features}")
            print(f"   Config docs: {config}")
            print(f"   General docs: {general}")
            return
        
        # Process documents
        print("📄 Processing documents from resource/pd_docs/...")
        result = doc_processor.process_new_documents()
        
        if result["processed"]:
            print(f"\n✓ Found {len(result['processed'])} documents to process\n")
            
            # Index each document
            for i, doc in enumerate(result["processed"], 1):
                filename = doc['metadata']['filename']
                doc_type = doc['doc_type']
                print(f"   [{i}/{len(result['processed'])}] Indexing: {filename}")
                print(f"        Type: {doc_type}")
                print(f"        Content length: {len(doc['content'])} chars")
                
                vector_store.add(
                    doc_id=doc["doc_id"],
                    content=doc["content"],
                    metadata=doc["metadata"],
                    doc_type=doc["doc_type"]
                )
                print(f"        ✓ Indexed successfully\n")
            
            print(f"✅ Successfully indexed {len(result['processed'])} documents!")
            print(f"   Documents moved to: resource/processed/")
        
        # Show errors if any
        if result["errors"]:
            print(f"\n⚠️  Encountered {len(result['errors'])} errors:")
            for error in result["errors"]:
                print(f"   - {error}")
        
        # Show final statistics
        print("\n" + "=" * 60)
        total = vector_store.count()
        features = vector_store.count(doc_type="feature")
        config = vector_store.count(doc_type="config")
        general = vector_store.count(doc_type="general")
        
        print("📊 Final Vector Store Statistics:")
        print(f"   Total documents: {total}")
        print(f"   Feature docs: {features}")
        print(f"   Config docs: {config}")
        print(f"   General docs: {general}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during indexing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()