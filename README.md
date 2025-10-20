# AI Learning Platform

An intelligent learning platform powered by AI that helps you learn more effectively using proven principles from "Make It Stick: The Science of Successful Learning".

## Features

### Core Learning Principles (Make It Stick)

1. **Spaced Repetition**: Questions are automatically scheduled at optimal intervals using the SM-2 algorithm
2. **Retrieval Practice**: Active testing strengthens memory more than passive review
3. **Interleaving**: Mix questions from different topics to improve learning
4. **Elaboration**: Connect new knowledge to existing understanding
5. **Generation**: Produce answers before seeing them to enhance retention
6. **Desirable Difficulty**: Adaptive difficulty keeps you in the optimal learning zone

### AI-Powered Features

- **Personalized Question Generation**: AI creates custom questions based on your topics using Claude
- **Adaptive Learning**: System learns your preferences and adjusts difficulty
- **Performance Analytics**: Track accuracy, streaks, and progress over time
- **Smart Scheduling**: Questions appear when you're most likely to forget them

### Technical Features

- RESTful API built with FastAPI
- SQLite database (easy to backup and portable)
- Modern, responsive web interface
- Spaced repetition using SM-2 algorithm
- Session-based learning with progress tracking

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) Anthropic API key for AI-powered question generation

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd bdkinas
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key (optional but recommended)
   ```

4. **Initialize the database**
   ```bash
   # The database will be created automatically on first run
   # It will be stored in data/learning_platform.db
   ```

5. **Start the backend server**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the frontend**
   Open `frontend/index.html` in your web browser, or serve it with:
   ```bash
   cd ../frontend
   python -m http.server 3000
   # Then visit http://localhost:3000
   ```

## Quick Start Guide

### 1. Create Your First Topic

1. Go to the "Topics" tab
2. Enter a topic name (e.g., "Python Programming")
3. Add a description of what you want to learn
4. Click "Create Topic"

### 2. Generate Questions

1. Click "Generate AI Questions" on your topic
2. Choose number of questions (5-10 recommended)
3. Select difficulty level (easy/medium/hard)
4. Wait for AI to generate personalized questions

**Note**: AI question generation requires an Anthropic API key. You can:
- Get a key from https://console.anthropic.com/
- Or manually create questions by modifying the database

### 3. Start Learning

1. Go to the "Review" tab
2. Select session type:
   - **Mixed**: Combines new questions and review (recommended)
   - **Daily Review**: Only due questions
   - **New Material**: Only unreviewed questions
3. Click "Start Session"
4. Answer questions and rate your confidence
5. Review your session summary

### 4. Build a Learning Habit

- The system tracks your daily streak
- Questions are automatically scheduled for optimal retention
- Review daily for best results (even just 10-15 minutes)
- The AI learns your preferences over time

## API Documentation

Once the backend is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

### Key Endpoints

- `POST /topics/` - Create a new topic
- `GET /topics/` - List all topics
- `POST /topics/{id}/generate-questions` - Generate AI questions
- `POST /reviews/start-session` - Start a learning session
- `GET /reviews/next-questions/{session_id}` - Get questions for review
- `POST /reviews/submit-answer` - Submit an answer
- `GET /reviews/stats` - Get learning statistics

## Project Structure

```
bdkinas/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration and database
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic (AI, spaced repetition)
│   │   └── main.py        # FastAPI application
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html         # Main page
│   ├── styles.css         # Styling
│   └── app.js            # Frontend logic
├── data/                  # Database files (created automatically)
└── README.md
```

## The Science: Make It Stick Principles

This platform implements research-backed learning strategies:

### 1. Spaced Repetition
- Review intervals increase with each successful recall
- Uses the SM-2 algorithm (same as Anki)
- Optimizes long-term retention

### 2. Retrieval Practice
- Active recall strengthens memory traces
- Testing effect: taking tests improves learning more than re-reading
- Self-assessment builds metacognition

### 3. Interleaving
- Mix different topics in a single session
- Creates desirable difficulty
- Improves discrimination and transfer

### 4. Elaboration
- Connect new information to existing knowledge
- AI generates "why" and "how" questions
- Deepens understanding

### 5. Generation
- Try to answer before seeing the solution
- Produces stronger memory encoding
- Even wrong answers help learning

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed: `python --version`
- Activate virtual environment: `source venv/bin/activate`
- Check all dependencies: `pip install -r requirements.txt`

### Frontend can't connect to API
- Ensure backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Verify API_BASE in `frontend/app.js` matches your backend URL

### AI questions not generating
- Add ANTHROPIC_API_KEY to `backend/.env`
- Get API key from https://console.anthropic.com/
- Check API quota and billing
- Fallback questions will be created if AI is unavailable

### Database issues
- Delete `data/learning_platform.db` to reset
- Backup database before resetting: `cp data/learning_platform.db data/backup.db`

## Future Enhancements

Potential features to add:
- Mobile app (React Native)
- Collaborative learning (share topics)
- Import from Anki/Quizlet
- Voice input for answers
- Gamification (achievements, levels)
- Export learning analytics
- Offline mode
- Browser extension
- Study reminders

## References

- **Make It Stick**: Brown, Roediger, McDaniel (2014)
- **SM-2 Algorithm**: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
- **FastAPI**: https://fastapi.tiangolo.com/
- **Anthropic Claude**: https://www.anthropic.com/

## License

This project is for personal use. Feel free to modify and extend as needed.

---

**Happy Learning!** Remember: consistent practice beats cramming every time.
