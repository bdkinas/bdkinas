"""
Extended models for AI tutoring and personalized learning journeys
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base
import enum


class UnderstandingLevel(str, enum.Enum):
    """Bloom's Taxonomy levels"""
    NONE = "none"  # No knowledge
    REMEMBER = "remember"  # Can recall facts
    UNDERSTAND = "understand"  # Can explain concepts
    APPLY = "apply"  # Can use in new situations
    ANALYZE = "analyze"  # Can break down and examine
    EVALUATE = "evaluate"  # Can judge and critique
    CREATE = "create"  # Can generate new ideas


class Concept(Base):
    """
    A core concept or idea within a topic
    Represents nodes in the knowledge graph
    """
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))

    name = Column(String, index=True)
    description = Column(Text)

    # Learning structure
    prerequisites = Column(JSON, default=list)  # IDs of prerequisite concepts
    difficulty_level = Column(Integer, default=1)  # 1-5 scale
    estimated_time_minutes = Column(Integer, default=30)

    # Content
    explanation = Column(Text, nullable=True)  # Core teaching content
    examples = Column(JSON, default=list)  # List of examples
    analogies = Column(JSON, default=list)  # Helpful analogies
    common_misconceptions = Column(JSON, default=list)  # What students often get wrong

    # Metadata
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("Topic", backref="concepts")
    masteries = relationship("ConceptMastery", back_populates="concept", cascade="all, delete-orphan")


class ConceptMastery(Base):
    """
    Tracks a user's understanding depth for each concept
    """
    __tablename__ = "concept_mastery"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    concept_id = Column(Integer, ForeignKey("concepts.id"))

    # Understanding depth (Bloom's Taxonomy)
    current_level = Column(String, default=UnderstandingLevel.NONE.value)
    target_level = Column(String, default=UnderstandingLevel.APPLY.value)

    # Confidence and mastery
    confidence_score = Column(Float, default=0.0)  # 0-1 scale
    mastery_score = Column(Float, default=0.0)  # 0-1 scale

    # Progress tracking
    times_practiced = Column(Integer, default=0)
    times_taught = Column(Integer, default=0)  # Times AI taught this concept
    last_practiced = Column(DateTime, nullable=True)

    # Learning insights
    struggling_areas = Column(JSON, default=list)  # Specific aspects they struggle with
    strengths = Column(JSON, default=list)  # What they understand well
    misconceptions = Column(JSON, default=list)  # Tracked misconceptions

    # Spaced repetition
    next_review_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="concept_masteries")
    concept = relationship("Concept", back_populates="masteries")


class LearningPath(Base):
    """
    Personalized learning journey for a user
    """
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))

    name = Column(String)
    description = Column(Text)

    # Path structure
    concept_sequence = Column(JSON, default=list)  # Ordered list of concept IDs
    current_concept_id = Column(Integer, nullable=True)

    # Progress
    concepts_mastered = Column(Integer, default=0)
    total_concepts = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    # Personalization
    learning_style = Column(String, default="balanced")  # visual, verbal, kinesthetic, logical
    pace = Column(String, default="moderate")  # slow, moderate, fast
    challenge_level = Column(String, default="optimal")  # easy, optimal, challenging

    # Status
    status = Column(String, default="active")  # active, completed, paused
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="learning_paths")
    topic = relationship("Topic", backref="learning_paths")


class TutoringSession(Base):
    """
    An interactive tutoring session (different from quiz review sessions)
    """
    __tablename__ = "tutoring_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)

    # Session info
    session_type = Column(String)  # 'exploration', 'depth_check', 'teaching', 'practice', 'reflection'
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Session goals
    learning_objectives = Column(JSON, default=list)
    concepts_covered = Column(JSON, default=list)

    # Outcomes
    depth_achieved = Column(String, nullable=True)  # UnderstandingLevel
    insights_gained = Column(JSON, default=list)
    struggles_identified = Column(JSON, default=list)

    # AI coaching
    teaching_approach = Column(String, default="socratic")  # socratic, direct, exploratory
    ai_personality = Column(String, default="encouraging")  # encouraging, challenging, neutral

    # Metrics
    turns_count = Column(Integer, default=0)
    quality_score = Column(Float, nullable=True)  # How productive was the session

    user = relationship("User", backref="tutoring_sessions")
    learning_path = relationship("LearningPath", backref="tutoring_sessions")
    concept = relationship("Concept", backref="tutoring_sessions")
    dialogue = relationship("DialogueTurn", back_populates="session", cascade="all, delete-orphan")


class DialogueTurn(Base):
    """
    A single turn in the Socratic dialogue
    """
    __tablename__ = "dialogue_turns"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("tutoring_sessions.id"))

    turn_number = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Content
    speaker = Column(String)  # 'ai' or 'user'
    message = Column(Text)

    # AI metadata (when speaker is 'ai')
    intent = Column(String, nullable=True)  # 'question', 'explanation', 'feedback', 'encouragement', 'challenge'
    question_type = Column(String, nullable=True)  # 'why', 'how', 'what_if', 'explain', 'apply'
    depth_target = Column(String, nullable=True)  # Which Bloom's level this targets

    # User metadata (when speaker is 'user')
    understanding_signals = Column(JSON, default=list)  # Detected understanding/confusion
    detected_level = Column(String, nullable=True)  # Assessed understanding level

    session = relationship("TutoringSession", back_populates="dialogue")


class Reflection(Base):
    """
    User reflections on their learning (metacognition)
    """
    __tablename__ = "reflections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("tutoring_sessions.id"), nullable=True)

    reflection_type = Column(String)  # 'session_end', 'weekly', 'concept_mastery', 'struggle'

    # Content
    prompt = Column(Text)  # What they were asked to reflect on
    response = Column(Text)  # Their reflection

    # Insights
    key_insights = Column(JSON, default=list)  # AI-extracted insights
    action_items = Column(JSON, default=list)  # What to work on

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="reflections")
    session = relationship("TutoringSession", backref="reflections")


class LearningInsight(Base):
    """
    AI-generated insights about the user's learning patterns
    """
    __tablename__ = "learning_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    insight_type = Column(String)  # 'strength', 'struggle', 'pattern', 'recommendation', 'milestone'
    category = Column(String)  # 'knowledge', 'skill', 'metacognition', 'motivation', 'strategy'

    title = Column(String)
    description = Column(Text)
    evidence = Column(JSON, default=list)  # Supporting data

    # Action
    actionable = Column(Boolean, default=False)
    suggested_actions = Column(JSON, default=list)

    # Status
    acknowledged = Column(Boolean, default=False)
    acted_on = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="learning_insights")
