"""
Analyzer Module - YouTube API tools for fetching video and channel data
"""
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Validate API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY not set in environment variables")

# Initialize YouTube API client
def get_youtube_client():
    """Create and return a YouTube API client."""
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)


def format_number(num: int) -> str:
    """Format large numbers for display (e.g., 1.5M, 2.3K)."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def parse_video_item(item: dict) -> dict:
    """Parse a YouTube API video item into a standardized format."""
    snippet = item.get('snippet', {})
    statistics = item.get('statistics', {})
    
    # Get the best available thumbnail
    thumbnails = snippet.get('thumbnails', {})
    thumbnail_url = (
        thumbnails.get('maxres', {}).get('url') or
        thumbnails.get('high', {}).get('url') or
        thumbnails.get('medium', {}).get('url') or
        thumbnails.get('default', {}).get('url', '')
    )
    
    # Parse publish date
    published_at = snippet.get('publishedAt', '')
    try:
        publish_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        formatted_date = publish_date.strftime('%B %d, %Y')
    except:
        formatted_date = published_at
    
    view_count = int(statistics.get('viewCount', 0))
    like_count = int(statistics.get('likeCount', 0))
    comment_count = int(statistics.get('commentCount', 0))
    
    return {
        'video_id': item.get('id', {}).get('videoId') or item.get('id'),
        'title': snippet.get('title', 'Unknown Title'),
        'description': snippet.get('description', '')[:200] + '...' if len(snippet.get('description', '')) > 200 else snippet.get('description', ''),
        'channel_title': snippet.get('channelTitle', 'Unknown Channel'),
        'channel_id': snippet.get('channelId', ''),
        'thumbnail_url': thumbnail_url,
        'published_at': published_at,
        'formatted_date': formatted_date,
        'view_count': view_count,
        'view_count_formatted': format_number(view_count),
        'like_count': like_count,
        'like_count_formatted': format_number(like_count),
        'comment_count': comment_count,
        'comment_count_formatted': format_number(comment_count),
        'url': f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId') or item.get('id')}"
    }


async def get_trending_videos(region_code: str = 'US', category_id: str = '10', max_results: int = 10) -> dict:
    """
    Fetch trending videos from YouTube.
    Category 10 = Music, 0 = All
    """
    try:
        youtube = get_youtube_client()
        
        request = youtube.videos().list(
            part='snippet,statistics',
            chart='mostPopular',
            regionCode=region_code,
            videoCategoryId=category_id if category_id != '0' else None,
            maxResults=max_results
        )
        
        response = request.execute()
        videos = []
        
        for item in response.get('items', []):
            # For trending, the id is a string, not a dict
            video_data = parse_video_item({
                **item,
                'id': {'videoId': item['id']} if isinstance(item['id'], str) else item['id']
            })
            video_data['video_id'] = item['id'] if isinstance(item['id'], str) else item['id'].get('videoId')
            video_data['url'] = f"https://www.youtube.com/watch?v={video_data['video_id']}"
            videos.append(video_data)
        
        return {
            'success': True,
            'type': 'trending',
            'region': region_code,
            'category': 'Music' if category_id == '10' else 'All',
            'count': len(videos),
            'videos': videos
        }
        
    except HttpError as e:
        logger.error(f"YouTube API error in get_trending_videos: {e}")
        return {'success': False, 'error': str(e), 'videos': []}
    except Exception as e:
        logger.error(f"Error in get_trending_videos: {e}")
        return {'success': False, 'error': str(e), 'videos': []}


async def search_channel(artist_name: str) -> dict:
    """Search for a YouTube channel by name and return channel details."""
    try:
        youtube = get_youtube_client()
        
        # Search for the channel
        search_request = youtube.search().list(
            part='snippet',
            q=artist_name,
            type='channel',
            maxResults=1
        )
        search_response = search_request.execute()
        
        if not search_response.get('items'):
            return {'success': False, 'error': f'Channel not found for: {artist_name}'}
        
        channel_item = search_response['items'][0]
        channel_id = channel_item['snippet']['channelId']
        
        # Get channel details
        channel_request = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get('items'):
            return {'success': False, 'error': 'Could not fetch channel details'}
        
        channel = channel_response['items'][0]
        stats = channel.get('statistics', {})
        
        return {
            'success': True,
            'channel_id': channel_id,
            'channel_title': channel['snippet'].get('title', artist_name),
            'description': channel['snippet'].get('description', '')[:200],
            'thumbnail_url': channel['snippet'].get('thumbnails', {}).get('high', {}).get('url', ''),
            'subscriber_count': int(stats.get('subscriberCount', 0)),
            'subscriber_count_formatted': format_number(int(stats.get('subscriberCount', 0))),
            'video_count': int(stats.get('videoCount', 0)),
            'view_count': int(stats.get('viewCount', 0)),
            'view_count_formatted': format_number(int(stats.get('viewCount', 0))),
            'uploads_playlist_id': channel.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
        }
        
    except HttpError as e:
        logger.error(f"YouTube API error in search_channel: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error in search_channel: {e}")
        return {'success': False, 'error': str(e)}


async def get_first_video(artist_name: str) -> dict:
    """
    Get the first (oldest) video uploaded by an artist/channel.
    """
    try:
        # First, find the channel
        channel_info = await search_channel(artist_name)
        if not channel_info.get('success'):
            return channel_info
        
        youtube = get_youtube_client()
        uploads_playlist_id = channel_info.get('uploads_playlist_id')
        
        if not uploads_playlist_id:
            return {'success': False, 'error': 'Could not find uploads playlist'}
        
        # Get all videos from uploads playlist (we need to paginate to find the oldest)
        # YouTube API returns newest first, so we need to get to the end
        all_videos = []
        next_page_token = None
        
        while True:
            playlist_request = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()
            
            for item in playlist_response.get('items', []):
                all_videos.append({
                    'video_id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet'].get('thumbnails', {}).get('high', {}).get('url', '')
                })
            
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token or len(all_videos) >= 500:  # Limit to prevent too many API calls
                break
        
        if not all_videos:
            return {'success': False, 'error': 'No videos found'}
        
        # Sort by publish date and get the oldest
        all_videos.sort(key=lambda x: x['published_at'])
        first_video = all_videos[0]
        
        # Get detailed stats for the first video
        video_request = youtube.videos().list(
            part='snippet,statistics',
            id=first_video['video_id']
        )
        video_response = video_request.execute()
        
        if video_response.get('items'):
            video_item = video_response['items'][0]
            video_data = parse_video_item({
                **video_item,
                'id': {'videoId': video_item['id']}
            })
            video_data['video_id'] = video_item['id']
            video_data['url'] = f"https://www.youtube.com/watch?v={video_item['id']}"
        else:
            video_data = first_video
        
        return {
            'success': True,
            'type': 'first_video',
            'channel': channel_info,
            'video': video_data,
            'total_videos_scanned': len(all_videos)
        }
        
    except HttpError as e:
        logger.error(f"YouTube API error in get_first_video: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error in get_first_video: {e}")
        return {'success': False, 'error': str(e)}


async def get_latest_video(artist_name: str) -> dict:
    """
    Get the latest (most recent) video uploaded by an artist/channel.
    """
    try:
        # First, find the channel
        channel_info = await search_channel(artist_name)
        if not channel_info.get('success'):
            return channel_info
        
        youtube = get_youtube_client()
        
        # Search for latest video from this channel
        search_request = youtube.search().list(
            part='snippet',
            channelId=channel_info['channel_id'],
            order='date',
            type='video',
            maxResults=1
        )
        search_response = search_request.execute()
        
        if not search_response.get('items'):
            return {'success': False, 'error': 'No videos found'}
        
        video_item = search_response['items'][0]
        video_id = video_item['id']['videoId']
        
        # Get detailed stats
        video_request = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        video_response = video_request.execute()
        
        if video_response.get('items'):
            video_item = video_response['items'][0]
            video_data = parse_video_item({
                **video_item,
                'id': {'videoId': video_item['id']}
            })
            video_data['video_id'] = video_item['id']
            video_data['url'] = f"https://www.youtube.com/watch?v={video_item['id']}"
        else:
            video_data = parse_video_item(video_item)
        
        return {
            'success': True,
            'type': 'latest_video',
            'channel': channel_info,
            'video': video_data
        }
        
    except HttpError as e:
        logger.error(f"YouTube API error in get_latest_video: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error in get_latest_video: {e}")
        return {'success': False, 'error': str(e)}


async def analyze_channel_growth(artist_name: str = None) -> dict:
    """
    Analyze channel growth. If no artist specified, compare top music channels.
    Returns channel statistics and relative growth indicators.
    """
    try:
        youtube = get_youtube_client()
        
        if artist_name:
            # Analyze specific channel
            channel_info = await search_channel(artist_name)
            if not channel_info.get('success'):
                return channel_info
            
            # Get recent videos to analyze upload frequency
            search_request = youtube.search().list(
                part='snippet',
                channelId=channel_info['channel_id'],
                order='date',
                type='video',
                maxResults=10
            )
            search_response = search_request.execute()
            
            recent_videos = []
            for item in search_response.get('items', []):
                recent_videos.append({
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt']
                })
            
            return {
                'success': True,
                'type': 'channel_growth',
                'channel': channel_info,
                'recent_videos': recent_videos,
                'upload_frequency': f"{len(recent_videos)} videos in recent uploads"
            }
        else:
            # Compare top music channels
            top_channels = ['T-Series', 'MrBeast', 'Cocomelon', 'SET India', 'PewDiePie']
            channels_data = []
            
            for channel_name in top_channels:
                channel_info = await search_channel(channel_name)
                if channel_info.get('success'):
                    channels_data.append({
                        'name': channel_info['channel_title'],
                        'subscribers': channel_info['subscriber_count'],
                        'subscribers_formatted': channel_info['subscriber_count_formatted'],
                        'total_views': channel_info['view_count'],
                        'total_views_formatted': channel_info['view_count_formatted'],
                        'video_count': channel_info['video_count']
                    })
            
            # Sort by subscribers
            channels_data.sort(key=lambda x: x['subscribers'], reverse=True)
            
            return {
                'success': True,
                'type': 'channel_comparison',
                'channels': channels_data,
                'top_channel': channels_data[0] if channels_data else None
            }
        
    except HttpError as e:
        logger.error(f"YouTube API error in analyze_channel_growth: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error in analyze_channel_growth: {e}")
        return {'success': False, 'error': str(e)}


async def search_videos(query: str, max_results: int = 10) -> dict:
    """
    General video search on YouTube.
    """
    try:
        youtube = get_youtube_client()
        
        search_request = youtube.search().list(
            part='snippet',
            q=query,
            type='video',
            maxResults=max_results,
            order='relevance'
        )
        search_response = search_request.execute()
        
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        
        if not video_ids:
            return {'success': False, 'error': 'No videos found', 'videos': []}
        
        # Get detailed stats for all videos
        videos_request = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(video_ids)
        )
        videos_response = videos_request.execute()
        
        videos = []
        for item in videos_response.get('items', []):
            video_data = parse_video_item({
                **item,
                'id': {'videoId': item['id']}
            })
            video_data['video_id'] = item['id']
            video_data['url'] = f"https://www.youtube.com/watch?v={item['id']}"
            videos.append(video_data)
        
        return {
            'success': True,
            'type': 'search',
            'query': query,
            'count': len(videos),
            'videos': videos
        }
        
    except HttpError as e:
        logger.error(f"YouTube API error in search_videos: {e}")
        return {'success': False, 'error': str(e), 'videos': []}
    except Exception as e:
        logger.error(f"Error in search_videos: {e}")
        return {'success': False, 'error': str(e), 'videos': []}
