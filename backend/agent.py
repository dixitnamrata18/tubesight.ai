"""
Agent Module - Orchestrates the agentic AI workflow
User query -> LLM planning -> Tool execution -> LLM summary
"""
import logging
from llm import classify_intent, summarize_results
from analyzer import (
    get_trending_videos,
    get_first_video,
    get_latest_video,
    analyze_channel_growth,
    search_videos
)

logger = logging.getLogger(__name__)

# Tool registry - maps tool names to functions
TOOLS = {
    'get_trending_videos': get_trending_videos,
    'get_first_video': get_first_video,
    'get_latest_video': get_latest_video,
    'analyze_channel_growth': analyze_channel_growth,
    'search_videos': search_videos
}


async def process_query(query: str) -> dict:
    """
    Main agent function that orchestrates the full workflow:
    1. LLM interprets intent
    2. Agent selects appropriate tool
    3. Tool calls YouTube API
    4. LLM summarizes results
    
    Returns a dict with:
    - success: bool
    - query: original query
    - intent: classified intent
    - tool_used: name of tool called
    - data: raw YouTube data
    - insight: LLM-generated summary
    - error: error message if any
    """
    result = {
        'success': False,
        'query': query,
        'intent': None,
        'tool_used': None,
        'data': None,
        'insight': None,
        'error': None
    }
    
    try:
        # Step 1: Classify intent using LLM
        logger.info(f"Processing query: {query}")
        intent_data = await classify_intent(query)
        result['intent'] = intent_data
        
        # Step 2: Select and execute the appropriate tool
        tool_name = intent_data.get('tool', 'search_videos')
        artist = intent_data.get('artist')
        search_term = intent_data.get('search_term')
        
        logger.info(f"Selected tool: {tool_name}, artist: {artist}")
        
        if tool_name not in TOOLS:
            logger.warning(f"Unknown tool: {tool_name}, falling back to search_videos")
            tool_name = 'search_videos'
        
        result['tool_used'] = tool_name
        
        # Step 3: Execute the tool with appropriate parameters
        tool_func = TOOLS[tool_name]
        
        if tool_name == 'get_trending_videos':
            # Check if query mentions music
            if any(word in query.lower() for word in ['song', 'music', 'track', 'album']):
                data = await tool_func(category_id='10')  # Music category
            else:
                data = await tool_func(category_id='0')  # All categories
                
        elif tool_name in ['get_first_video', 'get_latest_video']:
            if not artist:
                # Try to extract artist from query
                data = await search_videos(query)
            else:
                data = await tool_func(artist)
                
        elif tool_name == 'analyze_channel_growth':
            data = await tool_func(artist)
            
        elif tool_name == 'search_videos':
            search_query = search_term or artist or query
            data = await tool_func(search_query)
        else:
            data = await search_videos(query)
        
        result['data'] = data
        
        # Check if tool execution was successful
        if not data.get('success', False):
            result['error'] = data.get('error', 'Unknown error occurred')
            result['insight'] = f"I couldn't find the information you requested. Error: {result['error']}"
            return result
        
        # Step 4: Generate summary using LLM
        insight = await summarize_results(query, data)
        result['insight'] = insight
        result['success'] = True
        
        logger.info(f"Query processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        result['error'] = str(e)
        result['insight'] = "I encountered an error while processing your request. Please try again."
        return result


async def get_suggested_queries() -> list:
    """
    Return a list of suggested queries to help users get started.
    """
    return [
        "What is the number one trending song on YouTube right now?",
        "Justin Bieber's first video uploaded on YouTube",
        "Taylor Swift's latest music video",
        "Which artist is growing fastest on YouTube?",
        "Most viewed MrBeast video",
        "Trending videos in the US today"
    ]
