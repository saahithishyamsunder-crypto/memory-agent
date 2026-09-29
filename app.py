from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Post, Conversation, Insight
from auth import auth_bp
from social_integrations import YouTubeIntegration, InstagramIntegration, get_social_integration
from llm_engine import LLMEngine
from hindsight_memory import HindsightMemory

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///social_media_memory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize Hindsight Memory (REQUIRED for hackathon)
hindsight_memory = HindsightMemory()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# Main routes
@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

# API Routes
@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    """Get user's posts"""
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.posted_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'content': p.content,
        'platform': p.platform,
        'posted_at': p.posted_at.isoformat(),
        'likes': p.likes,
        'shares': p.shares,
        'comments': p.comments,
        'impressions': p.impressions,
        'score': p.performance_score
    } for p in posts])

@app.route('/api/posts', methods=['POST'])
@login_required
def add_post():
    """Add a new post manually"""
    data = request.json
    
    # Store in database
    post = Post(
        user_id=current_user.id,
        platform=data['platform'],
        content=data['content'],
        posted_at=data.get('posted_at'),
        likes=data.get('likes', 0),
        shares=data.get('shares', 0),
        comments=data.get('comments', 0),
        impressions=data.get('impressions', 0)
    )
    post.performance_score = post.calculate_performance_score()
    db.session.add(post)
    db.session.commit()
    
    # Store in Hindsight Memory (REQUIRED for hackathon)
    hindsight_memory.store_post(
        user_id=str(current_user.id),
        content=data['content'],
        platform=data['platform'],
        performance={
            'likes': data.get('likes', 0),
            'shares': data.get('shares', 0),
            'comments': data.get('comments', 0),
            'impressions': data.get('impressions', 0)
        }
    )
    
    return jsonify({
        'success': True, 
        'post_id': post.id,
        'hindsight_stored': hindsight_memory.is_available()
    })

@app.route('/api/sync/<platform>', methods=['POST'])
@login_required
def sync_platform(platform):
    """Sync posts from social media platform"""
    if platform not in ['youtube', 'instagram']:
        return jsonify({
            'success': False,
            'message': f'Unsupported platform: {platform}. Only YouTube and Instagram are supported.'
        })
    
    try:
        if platform == 'youtube':
            api_key = os.getenv('YOUTUBE_API_KEY')
            if not api_key:
                return jsonify({
                    'success': False,
                    'message': 'YouTube API key not configured. Add YOUTUBE_API_KEY to your .env file.'
                })
            
            # For demo, we'll need the user to provide their channel ID
            # In production, this would be stored in the social_accounts table
            channel_id = request.json.get('channel_id') if request.json else None
            if not channel_id:
                return jsonify({
                    'success': False,
                    'message': 'Please provide your YouTube channel ID to sync.'
                })
            
            youtube = YouTubeIntegration(api_key=api_key)
            synced_count = youtube.sync_videos_to_db(current_user.id, channel_id)
            
            return jsonify({
                'success': True,
                'message': f'Successfully synced {synced_count} YouTube videos',
                'synced_count': synced_count
            })
        
        elif platform == 'instagram':
            app_id = os.getenv('INSTAGRAM_APP_ID')
            app_secret = os.getenv('INSTAGRAM_APP_SECRET')
            access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
            
            if not all([app_id, app_secret, access_token]):
                return jsonify({
                    'success': False,
                    'message': 'Instagram API credentials not configured. Add INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, and INSTAGRAM_ACCESS_TOKEN to your .env file.'
                })
            
            # For demo, we'll need the user to provide their Instagram user ID
            instagram_user_id = request.json.get('instagram_user_id') if request.json else None
            if not instagram_user_id:
                return jsonify({
                    'success': False,
                    'message': 'Please provide your Instagram user ID to sync.'
                })
            
            instagram = InstagramIntegration(app_id, app_secret, access_token)
            synced_count = instagram.sync_posts_to_db(current_user.id, instagram_user_id)
            
            return jsonify({
                'success': True,
                'message': f'Successfully synced {synced_count} Instagram posts',
                'synced_count': synced_count
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error syncing {platform}: {str(e)}'
        })

