from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from ..database import get_db
from ..knowledge_base import knowledge_base_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str

class KnowledgeBaseSearch(BaseModel):
    query: str
    top_k: int = 5

class KnowledgeBaseResponse(BaseModel):
    title: str
    chunks_count: int
    chunks: List[Dict[str, Any]]

class SearchResult(BaseModel):
    chunk_id: str
    score: float
    content: str
    title: str
    chunk_index: int

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int

@router.post("/knowledge-base", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,
    db: Session = Depends(get_db)
):
    """
    Create or update knowledge base content.
    If a knowledge base with the same title exists, it will be updated.
    """
    try:
        result = knowledge_base_service.store_knowledge_base(
            title=knowledge_base.title,
            content=knowledge_base.content,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/search", response_model=SearchResponse)
async def search_knowledge_base(search_request: KnowledgeBaseSearch):
    """
    Search knowledge base using semantic search.
    """
    try:
        results = knowledge_base_service.search_knowledge_base(
            query=search_request.query,
            top_k=search_request.top_k
        )
        
        # Convert to Pydantic models
        search_results = [
            SearchResult(
                chunk_id=result['chunk_id'],
                score=result['score'],
                content=result['content'],
                title=result['title'],
                chunk_index=result['chunk_index']
            )
            for result in results
        ]
        
        return SearchResponse(
            results=search_results,
            query=search_request.query,
            total_results=len(search_results)
        )
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base", response_model=List[Dict[str, Any]])
async def get_all_knowledge_base(db: Session = Depends(get_db)):
    """
    Get all knowledge base entries grouped by title.
    """
    try:
        return knowledge_base_service.get_all_knowledge_base(db)
    except Exception as e:
        logger.error(f"Error getting knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge-base/{title}")
async def delete_knowledge_base(title: str, db: Session = Depends(get_db)):
    """
    Delete knowledge base entry by title.
    """
    try:
        deleted = knowledge_base_service.delete_knowledge_base(title, db)
        if not deleted:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"message": f"Knowledge base '{title}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/search/{query}")
async def quick_search_knowledge_base(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """
    Quick search endpoint using URL parameter.
    """
    try:
        results = knowledge_base_service.search_knowledge_base(query, top_k)
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        logger.error(f"Error in quick search: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 