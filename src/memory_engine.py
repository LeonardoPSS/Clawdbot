import os
import logging
import chromadb
from datetime import datetime
from src.ai_assistant import AIAssistant
from src.config import Settings
import uuid

logger = logging.getLogger(__name__)

class MemoryEngine:
    def __init__(self, config: Settings):
        self.config = config
        self.ai = AIAssistant(config)
        self.db_path = os.path.join(os.getcwd(), "data", "chroma_db")
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB Client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or Get Collection
        self.collection = self.client.get_or_create_collection(name="nexara_memories")

    def store_interaction(self, role: str, content: str):
        """Stores a chat interaction (User or Assistant) into vector memory."""
        try:
            # We need an embedding function. 
            # Ideally ChromaDB uses a default one (all-MiniLM-L6-v2) if none provided, but it requires downloading model.
            # OR we can use OpenAI embeddings if we want better quality.
            # Let's rely on Chroma's default for now to reduce dependencies/costs, 
            # BUT if it fails on Windows or is too heavy, we might switch to OpenAI API manually.
            
            # NOTE: Chroma default requires 'sentence-transformers'.
            
            self.collection.add(
                documents=[content],
                metadatas=[{"role": role, "timestamp": datetime.now().isoformat()}],
                ids=[str(uuid.uuid4())]
            )
            logger.info(f"🧠 Stored memory: {content[:30]}...")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")

    def recall_relevant(self, query: str, n_results=3) -> str:
        """Retrieves top N relevant past interactions."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            context = ""
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i]
                    role = meta.get("role", "unknown")
                    time = meta.get("timestamp", "")[:16]
                    context += f"[{time}] {role}: {doc}\n"
            
            return context
        except Exception as e:
            logger.error(f"Failed to recall memory: {e}")
            return ""
