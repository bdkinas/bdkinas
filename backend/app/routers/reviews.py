from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..core.database import get_db
from ..models.models import ReviewSession, CardReview, Question, User, UserPreference, Topic
from ..services.spaced_repetition import SpacedRepetitionService

router = APIRouter(prefix="/reviews", tags=["reviews"])
sr_service = SpacedRepetitionService()


class StartSessionRequest(BaseModel):
    session_type: str = 'mixed'  # 'daily_review', 'new_material', 'mixed'
    max_questions: int = 10


class SessionResponse(BaseModel):
    id: int
    started_at: datetime
    session_type: str
    total_questions: int

    class Config:
        from_attributes = True


class QuestionForReview(BaseModel):
    id: int
    question_text: str
    question_type: str
    difficulty: str
    options: Optional[List[str]] = None
    topic_name: str


class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    user_answer: str
    is_correct: bool
    confidence: int  # 1-5 scale


@router.post("/start-session", response_model=SessionResponse)
def start_review_session(request: StartSessionRequest, db: Session = Depends(get_db)):
    """
    Start a new review session with questions based on spaced repetition
    and Make It Stick principles
    """
    # Get user (single user for now)
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new session
    session = ReviewSession(
        user_id=user.id,
        session_type=request.session_type,
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get("/next-questions/{session_id}", response_model=List[QuestionForReview])
def get_next_questions(
    session_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get next questions for the session using spaced repetition and interleaving
    """
    session = db.query(ReviewSession).filter(ReviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get user preferences
    prefs = db.query(UserPreference).filter(UserPreference.user_id == session.user_id).first()

    # Get all questions
    all_questions = db.query(Question).all()

    # Get due questions (spaced repetition)
    due_questions = sr_service.get_due_questions(all_questions)

    # Get some new questions
    new_questions = sr_service.get_new_questions(all_questions, limit=max(3, limit // 3))

    # Combine due and new questions
    questions_to_review = due_questions[:limit - len(new_questions)] + new_questions

    # Apply interleaving (Make It Stick principle)
    if prefs and prefs.interleaving_ratio > 0:
        questions_to_review = sr_service.interleave_questions(
            questions_to_review,
            prefs.interleaving_ratio
        )

    # Limit to requested number
    questions_to_review = questions_to_review[:limit]

    # Format response
    response = []
    for q in questions_to_review:
        topic = db.query(Topic).filter(Topic.id == q.topic_id).first()
        response.append(QuestionForReview(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            difficulty=q.difficulty,
            options=q.options,
            topic_name=topic.name if topic else "Unknown"
        ))

    return response


@router.post("/submit-answer")
def submit_answer(answer: SubmitAnswerRequest, db: Session = Depends(get_db)):
    """
    Submit an answer and update spaced repetition parameters
    """
    session = db.query(ReviewSession).filter(ReviewSession.id == answer.session_id).first()
    question = db.query(Question).filter(Question.id == answer.question_id).first()

    if not session or not question:
        raise HTTPException(status_code=404, detail="Session or question not found")

    # Create card review record
    card_review = CardReview(
        session_id=session.id,
        question_id=question.id,
        reviewed_at=datetime.utcnow(),
        user_answer=answer.user_answer,
        is_correct=answer.is_correct,
        confidence=answer.confidence
    )
    db.add(card_review)

    # Update question statistics
    question.times_reviewed += 1
    if answer.is_correct:
        question.times_correct += 1
    question.last_reviewed = datetime.utcnow()

    # Update spaced repetition parameters using SM-2 algorithm
    new_reps, new_ef, new_interval, next_review = sr_service.calculate_next_review(
        quality=answer.confidence,
        repetitions=question.repetitions,
        easiness_factor=question.easiness_factor,
        interval_days=question.interval_days
    )

    question.repetitions = new_reps
    question.easiness_factor = new_ef
    question.interval_days = new_interval
    question.next_review_date = next_review

    # Adjust difficulty if needed (Make It Stick: Desirable Difficulty)
    question.difficulty = sr_service.adjust_difficulty(question, answer.is_correct)

    # Update session stats
    session.total_questions += 1
    if answer.is_correct:
        session.correct_answers += 1

    # Update user preferences
    user_prefs = db.query(UserPreference).filter(UserPreference.user_id == session.user_id).first()
    if user_prefs:
        user_prefs.total_reviews += 1
        # Update average accuracy (moving average)
        if user_prefs.total_reviews == 1:
            user_prefs.avg_accuracy = 1.0 if answer.is_correct else 0.0
        else:
            user_prefs.avg_accuracy = (
                (user_prefs.avg_accuracy * (user_prefs.total_reviews - 1) +
                 (1.0 if answer.is_correct else 0.0)) / user_prefs.total_reviews
            )
        user_prefs.last_review_date = datetime.utcnow()

    db.commit()

    return {
        "message": "Answer submitted successfully",
        "next_review_in_days": new_interval,
        "is_correct": answer.is_correct
    }


@router.post("/end-session/{session_id}")
def end_session(session_id: int, db: Session = Depends(get_db)):
    """End a review session and calculate statistics"""
    session = db.query(ReviewSession).filter(ReviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = datetime.utcnow()

    # Calculate session statistics
    accuracy = (session.correct_answers / session.total_questions * 100) if session.total_questions > 0 else 0

    # Get topic breakdown
    card_reviews = db.query(CardReview).filter(CardReview.session_id == session_id).all()
    topics_covered = set()
    for review in card_reviews:
        question = db.query(Question).filter(Question.id == review.question_id).first()
        if question:
            topics_covered.add(question.topic_id)

    session.interleaved_topics = len(topics_covered)

    db.commit()

    return {
        "session_id": session.id,
        "total_questions": session.total_questions,
        "correct_answers": session.correct_answers,
        "accuracy": round(accuracy, 2),
        "topics_covered": len(topics_covered),
        "duration_minutes": (
            (session.ended_at - session.started_at).total_seconds() / 60
        ) if session.ended_at else 0
    }


@router.get("/stats")
def get_user_stats(db: Session = Depends(get_db)):
    """Get overall learning statistics"""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    sessions = db.query(ReviewSession).filter(ReviewSession.user_id == user.id).all()
    topics = db.query(Topic).filter(Topic.user_id == user.id).all()

    total_questions = sum(t.total_questions for t in topics)
    questions_due_today = len(sr_service.get_due_questions(db.query(Question).all()))

    return {
        "total_topics": len(topics),
        "total_questions": total_questions,
        "questions_due_today": questions_due_today,
        "total_reviews": prefs.total_reviews if prefs else 0,
        "average_accuracy": round(prefs.avg_accuracy * 100, 2) if prefs else 0,
        "streak_days": prefs.streak_days if prefs else 0,
        "total_sessions": len(sessions)
    }
