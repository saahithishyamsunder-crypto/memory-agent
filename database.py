import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "social_media_memory.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize database tables for storing posts, performance, and conversations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Posts table - stores social media posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                platform TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                performance_likes INTEGER DEFAULT 0,
                performance_shares INTEGER DEFAULT 0,
                performance_comments INTEGER DEFAULT 0,
                performance_score REAL DEFAULT 0.0
            )
        """)
        
        # Conversations table - stores user interactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insights table - stores learned patterns from hindsight
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                evidence_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_post(self, content: str, platform: str, likes: int = 0, shares: int = 0, comments: int = 0) -> int:
        """Add a new social media post"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calculate performance score (simple weighted average)
        performance_score = (likes * 1.0 + shares * 2.0 + comments * 1.5) / 10.0
        
        cursor.execute("""
            INSERT INTO posts (content, platform, performance_likes, performance_shares, performance_comments, performance_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (content, platform, likes, shares, comments, performance_score))
        
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return post_id
    
    def add_conversation(self, user_message: str, ai_response: str, context: str = "") -> int:
        """Add a conversation entry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (user_message, ai_response, context)
            VALUES (?, ?, ?)
        """, (user_message, ai_response, context))
        
        conv_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conv_id
    
    def get_all_posts(self) -> List[Dict]:
        """Retrieve all posts with their performance data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, platform, posted_at, performance_likes, performance_shares, performance_comments, performance_score
            FROM posts ORDER BY posted_at DESC
        """)
        
        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row[0],
                'content': row[1],
                'platform': row[2],
                'posted_at': row[3],
                'likes': row[4],
                'shares': row[5],
                'comments': row[6],
                'score': row[7]
            })
        
        conn.close()
        return posts
    
    def get_top_performing_posts(self, limit: int = 5) -> List[Dict]:
        """Get top performing posts based on performance score"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, platform, performance_score
            FROM posts ORDER BY performance_score DESC LIMIT ?
        """, (limit,))
        
        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row[0],
                'content': row[1],
                'platform': row[2],
                'score': row[3]
            })
        
        conn.close()
        return posts
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_message, ai_response, context, timestamp
            FROM conversations ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row[0],
                'user_message': row[1],
                'ai_response': row[2],
                'context': row[3],
                'timestamp': row[4]
            })
        
        conn.close()
        return conversations
    
    def add_insight(self, pattern: str, success_rate: float, evidence_count: int) -> int:
        """Add or update an insight pattern"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if pattern exists
        cursor.execute("SELECT id FROM insights WHERE pattern = ?", (pattern,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing insight
            cursor.execute("""
                UPDATE insights 
                SET success_rate = ?, evidence_count = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (success_rate, evidence_count, existing[0]))
            insight_id = existing[0]
        else:
            # Add new insight
            cursor.execute("""
                INSERT INTO insights (pattern, success_rate, evidence_count)
                VALUES (?, ?, ?)
            """, (pattern, success_rate, evidence_count))
            insight_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return insight_id
    
    def get_insights(self) -> List[Dict]:
        """Get all learned insights"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, pattern, success_rate, evidence_count, last_updated
            FROM insights ORDER BY success_rate DESC
        """)
        
        insights = []
        for row in cursor.fetchall():
            insights.append({
                'id': row[0],
                'pattern': row[1],
                'success_rate': row[2],
                'evidence_count': row[3],
                'last_updated': row[4]
            })
        
        conn.close()
        return insights
