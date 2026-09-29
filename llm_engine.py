from groq import Groq
import os
from typing import List, Dict

class LLMEngine:
    """LLM engine for generating recommendations using hindsight (powered by Groq)"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        return self.client is not None
    
    def generate_recommendation(self, user_query: str, memories: Dict) -> str:
        """
        Generate a recommendation using LLM with hindsight context
        
        Args:
            user_query: What the user wants to post about
            memories: Dictionary containing top_posts, recent_conversations, and insights
        
        Returns:
            AI-generated recommendation
        """
        if not self.is_available():
            return self._fallback_recommendation(memories)
        
        # Build context from memories
        context = self._build_context(memories)
        
        # Create prompt for LLM
        prompt = f"""
You are a social media strategy AI assistant. You have access to the user's past social media performance data (hindsight).

USER QUERY: {user_query}

HINDSIGHT CONTEXT:
{context}

Based on this hindsight data, provide a specific recommendation for what the user should post next. 
Your recommendation should:
1. Reference specific patterns from their past performance
2. Suggest content similar to their top-performing posts
3. Be actionable and specific
4. Explain WHY you're making this recommendation based on the data

Provide your recommendation in a clear, conversational format. Keep it under 200 words.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",  # Using Llama 3 70B on Groq
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a social media strategy AI that uses hindsight from past performance to make recommendations. Be concise and actionable."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return self._fallback_recommendation(memories)
    
    def _build_context(self, memories: Dict) -> str:
        """Build context string from memories"""
        context_parts = []
        
        # Top performing posts
        if memories.get('top_posts'):
            context_parts.append("TOP PERFORMING POSTS:")
            for i, post in enumerate(memories['top_posts'][:3], 1):
                context_parts.append(f"{i}. '{post['content']}' (Score: {post['score']:.1f})")
        
        # Learned insights
        if memories.get('insights'):
            context_parts.append("\nLEARNED PATTERNS:")
            for insight in memories['insights'][:3]:
                context_parts.append(f"- {insight['pattern']}: {insight['success_rate']:.1%} success rate")
        
        # Recent conversations
        if memories.get('conversation_context'):
            context_parts.append("\nRECENT CONVERSATIONS:")
            for conv in memories['conversation_context'][:2]:
                context_parts.append(f"- User asked: '{conv}'")
        
        return "\n".join(context_parts) if context_parts else "No past data available yet."
    
    def _fallback_recommendation(self, memories: Dict) -> str:
        """Fallback recommendation when LLM is not available"""
        if memories.get('top_posts'):
            best_post = memories['top_posts'][0]
            if memories.get('insights'):
                best_insight = memories['insights'][0]
                return f"Based on your best performing post '{best_post['content'][:50]}...' and the pattern that {best_insight['pattern']} has a {best_insight['success_rate']:.0%} success rate, try creating similar content. Your audience responds well to this type of content."
            else:
                return f"Based on your best performing post '{best_post['content'][:50]}...', try creating similar content. Your audience responds well to this type of content."
        else:
            return "Start by adding some posts so I can learn what works best for your audience!"
