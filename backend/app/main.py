from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .routers import topics, reviews

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Learning Platform",
    description="An AI-powered learning platform based on Make It Stick principles",
    version="1.0.0"
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


@app.get("/")
def root():
    return {
        "message": "Welcome to the AI Learning Platform",
        "docs": "/docs",
        "principles": [
            "Spaced Repetition - Review at optimal intervals",
            "Retrieval Practice - Testing enhances learning",
            "Interleaving - Mix different topics",
            "Elaboration - Connect to existing knowledge",
            "Generation - Produce answers, not just recognize them"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
