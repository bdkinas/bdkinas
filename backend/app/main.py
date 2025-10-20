from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .routers import topics, reviews, tutoring

# Import models to ensure they're registered with SQLAlchemy
from .models import models
from .models import tutoring_models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Learning Platform",
    description="An AI-powered learning platform with Socratic tutoring and personalized learning paths",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router)
app.include_router(reviews.router)
app.include_router(tutoring.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to the AI Learning Platform v2.0",
        "tagline": "Your Personal AI Learning Coach",
        "docs": "/docs",
        "features": {
            "quiz_mode": "Spaced repetition quizzes with adaptive difficulty",
            "tutor_mode": "Socratic AI tutor for deep understanding",
            "learning_paths": "Personalized curriculum based on your progress",
            "depth_assessment": "Bloom's Taxonomy-based understanding tracking",
            "metacognition": "Reflection and learning-to-learn skills"
        },
        "principles": [
            "Spaced Repetition - Review at optimal intervals",
            "Retrieval Practice - Testing enhances learning",
            "Interleaving - Mix different topics",
            "Elaboration - Connect to existing knowledge",
            "Generation - Produce answers, not just recognize them",
            "Socratic Dialogue - Learn through questioning",
            "Metacognition - Think about your thinking"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
