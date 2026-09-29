from typing import List, Dict
import re
import os
import sys

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database

class MemoryAgent:
    """AI Agent that remembers and learns from social media history"""
    
    def __init__(self, db_path: str = "social_media_memory.db"):
        self.db = Database(db_path)
    
    def store_post_memory(self, content: str, platform: str, performance: Dict) -> int:
        """Store a post and its performance in memory"""
        return self.db.add_post(
            content=content,
            platform=platform,
            likes=performance.get('likes', 0),
            shares=performance.get('shares', 0),
            comments=performance.get('comments', 0)
        )
    
    def store_conversation_memory(self, user_message: str, ai_response: str, context: str = "") -> int:
        """Store a conversation in memory"""
        return self.db.add_conversation(user_message, ai_response, context)
    
    def retrieve_relevant_memories(self, query: str) -> Dict:
        """
        Retrieve relevant memories based on query
        This is the core "hindsight" mechanism - looking back at what worked before
        """
        # Get top performing posts
        top_posts = self.db.get_top_performing_posts(limit=5)
        
        # Get recent conversations
        recent_conversations = self.db.get_recent_conversations(limit=10)
        
        # Get learned insights
        insights = self.db.get_insights()
        
        return {
            'top_posts': top_posts,
            'recent_conversations': recent_conversations,
            'insights': insights
        }
    
    def extract_patterns(self) -> List[Dict]:
        """
        Analyze stored posts to extract successful patterns
        This is where the AI learns from hindsight
        """
        posts = self.db.get_all_posts()
        
        if not posts:
            return []
        
        # Simple pattern extraction based on content analysis
        patterns = []
        
        # Pattern 1: Post length analysis
        short_posts = [p for p in posts if len(p['content']) < 100]
        long_posts = [p for p in posts if len(p['content']) >= 100]
        
        if short_posts:
            avg_score = sum(p['score'] for p in short_posts) / len(short_posts)
            patterns.append({
                'pattern': 'short_posts',
                'description': 'Posts under 100 characters',
                'success_rate': avg_score,
                'evidence': len(short_posts)
            })
        
        if long_posts:
            avg_score = sum(p['score'] for p in long_posts) / len(long_posts)
            patterns.append({
                'pattern': 'long_posts',
                'description': 'Posts 100+ characters',
                'success_rate': avg_score,
                'evidence': len(long_posts)
            })
        
        # Pattern 2: Question posts
        question_posts = [p for p in posts if '?' in p['content']]
        if question_posts:
            avg_score = sum(p['score'] for p in question_posts) / len(question_posts)
            patterns.append({
                'pattern': 'question_posts',
                'description': 'Posts containing questions',
                'success_rate': avg_score,
                'evidence': len(question_posts)
            })
        
        # Pattern 3: Hashtag usage
        hashtag_posts = [p for p in posts if '#' in p['content']]
        if hashtag_posts:
            avg_score = sum(p['score'] for p in hashtag_posts) / len(hashtag_posts)
            patterns.append({
                'pattern': 'hashtag_posts',
                'description': 'Posts with hashtags',
                'success_rate': avg_score,
                'evidence': len(hashtag_posts)
            })
        
        # Store insights in database
        for pattern in patterns:
            self.db.add_insight(
                pattern=pattern['pattern'],
                success_rate=pattern['success_rate'],
                evidence_count=pattern['evidence']
            )
        
        return patterns
    
    def generate_recommendation(self, user_query: str) -> Dict:
        """
        Generate a recommendation based on hindsight (memories)
        This is the key feature - using past learnings to inform future decisions
        """
        # Retrieve relevant memories
        memories = self.retrieve_relevant_memories(user_query)
        
        # Extract and update patterns
        patterns = self.extract_patterns()
        
        # Build recommendation based on patterns
        recommendation = {
            'query': user_query,
            'based_on_memories': {
                'top_post_examples': [p['content'] for p in memories['top_posts'][:3]],
                'learned_patterns': patterns,
                'conversation_context': [c['user_message'] for c in memories['recent_conversations'][:3]]
            },
            'suggestion': self._build_suggestion(memories, patterns),
            'confidence': self._calculate_confidence(patterns, memories)
        }
        
        return recommendation
    
    def _build_suggestion(self, memories: Dict, patterns: List[Dict]) -> str:
        """Build a suggestion based on memories and patterns"""
        if not patterns:
            return "Start by posting content and I'll learn what works best for your audience!"
        
        # Find best performing pattern
        best_pattern = max(patterns, key=lambda x: x['success_rate'])
        
        suggestions = []
        
        if best_pattern['pattern'] == 'short_posts':
            suggestions.append("Keep your posts concise and under 100 characters")
        elif best_pattern['pattern'] == 'long_posts':
            suggestions.append("Your audience engages well with detailed, longer posts")
        elif best_pattern['pattern'] == 'question_posts':
            suggestions.append("Ask questions in your posts to boost engagement")
        elif best_pattern['pattern'] == 'hashtag_posts':
            suggestions.append("Use hashtags to increase reach")
        
        # Add context from top posts
        if memories['top_posts']:
            top_post = memories['top_posts'][0]
            suggestions.append(f"\nReference: Your best performing post was '{top_post['content'][:50]}...'")
        
        return "\n".join(suggestions)
    
    def _calculate_confidence(self, patterns: List[Dict], memories: Dict) -> float:
        """Calculate confidence in the recommendation based on evidence"""
        if not patterns:
            return 0.0
        
        total_evidence = sum(p['evidence'] for p in patterns)
        post_count = len(memories['top_posts'])
        
        # More evidence = higher confidence (capped at 0.95)
        confidence = min(0.95, (total_evidence + post_count) / 20.0)
        return round(confidence, 2)
