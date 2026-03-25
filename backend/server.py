from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Validate required API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
    logging.warning("OPENAI_API_KEY not set or using placeholder - AI features will not work")

if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "your_youtube_api_key_here":
    logging.warning("YOUTUBE_API_KEY not set or using placeholder - YouTube features will not work")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="TubeSight AI", description="AI-powered YouTube Analytics Search Engine")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import agent after environment is loaded
from agent import process_query, get_suggested_queries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language search query")


class VideoData(BaseModel):
    video_id: str
    title: str
    description: Optional[str] = None
    channel_title: str
    channel_id: Optional[str] = None
    thumbnail_url: str
    published_at: Optional[str] = None
    formatted_date: Optional[str] = None
    view_count: int = 0
    view_count_formatted: str = "0"
    like_count: int = 0
    like_count_formatted: str = "0"
    comment_count: int = 0
    comment_count_formatted: str = "0"
    url: str


class SearchResponse(BaseModel):
    success: bool
    query: str
    intent: Optional[dict] = None
    tool_used: Optional[str] = None
    insight: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


class SearchHistoryItem(BaseModel):
    id: str
    query: str
    intent: Optional[dict] = None
    tool_used: Optional[str] = None
    success: bool
    timestamp: datetime


# API Endpoints
@api_router.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "TubeSight AI API is running", "version": "1.0.0"}


@api_router.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here"),
        "youtube_configured": bool(YOUTUBE_API_KEY and YOUTUBE_API_KEY != "your_youtube_api_key_here")
    }


@api_router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Main search endpoint - processes natural language queries about YouTube.
    
    The AI agent will:
    1. Interpret your query intent
    2. Select the appropriate tool (trending, first video, latest video, etc.)
    3. Fetch data from YouTube API
    4. Generate an insightful summary
    """
    try:
        # Check if API keys are configured
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise HTTPException(
                status_code=503,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in environment variables."
            )
        
        if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "your_youtube_api_key_here":
            raise HTTPException(
                status_code=503,
                detail="YouTube API key not configured. Please set YOUTUBE_API_KEY in environment variables."
            )
        
        # Process the query through the agent
        result = await process_query(request.query)
        
        # Store search in history (without _id)
        history_doc = {
            "id": str(hash(f"{request.query}{datetime.now(timezone.utc).isoformat()}")),
            "query": request.query,
            "intent": result.get('intent'),
            "tool_used": result.get('tool_used'),
            "success": result.get('success', False),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.search_history.insert_one(history_doc)
        
        return SearchResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/suggestions", response_model=List[str])
async def get_suggestions():
    """Get suggested queries to help users get started."""
    return await get_suggested_queries()


@api_router.get("/history", response_model=List[SearchHistoryItem])
async def get_search_history(limit: int = 10):
    """Get recent search history."""
    history = await db.search_history.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Convert timestamp strings back to datetime if needed
    for item in history:
        if isinstance(item.get('timestamp'), str):
            item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
    
    return history


# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
