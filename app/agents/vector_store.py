import psycopg2
from psycopg2.extras import Json
from typing import Dict, List
import os
from openai import OpenAI

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "pd_copilot"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

class VectorStore:
    def __init__(self, table_name: str = "pd_docs"):
        self.table_name = table_name
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_dim = 1536
        self._setup_table()
    
    def _get_connection(self):
        return psycopg2.connect(**DB_CONFIG)
    
    def _setup_table(self):
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata JSONB,
                embedding vector({self.embedding_dim})
            )
        """)
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.table_name}_idx 
            ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embeddings using OpenAI's API"""
        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0.0] * self.embedding_dim  # Return zero vector on error
    
    def add(self, doc_id: str, content: str, metadata: dict):
        conn = self._get_connection()
        cur = conn.cursor()
        
        embedding = self.get_embedding(content)
        
        cur.execute(f"""
            INSERT INTO {self.table_name} (id, content, metadata, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET content = EXCLUDED.content, 
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding
        """, (doc_id, content, Json(metadata), embedding))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        
        query_embedding = self.get_embedding(query)
        
        cur.execute(f"""
            SELECT id, content, metadata
            FROM {self.table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, limit))
        
        results = [{
            "id": row[0],
            "content": row[1],
            "metadata": row[2]
        } for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        return results
    
    def count(self) -> int:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    
    def delete(self, doc_id: str):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {self.table_name} WHERE id = %s", (doc_id,))
        conn.commit()
        cur.close()
        conn.close()