@app.route('/api/recommend', methods=['POST'])
@login_required
def get_recommendation():
    """Get AI recommendation based on Hindsight memory"""
    data = request.json
    query = data.get('query', 'What should I post?')
    
    # Step 1: Hindsight retrieves relevant memories (CENTRAL TO HACKATHON)
    if hindsight_memory.is_available():
        # Use official Hindsight memory with semantic search
        memories = hindsight_memory.retrieve_relevant_memories(
            user_id=str(current_user.id),
            query=query,
            limit=10
        )
        
        # Add insights from database
        insights = Insight.query.filter_by(user_id=current_user.id)\
            .order_by(Insight.success_rate.desc())\
            .all()
        memories['insights'] = [{'pattern': i.pattern, 'success_rate': i.success_rate} for i in insights]
        
        memory_source = 'Hindsight Memory (Official)'
    else:
        # Fallback to database if Hindsight not available
        top_posts = Post.query.filter_by(user_id=current_user.id)\
            .order_by(Post.performance_score.desc())\
            .limit(5).all()
        
        insights = Insight.query.filter_by(user_id=current_user.id)\
            .order_by(Insight.success_rate.desc())\
            .all()
        
        conversations = Conversation.query.filter_by(user_id=current_user.id)\
            .order_by(Conversation.created_at.desc())\
            .limit(5).all()
        
        memories = {
            'top_posts': [{'content': p.content, 'score': p.performance_score} for p in top_posts],
            'insights': [{'pattern': i.pattern, 'success_rate': i.success_rate} for i in insights],
            'conversations': [c.user_message for c in conversations]
        }
        
        memory_source = 'Database (Hindsight not configured)'
    
    # Step 2: LLM generates recommendation using hindsight context
    llm_engine = LLMEngine()
    suggestion = llm_engine.generate_recommendation(query, memories)
    
    # Calculate confidence based on evidence
    confidence = 0.0
    if memories.get('top_posts'):
        confidence = min(0.95, len(memories['top_posts']) / 20.0)
    if memories.get('insights'):
        confidence = max(confidence, max([i['success_rate'] for i in memories['insights']]) if memories['insights'] else 0)
    
    return jsonify({
        'query': query,
        'suggestion': suggestion,
        'confidence': round(confidence, 2),
        'retrieved_memories': memories,  # Show what Hindsight retrieved
        'memory_count': len(memories.get('top_posts', [])) + len(memories.get('insights', [])),
        'llm_available': llm_engine.is_available(),
        'hindsight_available': hindsight_memory.is_available(),
        'memory_source': memory_source  # Show which memory system is being used
    })

@app.route('/api/insights', methods=['GET'])
@login_required
def get_insights():
    """Get user's learned insights"""
    insights = Insight.query.filter_by(user_id=current_user.id)\
        .order_by(Insight.success_rate.desc()).all()
    return jsonify([{
        'id': i.id,
        'pattern': i.pattern,
        'description': i.description,
        'success_rate': i.success_rate,
        'evidence_count': i.evidence_count,
        'last_updated': i.last_updated.isoformat()
    } for i in insights])

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze_patterns():
    """Trigger pattern analysis on user's posts"""
    posts = Post.query.filter_by(user_id=current_user.id).all()
    
    if not posts:
        return jsonify({'patterns': [], 'message': 'No posts to analyze'})
    
    patterns = []
    
    # Analyze post length
    short_posts = [p for p in posts if len(p.content) < 100]
    long_posts = [p for p in posts if len(p.content) >= 100]
    
    if short_posts:
        avg_score = sum(p.performance_score for p in short_posts) / len(short_posts)
        patterns.append({
            'pattern': 'short_posts',
            'description': 'Posts under 100 characters',
            'success_rate': avg_score,
            'evidence': len(short_posts)
        })
    
    if long_posts:
        avg_score = sum(p.performance_score for p in long_posts) / len(long_posts)
        patterns.append({
            'pattern': 'long_posts',
            'description': 'Posts 100+ characters',
            'success_rate': avg_score,
            'evidence': len(long_posts)
        })
    
    # Store insights
    for pattern in patterns:
        existing = Insight.query.filter_by(
            user_id=current_user.id,
            pattern=pattern['pattern']
        ).first()
        
        if existing:
            existing.success_rate = pattern['success_rate']
            existing.evidence_count = pattern['evidence']
        else:
            insight = Insight(
                user_id=current_user.id,
                pattern=pattern['pattern'],
                description=pattern['description'],
                success_rate=pattern['success_rate'],
                evidence_count=pattern['evidence']
            )
            db.session.add(insight)
    
    db.session.commit()
    return jsonify({'patterns': patterns})

