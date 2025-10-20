# Quick Start Guide

Get up and running in 5 minutes!

## Installation (First Time)

```bash
# 1. Navigate to project directory
cd /home/user/bdkinas

# 2. Make the startup script executable
chmod +x start.sh

# 3. Run the startup script (it will create venv and install dependencies)
./start.sh
```

## Configuration (Optional but Recommended)

To enable AI-powered question generation:

1. Get an Anthropic API key from https://console.anthropic.com/
2. Edit `backend/.env`:
   ```bash
   nano backend/.env
   ```
3. Add your API key:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```
4. Save and restart the server

## Daily Usage

### Starting the Server

```bash
./start.sh
```

The backend will start on http://localhost:8000

### Accessing the Frontend

**Option 1**: Open directly in browser
```bash
# Just open the file
xdg-open frontend/index.html  # Linux
open frontend/index.html      # Mac
```

**Option 2**: Serve with Python (recommended for full functionality)
```bash
cd frontend
python -m http.server 3000
# Then visit http://localhost:3000
```

## Your First Learning Session

1. **Create a Topic**
   - Click "Topics" tab
   - Enter: "Python Basics"
   - Description: "Learn Python fundamentals"
   - Click "Create Topic"

2. **Generate Questions** (requires API key)
   - Click "Generate AI Questions"
   - Enter: 5 questions, medium difficulty
   - Wait for generation

3. **Start Learning**
   - Click "Review" tab
   - Click "Start Session"
   - Answer questions
   - Rate your confidence (1-5)

4. **Come Back Tomorrow**
   - Questions will be scheduled based on spaced repetition
   - Review daily for best results!

## Tips for Effective Learning

- **Daily Practice**: Even 10-15 minutes daily beats long cramming sessions
- **Mixed Sessions**: Use "Mixed" session type to benefit from interleaving
- **Honest Confidence**: Rate your confidence honestly for optimal scheduling
- **Multiple Topics**: Create topics in different subjects to enhance interleaving
- **Review Regularly**: The system works best with consistent daily review

## Troubleshooting

**Backend won't start?**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Can't generate questions?**
- Check if ANTHROPIC_API_KEY is set in backend/.env
- Verify API key is valid at https://console.anthropic.com/
- Check you have API credits

**Frontend can't connect?**
- Make sure backend is running on port 8000
- Try serving frontend with python: `python -m http.server 3000`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API docs at http://localhost:8000/docs
- Customize user preferences in the database
- Add more topics and build your learning habit!

---

**Remember**: The best learning happens through consistent practice, not cramming!
