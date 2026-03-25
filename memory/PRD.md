# TubeSight AI - Product Requirements Document

## Original Problem Statement
Build a full-stack web application that acts as an AI-powered YouTube Analytics Search Engine. Users can type natural language questions and get YouTube insights.

## Architecture

### Tech Stack
- **Frontend**: React 19, TailwindCSS, Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT-4o-mini (via emergentintegrations)
- **External API**: YouTube Data API v3

### Agentic AI Architecture
```
User Query → LLM Intent Classification → Tool Selection → YouTube API → LLM Summary → Frontend Display
```

### Project Structure
```
/app/
├── backend/
│   ├── server.py      # FastAPI endpoints
│   ├── agent.py       # Agent orchestration
│   ├── analyzer.py    # YouTube API tools
│   └── llm.py         # OpenAI integration
└── frontend/
    └── src/pages/HomePage.jsx  # Main UI
```

## Core Requirements (Static)

### User Personas
1. **Content Creators**: Want to analyze trending content, competitor channels
2. **Music Fans**: Searching for artist videos, first/latest uploads
3. **Researchers**: Analyzing channel growth and statistics

### Features
1. Natural language search input
2. AI-powered intent classification
3. YouTube data fetching (trending, first video, latest video, channel growth)
4. LLM-generated insights
5. Video cards with thumbnails and statistics

## What's Been Implemented (Jan 2026)

### Backend
- [x] FastAPI server with CORS
- [x] Agent module with tool registry
- [x] LLM module for intent classification and summarization
- [x] Analyzer module with YouTube API tools:
  - get_trending_videos()
  - get_first_video(artist)
  - get_latest_video(artist)
  - analyze_channel_growth(artist)
  - search_videos(query)
- [x] Search history stored in MongoDB
- [x] Health check endpoints

### Frontend
- [x] Dark analytics dashboard UI
- [x] Glassmorphism design with neon accents
- [x] Search input with suggestions
- [x] Loading states with skeleton UI
- [x] AI Insight card display
- [x] Video cards grid with statistics
- [x] Channel info display
- [x] Error handling for missing API keys

## Environment Variables Required
```
OPENAI_API_KEY=<your-openai-key>
YOUTUBE_API_KEY=<your-youtube-api-key>
```

## Prioritized Backlog

### P0 (Blocking)
- [ ] User needs to add API keys to .env file

### P1 (Next Sprint)
- [ ] Search history display on frontend
- [ ] Caching for YouTube API responses
- [ ] Rate limiting protection

### P2 (Future)
- [ ] Multiple region support for trending
- [ ] Channel comparison charts
- [ ] Export results to PDF
- [ ] User accounts and saved searches

## Next Action Items
1. Add real OPENAI_API_KEY to /app/backend/.env
2. Add real YOUTUBE_API_KEY to /app/backend/.env
3. Restart backend: `sudo supervisorctl restart backend`
4. Test with real queries
