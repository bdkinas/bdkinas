# AI Learning Platform v2.0

**Your Personal AI Learning Coach** - Transform how you learn with Socratic dialogue, personalized teaching, and deep understanding assessment.

An intelligent learning platform that goes beyond quizzes to truly teach you through conversation, assess your depth of understanding using Bloom's Taxonomy, and guide you on a personalized learning journey.

## 🚀 Revolutionary Features

### **Two Modes of Learning**

#### **1. Quiz Mode** - Traditional spaced repetition with adaptive difficulty
- AI-generated quizzes based on your topics
- SM-2 algorithm for optimal review scheduling
- Performance tracking and analytics
- Interleaved practice across topics

#### **2. Tutor Mode** - Socratic AI teaching and coaching (NEW!)
- **Interactive Dialogue**: Learn through conversation with an AI tutor
- **Depth Assessment**: Bloom's Taxonomy-based understanding evaluation (Remember → Understand → Apply → Analyze → Evaluate → Create)
- **Personalized Teaching**: AI adapts explanations to your knowledge gaps
- **Learning Paths**: Structured curriculum with prerequisite management
- **Metacognition Training**: Develop self-awareness about your learning
- **Multiple Teaching Styles**: Exploration, depth checking, direct teaching, practice, and reflection

## 🎯 Core Learning Principles

Based on "Make It Stick: The Science of Successful Learning":

1. **Spaced Repetition**: Questions are automatically scheduled at optimal intervals using the SM-2 algorithm
2. **Retrieval Practice**: Active testing strengthens memory more than passive review
3. **Interleaving**: Mix questions from different topics to improve learning
4. **Elaboration**: Connect new knowledge to existing understanding
5. **Generation**: Produce answers before seeing them to enhance retention
6. **Desirable Difficulty**: Adaptive difficulty keeps you in the optimal learning zone
7. **Socratic Questioning**: Learn through dialogue and inquiry (NEW!)
8. **Metacognition**: Think about your thinking and develop learning strategies (NEW!)

## 🤖 AI-Powered Intelligence

### Quiz Generation
- **Personalized Questions**: AI creates custom questions based on your topics
- **Multiple Question Types**: Flashcards, multiple choice, open-ended, elaboration
- **Difficulty Adaptation**: System learns and adjusts to your level
- **Smart Scheduling**: Questions appear when you're most likely to forget

### Socratic Tutoring (NEW!)
- **Conversational Learning**: Real-time dialogue with AI tutor
- **Probing Questions**: "Why?", "How?", "What if?" to deepen understanding
- **Just-in-Time Teaching**: Explanations provided exactly when you need them
- **Gap Analysis**: Identifies specific knowledge gaps and misconceptions
- **Understanding Signals**: Detects confidence, confusion, and comprehension depth

### Learning Paths (NEW!)
- **Concept Dependencies**: Manages prerequisites and learning sequences
- **Personalized Curriculum**: Adapts to your progress and understanding
- **Milestone Tracking**: Celebrates progress through the learning journey
- **Adaptive Pacing**: Speeds up or slows down based on performance

## 🧠 Technical Architecture

- **Backend**: FastAPI with Python
- **Database**: SQLite (easy to backup and portable)
- **AI Engine**: Anthropic Claude for intelligent tutoring
- **Frontend**: Modern, responsive web interface
- **Algorithms**: SM-2 spaced repetition, Bloom's Taxonomy assessment
- **Knowledge Modeling**: Concept graphs with mastery tracking

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

### 3. Start Learning (Quiz Mode)

1. Go to the "Review" tab
2. Select session type:
   - **Mixed**: Combines new questions and review (recommended)
   - **Daily Review**: Only due questions
   - **New Material**: Only unreviewed questions
3. Click "Start Session"
4. Answer questions and rate your confidence
5. Review your session summary

### 4. Try Tutor Mode (NEW!)

Navigate to Tutor Mode for deep, conversational learning:

1. Click "Tutor Mode" in the navigation
2. Choose your learning approach:
   - **🔍 Exploration**: Discover what you already know through Socratic questions
   - **🎯 Depth Check**: Test how deeply you understand (Bloom's Taxonomy)
   - **📚 Teach Me**: Learn through AI-guided explanations and examples
   - **💪 Practice**: Apply concepts in realistic scenarios
   - **🤔 Reflection**: Develop metacognition and learning strategies
   - **🗺️ Learning Path**: Follow a structured curriculum

3. Select a concept to explore
4. Engage in conversation with your AI tutor
5. The AI will:
   - Ask probing questions to assess your understanding
   - Provide personalized teaching based on your gaps
   - Guide you to deeper comprehension
   - Track your progress using Bloom's Taxonomy

**Example Tutor Mode Dialogue:**
```
AI: Let's explore Python functions. What do you think a function is?
You: A reusable block of code?
AI: Good start! Why would we want to make code reusable?
You: To avoid repeating ourselves?
AI: Exactly! Can you think of a real-world example where you'd use a function?
You: Maybe calculating the area of different circles?
AI: Perfect! Now let's explore how we'd write that...
```

### 5. Build a Learning Habit

- **Daily Practice**: Even 10-15 minutes daily beats long cramming sessions
- **Mix Modes**: Use Quiz Mode for retention, Tutor Mode for deep understanding
- **Track Progress**: Watch your knowledge map grow with each session
- **Reflect Regularly**: Use reflection mode to develop metacognitive awareness
- **Follow Learning Paths**: Let the AI guide your structured learning journey

## API Documentation

Once the backend is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

### Key Endpoints

**Quiz Mode:**
- `POST /topics/` - Create a new topic
- `GET /topics/` - List all topics
- `POST /topics/{id}/generate-questions` - Generate AI questions
- `POST /reviews/start-session` - Start a quiz session
- `GET /reviews/next-questions/{session_id}` - Get questions for review
- `POST /reviews/submit-answer` - Submit an answer
- `GET /reviews/stats` - Get learning statistics

**Tutor Mode (NEW!):**
- `POST /tutoring/concepts` - Create a concept
- `GET /tutoring/concepts/topic/{topic_id}` - Get concepts for a topic
- `POST /tutoring/sessions/start` - Start AI tutoring session
- `POST /tutoring/sessions/continue` - Continue Socratic dialogue
- `POST /tutoring/sessions/{id}/end` - End session and assess depth
- `GET /tutoring/mastery/concept/{concept_id}` - Get mastery level
- `POST /tutoring/learning-paths` - Create personalized learning path
- `GET /tutoring/learning-paths/{id}/next-concept` - Get next concept to learn
- `GET /tutoring/insights` - Get AI-generated learning insights

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
