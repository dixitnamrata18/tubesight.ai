"""
LLM Module – Handles OpenAI intent detection and summarization
"""

import os
import json
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

# load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# validate API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT_INTENT = """
You classify YouTube queries.

Return ONLY JSON in this format:

{
 "intent": "...",
 "artist": "...",
 "tool": "...",
 "search_term": "..."
}

Possible intents:
trending
first_video
latest_video
channel_growth
search_video

Rules:

If the query asks about someone's FIRST YouTube video
Examples:
"Justin Bieber first video"
"first video of MrBeast"
"what was Taylor Swift first upload"

→ intent = first_video

artist = the creator name
tool = get_first_video

If asking about trending / viral videos
→ intent = trending
tool = get_trending_videos

If asking about newest upload
→ intent = latest_video
tool = get_latest_video

If asking about fastest growing channel
→ intent = channel_growth
tool = analyze_channel_growth

Otherwise
→ intent = search_video
tool = search_videos

Return ONLY valid JSON.
"""


SYSTEM_PROMPT_SUMMARY = """
You summarize YouTube video results.

Rules:
- Answer the user's question
- Mention the most relevant video
- Include views or popularity insight if possible
- Keep response under 120 words
"""


async def classify_intent(query: str) -> dict:
    """
    Classify user intent using OpenAI
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_INTENT},
                {"role": "user", "content": query}
            ]
        )

        content = response.choices[0].message.content.strip()
        result = json.loads(content)

        result["query"] = query

        logger.info(f"Intent classified: {result}")
        return result

    except Exception as e:
        logger.exception("Intent classification failed")

        return {
            "intent": "unknown",
            "artist": None,
            "tool": "search_videos",
            "query": query,
            "search_term": query
        }


async def summarize_results(query: str, data: dict):

    try:

        videos = data.get("videos", [])[:5]

        compact_data = []

        for v in videos:
            compact_data.append({
                "title": v.get("title"),
                "channel": v.get("channel_title"),
                "views": v.get("view_count"),
                "date": v.get("formatted_date")
            })

        context = {
            "question": query,
            "videos": compact_data
        }

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SUMMARY},
                {"role": "user", "content": json.dumps(context)}
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.exception("Summary generation failed")
        return "Results found but summary generation failed."
