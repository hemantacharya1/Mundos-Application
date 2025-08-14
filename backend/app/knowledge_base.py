import os
import uuid
from typing import List, Dict, Any
import logging

from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
import google.generativeai as genai

# Assuming your models.py is in the same directory or accessible
from .models import KnowledgeBase

# --- Configuration ---
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "knowledge-base-gemini")

# Google AI (Gemini) Configuration
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
# The latest text embedding model from the Gemini family
EMBEDDING_MODEL_NAME = "models/text-embedding-004"

# --- Main Service Class ---

class KnowledgeBaseService:
    def __init__(self):
        """Initializes Pinecone, Google AI SDK, and the text splitter."""
        # --- Validate Environment Variables ---
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY must be set in environment variables.")
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set to use the Gemini embedding models.")

        # --- Initialize Google AI (Gemini) ---
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            # The dimension for Google's text-embedding-004 model is 768
            self.embedding_dimension = 768
            logger.info(f"Successfully configured Google AI with model: {EMBEDDING_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to configure Google AI SDK: {e}")
            raise

        # --- Initialize Pinecone ---
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self._setup_pinecone_index()

        # --- Initialize Text Splitter ---
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def _setup_pinecone_index(self):
        """Checks for the Pinecone index and creates it if it doesn't exist."""
        if PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
            logger.info(f"Creating new Pinecone index: '{PINECONE_INDEX_NAME}' with dimension {self.embedding_dimension}")
            self.pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=self.embedding_dimension,
                metric="cosine",  # Cosine similarity is excellent for text embeddings
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        self.index = self.pc.Index(PINECONE_INDEX_NAME)
        logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' is ready.")

    def _embed_content(self, content: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """
        Generates embeddings for a list of texts using the Gemini API.
        task_type can be: "RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT", "SEMANTIC_SIMILARITY", etc.
        """
        try:
            # The embed_content method can handle a list of texts directly
            result = genai.embed_content(
                model=EMBEDDING_MODEL_NAME,
                content=content,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embeddings with Gemini API: {e}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        """Splits text into manageable chunks."""
        try:
            return self.text_splitter.split_text(text)
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise

    def store_knowledge_base(self, title: str, content: str, db: Session) -> Dict[str, Any]:
        """Chunks, embeds, and stores knowledge base content."""
        try:
            # Clean up existing entries to avoid duplication and ensure consistency
            self.delete_knowledge_base(title, db)

            chunks = self.chunk_text(content)
            if not chunks:
                logger.warning(f"No chunks were created for title '{title}'. Nothing to store.")
                return {'title': title, 'chunks_count': 0, 'chunks': []}

            # Embed all chunks in a single batch call for efficiency
            # For storing documents, the task_type is RETRIEVAL_DOCUMENT
            chunk_embeddings = self._embed_content(chunks, task_type="RETRIEVAL_DOCUMENT")

            vectors_to_upsert = []
            stored_chunks_info = []
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                
                vectors_to_upsert.append({
                    'id': chunk_id,
                    'values': chunk_embeddings[i],
                    'metadata': {'title': title, 'content': chunk,'chunk_index': i}
                })

                db.add(KnowledgeBase(title=title, content=chunk, chunk_id=chunk_id))
                stored_chunks_info.append({'chunk_id': chunk_id, 'content': chunk})

            if vectors_to_upsert:
                self.index.upsert(vectors=vectors_to_upsert)

            db.commit()
            logger.info(f"Successfully stored {len(chunks)} chunks for title '{title}'.")
            return {'title': title, 'chunks_count': len(chunks), 'chunks': stored_chunks_info}

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing knowledge base '{title}': {e}")
            raise

    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Embeds a query and searches the vector store."""
        try:
            # For search, the task_type is RETRIEVAL_QUERY
            query_embedding = self._embed_content([query], task_type="RETRIEVAL_QUERY")[0]

            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            print("-"*50,search_results)

            results = []
            for match in search_results.matches:
                results.append({
                'chunk_id': match.id,
                'score': match.score,
                'content': match.metadata.get('content', ''), # .get() is safe
                'title': match.metadata.get('title', ''),     # .get() is safe
                'chunk_index': match.metadata.get('chunk_index', -1) # <-- THIS MAKES THE CODE MORE ROBUST
            })
            return results

        except Exception as e:
            logger.error(f"Error searching knowledge base with query '{query}': {e}")
            raise

    def get_all_knowledge_base(self, db: Session) -> List[Dict[str, Any]]:
        """Gets all knowledge base entries from the database, grouped by title."""
        try:
            # Query all entries and order them to ensure consistent grouping
            entries = db.query(KnowledgeBase).order_by(KnowledgeBase.title, KnowledgeBase.id).all()
            
            # Group entries by title in a dictionary
            grouped_entries = {}
            for entry in entries:
                if entry.title not in grouped_entries:
                    grouped_entries[entry.title] = {
                        'title': entry.title,
                        'chunks': [],
                        'created_at': entry.created_at.isoformat() if entry.created_at else None,
                        'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                    }
                
                grouped_entries[entry.title]['chunks'].append({
                    'id': entry.id, # Using the database ID
                    'content': entry.content,
                    'chunk_id': entry.chunk_id, # The Pinecone ID
                    'created_at': entry.created_at.isoformat() if entry.created_at else None,
                    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                })
            
            # Return the grouped entries as a list
            return list(grouped_entries.values())
            
        except Exception as e:
            # Use f-string for better formatting and include traceback
            logger.error(f"Error getting all knowledge base entries: {e}")
            raise

    def delete_knowledge_base(self, title: str, db: Session) -> bool:
        """Deletes a knowledge base entry from both Pinecone and the database."""
        try:
            logger.info(f"Attempting to delete knowledge base with title: '{title}'")
            
            # First, find all entries with this title
            entries = db.query(KnowledgeBase).filter(KnowledgeBase.title == title).all()
            logger.info(f"Found {len(entries)} entries with title '{title}'")
            
            if not entries:
                logger.warning(f"No entries found with title '{title}'")
                return False

            # Collect chunk IDs for Pinecone deletion
            chunk_ids = [entry.chunk_id for entry in entries if entry.chunk_id]
            logger.info(f"Found {len(chunk_ids)} chunk IDs to delete from Pinecone")
            
            # Delete from Pinecone if we have chunk IDs
            if chunk_ids:
                try:
                    self.index.delete(ids=chunk_ids)
                    logger.info(f"Successfully deleted {len(chunk_ids)} chunks from Pinecone")
                except Exception as pinecone_error:
                    logger.error(f"Error deleting from Pinecone: {pinecone_error}")
                    # Continue with database deletion even if Pinecone fails

            # Delete from database
            deleted_count = 0
            for entry in entries:
                try:
                    db.delete(entry)
                    deleted_count += 1
                except Exception as db_error:
                    logger.error(f"Error deleting entry {entry.id} from database: {db_error}")

            # Commit the transaction
            db.commit()
            logger.info(f"Successfully deleted {deleted_count} entries from database")
            
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting knowledge base '{title}': {e}")
            raise

# --- Example of creating a global instance ---
knowledge_base_service = KnowledgeBaseService()