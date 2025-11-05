from typing import List, Dict, Optional
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# OpenAI Vector Store ID
VECTOR_STORE_ID = "vs_690b579d1b048191b0dafb2d39db50fb"

class VectorStore:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.vector_store_id = VECTOR_STORE_ID
            self.client = client
            self._initialized = True
            self._verify_connection()
    
    def _verify_connection(self):
        """Verify connection to OpenAI vector store"""
        try:
            # Test retrieval to verify vector store exists
            self.client.beta.vector_stores.retrieve(self.vector_store_id)
            print(f"✓ Connected to OpenAI Vector Store: {self.vector_store_id}")
        except Exception as e:
            print(f"⚠️  Vector store connection failed: {e}")
            raise
    
    def search(self, query: str, limit: int = 3, doc_type: Optional[str] = None) -> List[Dict]:
        """
        Search using OpenAI's vector store file search
        
        Args:
            query: Search query text
            limit: Maximum number of results (Note: OpenAI manages this internally)
            doc_type: Optional document type filter (applied post-retrieval)
        
        Returns:
            List of documents with content, metadata, and score
        """
        try:
            # Create a thread with the query
            thread = self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ]
            )
            
            # Create assistant with file search
            assistant = self.client.beta.assistants.create(
                name="Document Retriever",
                instructions="You retrieve relevant documents based on user queries.",
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            # Get messages with file citations
            messages = list(self.client.beta.threads.messages.list(
                thread_id=thread.id,
                run_id=run.id
            ))
            
            results = []
            
            # Extract file citations from annotations
            if messages and len(messages) > 0:
                message_content = messages[0].content[0].text
                annotations = message_content.annotations
                
                # Track processed file IDs to avoid duplicates
                processed_files = set()
                
                for annotation in annotations:
                    if hasattr(annotation, 'file_citation'):
                        file_id = annotation.file_citation.file_id
                        
                        # Skip if already processed
                        if file_id in processed_files:
                            continue
                        processed_files.add(file_id)
                        
                        # Retrieve file details
                        try:
                            file_obj = self.client.files.retrieve(file_id)
                            
                            # Get file content (if accessible)
                            file_content = self.client.files.content(file_id)
                            content_text = file_content.text if hasattr(file_content, 'text') else str(file_content.read())
                            
                            result = {
                                'doc_id': file_id,
                                'content': content_text[:2000],  # Truncate for display
                                'metadata': {
                                    'filename': file_obj.filename,
                                    'file_id': file_id,
                                    'created_at': file_obj.created_at,
                                    'bytes': file_obj.bytes
                                },
                                'doc_type': self._infer_doc_type(file_obj.filename),
                                'score': 0.9  # OpenAI doesn't provide scores
                            }
                            
                            # Apply doc_type filter if specified
                            if doc_type is None or result['doc_type'] == doc_type:
                                results.append(result)
                                
                                # Limit results
                                if len(results) >= limit:
                                    break
                        except Exception as e:
                            print(f"⚠️  Error retrieving file {file_id}: {e}")
                            continue
            
            # Cleanup
            self.client.beta.assistants.delete(assistant.id)
            self.client.beta.threads.delete(thread.id)
            
            return results
            
        except Exception as e:
            print(f"⚠️  Search error: {e}")
            return []
    
    def _infer_doc_type(self, filename: str) -> str:
        """Infer document type from filename"""
        filename_lower = filename.lower()
        
        if any(kw in filename_lower for kw in ['config', 'setup', 'configure']):
            return "config"
        elif any(kw in filename_lower for kw in ['feature', 'entity', 'view']):
            return "feature"
        return "general"
    
    def count(self, doc_type: Optional[str] = None) -> int:
        """
        Get count of files in vector store
        Note: OpenAI doesn't provide type-based filtering, so we return total count
        """
        try:
            vector_store = self.client.beta.vector_stores.retrieve(self.vector_store_id)
            file_counts = vector_store.file_counts
            return file_counts.completed if hasattr(file_counts, 'completed') else 0
        except Exception as e:
            print(f"⚠️  Error getting count: {e}")
            return 0
    
    def is_connected(self) -> bool:
        """Check if vector store is accessible"""
        try:
            self.client.beta.vector_stores.retrieve(self.vector_store_id)
            return True
        except:
            return False
    
    def add(self, doc_id: str, content: str, metadata: Dict, doc_type: str = "general"):
        """
        Add/upload a document to OpenAI vector store
        Note: This requires file upload which is different from the search flow
        """
        try:
            # Create a temporary file with content
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            # Upload file to OpenAI
            with open(tmp_path, 'rb') as f:
                file_obj = self.client.files.create(
                    file=f,
                    purpose='assistants'
                )
            
            # Add file to vector store
            self.client.beta.vector_stores.files.create(
                vector_store_id=self.vector_store_id,
                file_id=file_obj.id
            )
            
            # Cleanup temp file
            os.unlink(tmp_path)
            
            print(f"✓ Added document {metadata.get('filename', doc_id)} to vector store")
            
        except Exception as e:
            print(f"⚠️  Error adding document: {e}")
    
    def close(self):
        """Cleanup (no-op for OpenAI API)"""
        pass


vector_store = VectorStore()