@app.route('/api/demo-data', methods=['POST'])
@login_required
def load_demo_data():
    """Load demo data for hackathon demonstration"""
    # Clear existing demo data for this user
    Post.query.filter_by(user_id=current_user.id).delete()
    Insight.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    # Sample posts with varying performance for demo
    sample_posts = [
        {"content": "Just launched our new YouTube tutorial! #tutorial", "platform": "youtube", "likes": 150, "shares": 45, "comments": 20, "impressions": 1000},
        {"content": "What's your biggest challenge with video editing?", "platform": "youtube", "likes": 89, "shares": 12, "comments": 67, "impressions": 800},
        {"content": "Behind the scenes of our latest video shoot", "platform": "youtube", "likes": 230, "shares": 30, "comments": 45, "impressions": 1500},
        {"content": "Quick tip: Always use good lighting", "platform": "youtube", "likes": 45, "shares": 8, "comments": 5, "impressions": 300},
        {"content": "We're launching a new course! Check it out", "platform": "youtube", "likes": 120, "shares": 25, "comments": 15, "impressions": 900},
        {"content": "Beautiful sunset photo from our trip", "platform": "instagram", "likes": 180, "shares": 22, "comments": 38, "impressions": 1200},
        {"content": "Question: What content do you want to see next?", "platform": "youtube", "likes": 95, "shares": 18, "comments": 52, "impressions": 700},
    ]
    
    for post_data in sample_posts:
        post = Post(
            user_id=current_user.id,
            platform=post_data['platform'],
            content=post_data['content'],
            likes=post_data['likes'],
            shares=post_data['shares'],
            comments=post_data['comments'],
            impressions=post_data['impressions']
        )
        post.performance_score = post.calculate_performance_score()
        db.session.add(post)
        
        # Store in Hindsight Memory
        hindsight_memory.store_post(
            user_id=str(current_user.id),
            content=post_data['content'],
            platform=post_data['platform'],
            performance={
                'likes': post_data['likes'],
                'shares': post_data['shares'],
                'comments': post_data['comments'],
                'impressions': post_data['impressions']
            }
        )
    
    # Sample conversations
    sample_conversations = [
        {"user_message": "What should I post about today?", "ai_response": "Based on your past performance, question posts get high engagement", "context": "content_planning"},
        {"user_message": "How can I increase engagement?", "ai_response": "Your behind-the-scenes content tends to get more likes", "context": "engagement"},
    ]
    
    for conv_data in sample_conversations:
        conv = Conversation(
            user_id=current_user.id,
            user_message=conv_data['user_message'],
            ai_response=conv_data['ai_response'],
            context=conv_data['context']
        )
        db.session.add(conv)
        
        # Store in Hindsight Memory
        hindsight_memory.store_conversation(
            user_id=str(current_user.id),
            user_message=conv_data['user_message'],
            ai_response=conv_data['ai_response'],
            context=conv_data['context']
        )
    
    db.session.commit()
    
    # Analyze patterns
    patterns_response = analyze_patterns()
    patterns_data = patterns_response.get_json()
    
    return jsonify({
        'success': True,
        'posts_added': len(sample_posts),
        'conversations_added': len(sample_conversations),
        'patterns_found': len(patterns_data.get('patterns', [])),
        'message': 'Demo data loaded! Now you can demonstrate the hindsight flow.'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
