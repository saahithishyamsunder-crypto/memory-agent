# Social Media Memory Agent

A production-ready AI assistant that learns from your social media posts, their performance, and conversations to provide smarter recommendations using **Hindsight Memory**.

## 🎯 The Hindsight Concept (Hackathon Requirement)

This project uses **official Hindsight Memory technology** as required by the hackathon. The AI doesn't start from zero every time. It:
1. **Stores memories** in Hindsight (persistent vector database)
2. **Analyzes patterns** from historical data using semantic search
3. **Uses insights** to inform future recommendations
4. **Continuously learns** with each new post

**Hindsight is CENTRAL to this project** - it's not just a feature, it's the core memory layer that powers the entire agent.

## 🚀 Features

- **User Authentication** - Secure registration and login
- **YouTube & Instagram Support** - Sync videos and posts from YouTube and Instagram
- **Real Data Sync** - Fetch posts and analytics from social media APIs
- **Pattern Recognition** - Automatically learns what content performs best
- **Smart Recommendations** - Data-driven suggestions based on your history
- **Confidence Scoring** - More evidence = higher confidence
- **Production Ready** - Docker, PostgreSQL, cloud deployment ready

## 🛠️ Tech Stack

- **Python 3.11+** - Backend
- **Flask** - Web framework
- **Hindsight Memory** - Official vector database for persistent memory (REQUIRED)
- **Groq** - LLM (Llama 3) for recommendations
- **PostgreSQL** - Production database (SQLite for dev)
- **SQLAlchemy** - ORM
- **Flask-Login** - Authentication
- **YouTube Data API** - YouTube integration
- **Instagram Graph API** - Instagram integration
- **Docker** - Containerization
- **Render/Heroku** - Cloud deployment ready

## 📦 Installation

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd windsurf-project
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Run the application**
```bash
python app.py
```

5. **Open browser**
Navigate to `http://localhost:5000`

### Docker Deployment

1. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

2. **Access the application**
Navigate to `http://localhost:5000`

## 🌐 Cloud Deployment

### Deploy to Render

1. **Push code to GitHub**
2. **Create a new Render account**
3. **Connect your GitHub repository**
4. **Render will automatically detect `render.yaml`**
5. **Set environment variables in Render dashboard:**
   - `DATABASE_URL` (auto-generated)
   - `SECRET_KEY` (auto-generated)
   - `HINDSIGHT_API_KEY` (REQUIRED for hackathon)
   - `GROQ_API_KEY` (optional)
   - `YOUTUBE_API_KEY` (optional)
   - `INSTAGRAM_APP_ID` (optional)
   - `INSTAGRAM_APP_SECRET` (optional)
   - `INSTAGRAM_ACCESS_TOKEN` (optional)

6. **Deploy** - Your app will be live at `https://your-app.onrender.com`

### Deploy to Railway/Vercel/Heroku

Similar process - use the provided `Dockerfile` and set environment variables in your platform's dashboard.

## 🔑 Hindsight Memory Configuration (REQUIRED for Hackathon)

This project REQUIRES Hindsight Memory for the hackathon. Get your API key:

1. Go to [Hindsight Cloud](https://ui.hindsight.vectorize.io/)
2. Sign up for an account
3. Get your API key from the dashboard
4. Use promo code **MEMHACK99** for $50 in free credits
5. Add to `.env` file:
```
HINDSIGHT_API_KEY=your-hindsight-api-key
```

### How Hindsight is Used in This Project

**Memory Storage:**
- Every post is stored in Hindsight with metadata (platform, performance metrics)
- Conversations are stored for context
- Uses user-specific namespaces for multi-tenant support

**Memory Retrieval:**
- Semantic search retrieves relevant memories based on user queries
- Returns top-performing posts and patterns
- Central to the recommendation engine

**Memory Visibility:**
- UI shows which memory system is active (Hindsight vs fallback)
- Displays retrieved memories in recommendations
- Makes memory central to the user experience

## 🔑 API Configuration

### YouTube API (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create API credentials (API Key)
5. Add to `.env` file:
```
YOUTUBE_API_KEY=your_youtube_api_key
```

### Instagram Graph API (Optional)

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Instagram Graph API product
4. Get your App ID and App Secret
5. Generate an access token using the Instagram Basic Display API
6. Add to `.env` file:
```
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
```

## 💡 How It Works

### Memory Storage
- Posts are stored with content, platform, and performance metrics
- User data is isolated per account
- Performance is calculated as a weighted score

### Pattern Learning
The AI automatically extracts patterns:
- **Post length**: Short vs long posts performance
- **Questions**: Do questions increase engagement?
- **Hashtags**: Impact of hashtag usage
- **Platform**: Which platform performs best

### Hindsight Recommendations
When you ask for a recommendation, the AI:
1. Retrieves your top-performing posts
2. Loads learned patterns from the database
3. Generates suggestions based on what worked before
4. Provides a confidence score based on evidence

## 🎮 Usage

1. **Register** - Create an account
2. **Add Posts** - Manually enter posts or sync from social media
3. **Analyze Patterns** - Click "Analyze Patterns" to extract insights
4. **Get Recommendations** - Ask what to post, receive AI suggestions
5. **Continuous Learning** - Each new post improves future recommendations

## � Security

- Passwords are hashed using Werkzeug security
- User data is isolated per account
- API tokens should be stored securely in environment variables
- In production, use HTTPS and secure headers

## 📊 Database Schema

- **users** - User accounts and authentication
- **social_accounts** - Connected social media accounts
- **posts** - Social media posts with performance data
- **conversations** - User conversations with AI
- **insights** - Learned patterns and success rates

## 🎯 Production Checklist

Before deploying to production:

- [ ] **Configure Hindsight API Key** (REQUIRED for hackathon)
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure Groq API key for LLM recommendations
- [ ] Configure YouTube/Instagram API credentials (optional)
- [ ] Enable HTTPS
- [ ] Set up proper logging
- [ ] Configure rate limiting
- [ ] Add monitoring (e.g., Sentry, LogRocket)
- [ ] Set up backups for database
- [ ] Review and update CORS settings if needed

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use this project for your own purposes.

## 🆘 Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review the code comments

## 🎉 Acknowledgments

Built for hackathon demonstration of the hindsight concept in AI systems.
