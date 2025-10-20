from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from ..core.database import get_db
from ..models.models import Topic, User, UserPreference
from ..services.ai_service import AILearningService

router = APIRouter(prefix="/topics", tags=["topics"])
ai_service = AILearningService()


class TopicCreate(BaseModel):
    name: str
    description: str


class TopicResponse(BaseModel):
    id: int
    name: str
    description: str
    mastery_level: float
    total_questions: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=TopicResponse)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    """Create a new learning topic"""
    # For now, using user_id = 1 (single user system)
    user = db.query(User).first()
    if not user:
        # Create default user if doesn't exist
        user = User(username="learner", email="learner@example.com", hashed_password="temp")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create user preferences
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
        db.commit()

    db_topic = Topic(
        user_id=user.id,
        name=topic.name,
        description=topic.description
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


@router.get("/", response_model=List[TopicResponse])
def get_topics(db: Session = Depends(get_db)):
    """Get all topics for the user"""
    topics = db.query(Topic).all()
    return topics


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a specific topic"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.delete("/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Delete a topic and all its questions"""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db.delete(topic)
    db.commit()
    return {"message": "Topic deleted successfully"}


class GenerateQuestionsRequest(BaseModel):
    num_questions: int = 5
    difficulty: str = 'medium'


@router.post("/{topic_id}/generate-questions")
def generate_questions(
    topic_id: int,
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db)
):
    """Generate AI-powered questions for a topic"""
    from ..models.models import Question

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Get user preferences for personalization
    user = db.query(User).filter(User.id == topic.user_id).first()
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()

    user_context = {}
    if prefs:
        user_context = {
            'avg_accuracy': prefs.avg_accuracy,
            'preferences': {
                'question_types': prefs.preferred_question_types,
                'difficulty': prefs.difficulty_preference
            }
        }

    # Generate questions using AI
    generated_questions = ai_service.generate_questions(
        topic_name=topic.name,
        topic_description=topic.description,
        num_questions=request.num_questions,
        difficulty=request.difficulty,
        user_context=user_context
    )

    # Save questions to database
    created_questions = []
    for q_data in generated_questions:
        question = Question(
            topic_id=topic.id,
            question_text=q_data['question_text'],
            answer_text=q_data['answer_text'],
            question_type=q_data['question_type'],
            difficulty=q_data['difficulty'],
            explanation=q_data.get('explanation'),
            options=q_data.get('options'),
            tags=q_data.get('tags', []),
            ai_generated=True
        )
        db.add(question)
        created_questions.append(question)

    # Update topic question count
    topic.total_questions += len(created_questions)

    db.commit()

    return {
        "message": f"Generated {len(created_questions)} questions",
        "questions": [q.id for q in created_questions]
    }
