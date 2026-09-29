import requests
from datetime import datetime
from models import db, Post, SocialAccount
import os


class YouTubeIntegration:
    """YouTube API integration for fetching video analytics"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def fetch_channel_videos(self, channel_id, max_results=50):
        """Fetch recent videos from a YouTube channel"""
        try:
            # Get videos from channel
            url = f"{self.base_url}/search"
            params = {
                'key': self.api_key,
                'channelId': channel_id,
                'part': 'id',
                'order': 'date',
                'maxResults': max_results
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            video_ids = [item['id']['videoId'] for item in data.get('items', []) if 'videoId' in item.get('id', {})]
            
            # Get video statistics
            videos_data = []
            if video_ids:
                stats_url = f"{self.base_url}/videos"
                stats_params = {
                    'key': self.api_key,
                    'id': ','.join(video_ids),
                    'part': 'statistics,snippet'
                }
                
                stats_response = requests.get(stats_url, params=stats_params)
                stats_response.raise_for_status()
                stats_data = stats_response.json()
                
                for video in stats_data.get('items', []):
                    stats = video.get('statistics', {})
                    snippet = video.get('snippet', {})
                    videos_data.append({
                        'platform_post_id': video['id'],
                        'content': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'posted_at': snippet.get('publishedAt'),
                        'likes': int(stats.get('likeCount', 0)),
                        'shares': int(stats.get('favoriteCount', 0)),  # YouTube doesn't have shares, using favorites
                        'comments': int(stats.get('commentCount', 0)),
                        'impressions': 0,  # YouTube API doesn't provide impressions in basic stats
                        'views': int(stats.get('viewCount', 0))
                    })
            
            return videos_data
        except Exception as e:
            print(f"Error fetching YouTube videos: {e}")
            return []
    
    def sync_videos_to_db(self, user_db_id, channel_id):
        """Sync YouTube videos to database"""
        videos_data = self.fetch_channel_videos(channel_id)
        
        synced_count = 0
        for video_data in videos_data:
            # Check if video already exists
            existing_post = Post.query.filter_by(
                user_id=user_db_id,
                platform='youtube',
                platform_post_id=video_data['platform_post_id']
            ).first()
            
            if not existing_post:
                post = Post(
                    user_id=user_db_id,
                    platform='youtube',
                    platform_post_id=video_data['platform_post_id'],
                    content=f"{video_data['content']}\n\n{video_data['description'][:500]}",
                    posted_at=video_data['posted_at'],
                    likes=video_data['likes'],
                    shares=video_data['shares'],
                    comments=video_data['comments'],
                    impressions=video_data['impressions'],
                    is_synced=True,
                    synced_at=datetime.utcnow()
                )
                post.performance_score = post.calculate_performance_score()
                db.session.add(post)
                synced_count += 1
        
        db.session.commit()
        return synced_count


class InstagramIntegration:
    """Instagram Graph API integration for fetching posts and analytics"""
    
    def __init__(self, app_id, app_secret, access_token):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.base_url = "https://graph.instagram.com"
    
    def fetch_user_media(self, user_id, limit=25):
        """Fetch recent media from Instagram"""
        try:
            # Get user's media
            url = f"{self.base_url}/{user_id}/media"
            params = {
                'access_token': self.access_token,
                'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
                'limit': limit
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            posts_data = []
            for media in data.get('data', []):
                if media.get('media_type') in ['IMAGE', 'CAROUSEL_ALBUM']:
                    posts_data.append({
                        'platform_post_id': media['id'],
                        'content': media.get('caption', ''),
                        'media_url': media.get('media_url', ''),
                        'posted_at': media.get('timestamp'),
                        'likes': int(media.get('like_count', 0)),
                        'shares': 0,  # Instagram doesn't provide share count
                        'comments': int(media.get('comments_count', 0)),
                        'impressions': 0  # Requires additional API call
                    })
            
            return posts_data
        except Exception as e:
            print(f"Error fetching Instagram posts: {e}")
            return []
    
    def sync_posts_to_db(self, user_db_id, instagram_user_id):
        """Sync Instagram posts to database"""
        posts_data = self.fetch_user_media(instagram_user_id)
        
        synced_count = 0
        for post_data in posts_data:
            # Check if post already exists
            existing_post = Post.query.filter_by(
                user_id=user_db_id,
                platform='instagram',
                platform_post_id=post_data['platform_post_id']
            ).first()
            
            if not existing_post:
                post = Post(
                    user_id=user_db_id,
                    platform='instagram',
                    platform_post_id=post_data['platform_post_id'],
                    content=post_data['content'],
                    posted_at=post_data['posted_at'],
                    likes=post_data['likes'],
                    shares=post_data['shares'],
                    comments=post_data['comments'],
                    impressions=post_data['impressions'],
                    is_synced=True,
                    synced_at=datetime.utcnow()
                )
                post.performance_score = post.calculate_performance_score()
                db.session.add(post)
                synced_count += 1
        
        db.session.commit()
        return synced_count


def get_social_integration(platform, credentials):
    """Factory function to get the appropriate social media integration"""
    if platform == 'youtube':
        return YouTubeIntegration(
            api_key=credentials.get('api_key')
        )
    elif platform == 'instagram':
        return InstagramIntegration(
            app_id=credentials.get('app_id'),
            app_secret=credentials.get('app_secret'),
            access_token=credentials.get('access_token')
        )
    else:
        raise ValueError(f"Unsupported platform: {platform}")
