import chromadb
import os

class VectorStore:
    def __init__(self):
        os.makedirs("./data/chromadb", exist_ok=True)
        self.client = chromadb.PersistentClient(path="./data/chromadb")
    
    def get_or_create_collection(self, sector: str):
        return self.client.get_or_create_collection(
            name=sector.lower(),
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, sector: str, documents: list, 
                      ids: list, metadatas: list):
        collection = self.get_or_create_collection(sector)
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        print(f"✅ Added {len(documents)} chunks to {sector}")
    
    def search(self, sector: str, query: str, n_results: int = 5):
        collection = self.get_or_create_collection(sector)
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}