"""
Hindsight Memory Integration
Uses official Hindsight SDK for persistent memory storage and retrieval
"""

import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    from hindsight import Hindsight
    HINDSIGHT_AVAILABLE = True
except ImportError:
    HINDSIGHT_AVAILABLE = False
    print("Hindsight SDK not installed. Install with: pip install hindsight-sdk")


class HindsightMemory:
    """Hindsight-powered memory system for social media agent"""
    
    def __init__(self, api_key=None):
        """
        Initialize Hindsight memory
        
        Args:
            api_key: Hindsight API key (from Hindsight Cloud or self-hosted)
        """
        self.api_key = api_key or os.getenv('HINDSIGHT_API_KEY')
        self.client = None
        
        if HINDSIGHT_AVAILABLE and self.api_key:
            try:
                self.client = Hindsight(api_key=self.api_key)
                print("Hindsight memory initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Hindsight: {e}")
        else:
            print("Hindsight not available - using fallback memory")
    
    def is_available(self) -> bool:
        """Check if Hindsight is available"""
        return self.client is not None
    
    def store_post(self, user_id: str, content: str, platform: str, performance: Dict) -> bool:
        """
        Store a post memory in Hindsight
        
        Args:
            user_id: User identifier
            content: Post content
            platform: Platform name (youtube, instagram)
            performance: Dict with likes, shares, comments, impressions
        
        Returns:
            Success status
        """
        if not self.is_available():
            return False
        
        try:
            memory_data = {
                'type': 'post',
                'user_id': user_id,
                'content': content,
                'platform': platform,
                'performance': performance,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {
                    'performance_score': self._calculate_score(performance)
                }
            }
            
            # Store in Hindsight with user-specific namespace
            self.client.add(
                namespace=f"user_{user_id}",
                data=memory_data,
                metadata={'type': 'post', 'platform': platform}
            )
            
            return True
        except Exception as e:
            print(f"Error storing post in Hindsight: {e}")
            return False
    
    def store_conversation(self, user_id: str, user_message: str, ai_response: str, context: str = "") -> bool:
        """
        Store a conversation memory in Hindsight
        
        Args:
            user_id: User identifier
            user_message: User's message
            ai_response: AI's response
            context: Conversation context
        
        Returns:
            Success status
        """
        if not self.is_available():
            return False
        
        try:
            memory_data = {
                'type': 'conversation',
                'user_id': user_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'context': context,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.client.add(
                namespace=f"user_{user_id}",
                data=memory_data,
                metadata={'type': 'conversation'}
            )
            
            return True
        except Exception as e:
            print(f"Error storing conversation in Hindsight: {e}")
            return False
    
    def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10) -> Dict:
        """
        Retrieve relevant memories using Hindsight's semantic search
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of memories to retrieve
        
        Returns:
            Dictionary with top_posts, conversations, and insights
        """
        if not self.is_available():
            return {'top_posts': [], 'conversations': [], 'insights': [], 'error': 'Hindsight not available'}
        
        try:
            # Search for relevant memories
            results = self.client.search(
                namespace=f"user_{user_id}",
                query=query,
                limit=limit
            )
            
            # Organize results by type
            memories = {
                'top_posts': [],
                'conversations': [],
                'insights': []
            }
            
            for result in results:
                memory_type = result.get('metadata', {}).get('type', 'unknown')
                
                if memory_type == 'post':
                    memories['top_posts'].append({
                        'content': result.get('content'),
                        'score': result.get('metadata', {}).get('performance_score', 0),
                        'platform': result.get('platform')
                    })
                elif memory_type == 'conversation':
                    memories['conversations'].append({
                        'user_message': result.get('user_message'),
                        'ai_response': result.get('ai_response')
                    })
            
            # Sort posts by performance score
            memories['top_posts'].sort(key=lambda x: x['score'], reverse=True)
            
            return memories
        
        except Exception as e:
            print(f"Error retrieving memories from Hindsight: {e}")
            return {'top_posts': [], 'conversations': [], 'insights': [], 'error': str(e)}
    
    def get_all_posts(self, user_id: str) -> List[Dict]:
        """
        Get all posts for a user from Hindsight
        
        Args:
            user_id: User identifier
        
        Returns:
            List of post memories
        """
        if not self.is_available():
            return []
        
        try:
            results = self.client.search(
                namespace=f"user_{user_id}",
                query="post",
                limit=100
            )
            
            posts = []
            for result in results:
                if result.get('metadata', {}).get('type') == 'post':
                    posts.append({
                        'content': result.get('content'),
                        'platform': result.get('platform'),
                        'performance': result.get('performance', {}),
                        'score': result.get('metadata', {}).get('performance_score', 0),
                        'timestamp': result.get('timestamp')
                    })
            
            return posts
        
        except Exception as e:
            print(f"Error getting posts from Hindsight: {e}")
            return []
    
    def _calculate_score(self, performance: Dict) -> float:
        """Calculate performance score from metrics"""
        likes = performance.get('likes', 0)
        shares = performance.get('shares', 0)
        comments = performance.get('comments', 0)
        impressions = performance.get('impressions', 1)
        
        return (likes * 1.0 + shares * 2.0 + comments * 1.5) / max(1, impressions / 100)
