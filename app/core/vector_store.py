from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/pd_copilot")

class VectorStore:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.conn = None
            self._initialized = True
    
    def _ensure_connection(self):
        """Lazy connection - only connect when actually needed"""
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(DATABASE_URL)
                self._init_db()
            except Exception as e:
                print(f"⚠️  Database connection failed: {e}")
                print(f"⚠️  Vector store features will be limited until database is available")
                raise
    
    def _init_db(self):
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    doc_id VARCHAR(255) UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    metadata JSONB,
                    doc_type VARCHAR(50) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
        self.conn.commit()
    
    def _get_embedding(self, text: str) -> List[float]:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]
        )
        return response.data[0].embedding
    
    def add(self, doc_id: str, content: str, metadata: Dict, doc_type: str = "general"):
        self._ensure_connection()
        
        embedding = self._get_embedding(content)
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (doc_id, content, embedding, metadata, doc_type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    doc_type = EXCLUDED.doc_type,
                    created_at = CURRENT_TIMESTAMP
            """, (doc_id, content, embedding, Json(metadata), doc_type))
        self.conn.commit()
    
    def search(self, query: str, limit: int = 3, doc_type: Optional[str] = None) -> List[Dict]:
        self._ensure_connection()
        
        query_embedding = self._get_embedding(query)
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            if doc_type:
                cur.execute("""
                    SELECT doc_id, content, metadata, doc_type,
                           1 - (embedding <=> %s::vector) as score
                    FROM documents
                    WHERE doc_type = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, doc_type, query_embedding, limit))
            else:
                cur.execute("""
                    SELECT doc_id, content, metadata, doc_type,
                           1 - (embedding <=> %s::vector) as score
                    FROM documents
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    def count(self, doc_type: Optional[str] = None) -> int:
        self._ensure_connection()
        
        with self.conn.cursor() as cur:
            if doc_type:
                cur.execute("SELECT COUNT(*) FROM documents WHERE doc_type = %s", (doc_type,))
            else:
                cur.execute("SELECT COUNT(*) FROM documents")
            return cur.fetchone()[0]
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.conn is not None
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

vector_store = VectorStore()