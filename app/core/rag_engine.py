from typing import List, Dict, Optional
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RAGEngine:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def query(self, query: str, system_prompt: str, limit: int = 3, doc_type: Optional[str] = None) -> str:
        docs = self.vector_store.search(query, limit=limit, doc_type=doc_type)
        
        if not docs:
            return "No relevant documentation found. Please check if documents are indexed."
        
        context = "\n\n".join([
            f"[Source: {doc['metadata']['filename']}]\n{doc['content'][:2000]}"
            for doc in docs
        ])
        
        sources = [f"{doc['metadata']['filename']} (score: {doc['score']:.2f})" for doc in docs]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nContext:\n{context}"}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        return f"{answer}\n\n📚 Sources: {', '.join(sources)}"