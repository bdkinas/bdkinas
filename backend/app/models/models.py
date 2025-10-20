from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    topics = relationship("Topic", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    review_sessions = relationship("ReviewSession", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    """Stores learned user preferences for personalized learning"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Learning style preferences (learned over time)
    preferred_question_types = Column(JSON, default=list)  # ['multiple_choice', 'open_ended', etc.]
    difficulty_preference = Column(String, default='medium')  # 'easy', 'medium', 'hard', 'adaptive'
    session_length_minutes = Column(Integer, default=20)
    questions_per_session = Column(Integer, default=10)

    # Make It Stick preferences
    interleaving_ratio = Column(Float, default=0.3)  # Mix old/new topics
    elaboration_frequency = Column(Float, default=0.2)  # How often to ask "why/how" questions
    generation_first = Column(Boolean, default=True)  # Try to answer before seeing content

    # Performance tracking
    avg_accuracy = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_review_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="preferences")


class Topic(Base):
    """A subject area the user wants to learn"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Topic metadata
    mastery_level = Column(Float, default=0.0)  # 0-1 scale
    total_questions = Column(Integer, default=0)

    user = relationship("User", back_populates="topics")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")


class Question(Base):
    """Individual question/flashcard with spaced repetition data"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))

    # Question content
    question_text = Column(Text)
    answer_text = Column(Text)
    question_type = Column(String)  # 'flashcard', 'multiple_choice', 'open_ended', 'elaboration'
    difficulty = Column(String, default='medium')  # 'easy', 'medium', 'hard'

    # Additional context
    explanation = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)  # For multiple choice
    tags = Column(JSON, default=list)

    # Spaced repetition (SM-2 algorithm)
    easiness_factor = Column(Float, default=2.5)  # EF in SM-2
    repetitions = Column(Integer, default=0)  # Number of successful reviews
    interval_days = Column(Float, default=0)  # Days until next review
    next_review_date = Column(DateTime, default=datetime.utcnow)

    # Performance tracking
    times_reviewed = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    last_reviewed = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    ai_generated = Column(Boolean, default=False)

    topic = relationship("Topic", back_populates="questions")
    reviews = relationship("CardReview", back_populates="question", cascade="all, delete-orphan")


class ReviewSession(Base):
    """A single study session"""
    __tablename__ = "review_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Session stats
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    session_type = Column(String)  # 'daily_review', 'new_material', 'mixed'

    # Make It Stick metrics
    interleaved_topics = Column(Integer, default=0)
    elaboration_questions = Column(Integer, default=0)

    user = relationship("User", back_populates="review_sessions")
    card_reviews = relationship("CardReview", back_populates="session", cascade="all, delete-orphan")


class CardReview(Base):
    """Individual card review within a session"""
    __tablename__ = "card_reviews"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("review_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    reviewed_at = Column(DateTime, default=datetime.utcnow)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean)
    confidence = Column(Integer)  # 1-5 scale (SM-2 quality rating)
    response_time_seconds = Column(Float, nullable=True)

    session = relationship("ReviewSession", back_populates="card_reviews")
    question = relationship("Question", back_populates="reviews")
