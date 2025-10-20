from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..core.database import get_db
from ..models.models import User, Topic, UserPreference
from ..models.tutoring_models import (
    Concept, ConceptMastery, LearningPath, TutoringSession,
    DialogueTurn, Reflection, LearningInsight, UnderstandingLevel
)
from ..services.socratic_tutor import SocraticTutor
from ..services.learning_path_engine import LearningPathEngine

router = APIRouter(prefix="/tutoring", tags=["tutoring"])
tutor = SocraticTutor()
path_engine = LearningPathEngine()


# Request/Response Models
class ConceptCreate(BaseModel):
    topic_id: int
    name: str
    description: str
    prerequisites: List[int] = []
    difficulty_level: int = 1
    estimated_time_minutes: int = 30


class ConceptResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    description: str
    difficulty_level: int
    estimated_time_minutes: int

    class Config:
        from_attributes = True


class StartTutoringRequest(BaseModel):
    concept_id: Optional[int] = None
    session_type: str = 'exploration'  # exploration, depth_check, teaching, practice, reflection


class ContinueDialogueRequest(BaseModel):
    session_id: int
    user_message: str


class DialogueResponse(BaseModel):
    turn_id: int
    speaker: str
    message: str
    intent: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class CreateLearningPathRequest(BaseModel):
    topic_id: int
    target_depth: str = "apply"


class LearningPathResponse(BaseModel):
    id: int
    name: str
    progress_percentage: float
    concepts_mastered: int
    total_concepts: int
    current_concept_id: Optional[int]

    class Config:
        from_attributes = True


# Concept Management
@router.post("/concepts", response_model=ConceptResponse)
def create_concept(concept: ConceptCreate, db: Session = Depends(get_db)):
    """Create a new concept within a topic"""
    topic = db.query(Topic).filter(Topic.id == concept.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db_concept = Concept(
        topic_id=concept.topic_id,
        name=concept.name,
        description=concept.description,
        prerequisites=concept.prerequisites,
        difficulty_level=concept.difficulty_level,
        estimated_time_minutes=concept.estimated_time_minutes
    )
    db.add(db_concept)
    db.commit()
    db.refresh(db_concept)
    return db_concept


@router.get("/concepts/topic/{topic_id}", response_model=List[ConceptResponse])
def get_topic_concepts(topic_id: int, db: Session = Depends(get_db)):
    """Get all concepts for a topic"""
    concepts = db.query(Concept).filter(Concept.topic_id == topic_id).all()
    return concepts


@router.post("/concepts/{concept_id}/generate-content")
def generate_concept_content(concept_id: int, db: Session = Depends(get_db)):
    """Generate teaching content for a concept using AI"""
    from ..services.ai_service import AILearningService
    ai_service = AILearningService()

    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Generate comprehensive teaching content
    content = tutor.generate_teaching_content(
        concept={
            'id': concept.id,
            'name': concept.name,
            'description': concept.description
        },
        knowledge_gaps=["General understanding"],  # Could be personalized
        learning_style="balanced"
    )

    # Update concept with generated content
    concept.explanation = content.get('core_explanation')
    concept.examples = content.get('examples', [])
    concept.analogies = content.get('analogies', [])

    db.commit()

    return {
        "message": "Content generated successfully",
        "content": content
    }


# Learning Path Management
@router.post("/learning-paths", response_model=LearningPathResponse)
def create_learning_path(request: CreateLearningPathRequest, db: Session = Depends(get_db)):
    """Create a personalized learning path for a topic"""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Get all concepts for this topic
    concepts = db.query(Concept).filter(Concept.topic_id == request.topic_id).all()

    if not concepts:
        raise HTTPException(status_code=400, detail="No concepts found for this topic. Create concepts first.")

    # Get user profile
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    user_profile = {
        'avg_accuracy': prefs.avg_accuracy if prefs else 0.0,
        'learning_style': 'balanced'
    }

    # Convert concepts to dicts
    concepts_data = [{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'prerequisites': c.prerequisites or [],
        'difficulty_level': c.difficulty_level,
        'estimated_time_minutes': c.estimated_time_minutes
    } for c in concepts]

    # Generate learning path
    path_data = path_engine.create_learning_path(
        topic_id=request.topic_id,
        concepts=concepts_data,
        user_profile=user_profile,
        target_depth=request.target_depth
    )

    # Create learning path in database
    learning_path = LearningPath(
        user_id=user.id,
        topic_id=request.topic_id,
        name=f"{topic.name} Learning Journey",
        description=f"Personalized path through {len(concepts)} concepts",
        concept_sequence=path_data['concept_sequence'],
        total_concepts=path_data['total_concepts'],
        current_concept_id=path_data['concept_sequence'][0] if path_data['concept_sequence'] else None
    )

    db.add(learning_path)
    db.commit()
    db.refresh(learning_path)

    return learning_path


@router.get("/learning-paths", response_model=List[LearningPathResponse])
def get_learning_paths(db: Session = Depends(get_db)):
    """Get all learning paths for the user"""
    paths = db.query(LearningPath).all()
    return paths


@router.get("/learning-paths/{path_id}/next-concept")
def get_next_concept(path_id: int, db: Session = Depends(get_db)):
    """Get the next concept to learn in the path"""
    learning_path = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get concept masteries
    masteries = db.query(ConceptMastery).filter(
        ConceptMastery.user_id == learning_path.user_id
    ).all()

    mastery_data = [{
        'concept_id': m.concept_id,
        'mastery_score': m.mastery_score,
        'current_level': m.current_level
    } for m in masteries]

    # Get all concepts
    concepts = db.query(Concept).filter(
        Concept.id.in_(learning_path.concept_sequence)
    ).all()

    concepts_data = [{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'prerequisites': c.prerequisites or []
    } for c in concepts]

    # Get next concept
    next_concept = path_engine.get_next_concept(
        learning_path={
            'concept_sequence': learning_path.concept_sequence,
            'current_concept_index': learning_path.concepts_mastered
        },
        concept_masteries=mastery_data,
        concepts=concepts_data
    )

    if not next_concept:
        return {
            "message": "Learning path completed!",
            "completed": True
        }

    return next_concept


# Tutoring Sessions
@router.post("/sessions/start")
def start_tutoring_session(request: StartTutoringRequest, db: Session = Depends(get_db)):
    """Start a new AI tutoring session"""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get concept if specified
    concept = None
    if request.concept_id:
        concept = db.query(Concept).filter(Concept.id == request.concept_id).first()
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

    # Get user profile
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    user_profile = {
        'avg_accuracy': prefs.avg_accuracy if prefs else 0.0,
        'learning_style': 'balanced',
        'strengths': [],
        'struggles': []
    }

    # Start AI tutoring session
    if concept:
        session_start = tutor.start_tutoring_session(
            concept={
                'id': concept.id,
                'name': concept.name,
                'description': concept.description
            },
            user_profile=user_profile,
            session_type=request.session_type
        )
    else:
        session_start = {
            "message": "Hi! I'm your AI learning coach. What would you like to explore today?",
            "intent": "greeting",
            "session_context": {}
        }

    # Create session in database
    session = TutoringSession(
        user_id=user.id,
        concept_id=request.concept_id,
        session_type=request.session_type,
        teaching_approach="socratic"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Add first AI message to dialogue
    ai_turn = DialogueTurn(
        session_id=session.id,
        turn_number=1,
        speaker='ai',
        message=session_start['message'],
        intent=session_start.get('intent')
    )
    db.add(ai_turn)
    session.turns_count = 1
    db.commit()

    return {
        "session_id": session.id,
        "message": session_start['message'],
        "session_type": request.session_type
    }


@router.post("/sessions/continue")
def continue_dialogue(request: ContinueDialogueRequest, db: Session = Depends(get_db)):
    """Continue the Socratic dialogue"""
    session = db.query(TutoringSession).filter(
        TutoringSession.id == request.session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get conversation history
    history = db.query(DialogueTurn).filter(
        DialogueTurn.session_id == session.id
    ).order_by(DialogueTurn.turn_number).all()

    history_data = [{
        'speaker': turn.speaker,
        'message': turn.message,
        'intent': turn.intent
    } for turn in history]

    # Add user's message
    user_turn = DialogueTurn(
        session_id=session.id,
        turn_number=session.turns_count + 1,
        speaker='user',
        message=request.user_message
    )
    db.add(user_turn)
    session.turns_count += 1

    # Get concept info
    concept = None
    if session.concept_id:
        concept = db.query(Concept).filter(Concept.id == session.concept_id).first()

    concept_data = {
        'id': concept.id,
        'name': concept.name,
        'description': concept.description
    } if concept else {'id': 0, 'name': 'General', 'description': 'General discussion'}

    # Get user profile
    prefs = db.query(UserPreference).filter(UserPreference.user_id == session.user_id).first()
    user_profile = {
        'avg_accuracy': prefs.avg_accuracy if prefs else 0.0,
        'learning_style': 'balanced'
    }

    # Generate AI response
    ai_response = tutor.continue_dialogue(
        user_message=request.user_message,
        conversation_history=history_data,
        concept=concept_data,
        session_context={'session_type': session.session_type},
        user_profile=user_profile
    )

    # Add AI response to dialogue
    ai_turn = DialogueTurn(
        session_id=session.id,
        turn_number=session.turns_count + 1,
        speaker='ai',
        message=ai_response['message'],
        intent=ai_response.get('intent')
    )
    db.add(ai_turn)
    session.turns_count += 1

    db.commit()

    return {
        "message": ai_response['message'],
        "intent": ai_response.get('intent'),
        "understanding_assessment": ai_response.get('understanding_assessment')
    }


@router.post("/sessions/{session_id}/end")
def end_tutoring_session(session_id: int, db: Session = Depends(get_db)):
    """End a tutoring session and assess learning"""
    session = db.query(TutoringSession).filter(TutoringSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = datetime.utcnow()

    # Get all user responses
    user_turns = db.query(DialogueTurn).filter(
        DialogueTurn.session_id == session_id,
        DialogueTurn.speaker == 'user'
    ).all()

    user_responses = [turn.message for turn in user_turns]

    # Assess depth if we have a concept
    if session.concept_id and user_responses:
        concept = db.query(Concept).filter(Concept.id == session.concept_id).first()

        assessment = tutor.assess_depth(
            user_responses=user_responses,
            concept={
                'id': concept.id,
                'name': concept.name,
                'description': concept.description
            }
        )

        session.depth_achieved = assessment.get('level', 'understand')
        session.insights_gained = assessment.get('strengths', [])
        session.struggles_identified = assessment.get('knowledge_gaps', [])

        # Update or create concept mastery
        mastery = db.query(ConceptMastery).filter(
            ConceptMastery.user_id == session.user_id,
            ConceptMastery.concept_id == session.concept_id
        ).first()

        if not mastery:
            mastery = ConceptMastery(
                user_id=session.user_id,
                concept_id=session.concept_id
            )
            db.add(mastery)

        # Update mastery based on assessment
        mastery.current_level = assessment.get('level', 'understand')
        mastery.confidence_score = assessment.get('confidence', 0.5)
        mastery.times_practiced += 1
        mastery.last_practiced = datetime.utcnow()

        # Update mastery score (weighted average)
        new_score = assessment.get('confidence', 0.5)
        if mastery.times_practiced == 1:
            mastery.mastery_score = new_score
        else:
            mastery.mastery_score = (mastery.mastery_score * 0.7 + new_score * 0.3)

        # Track gaps and strengths
        mastery.struggling_areas = assessment.get('knowledge_gaps', [])
        mastery.strengths = assessment.get('strengths', [])
        mastery.misconceptions = assessment.get('misconceptions', [])

    db.commit()

    return {
        "session_id": session.id,
        "turns": session.turns_count,
        "depth_achieved": session.depth_achieved,
        "insights": session.insights_gained,
        "areas_to_review": session.struggles_identified
    }


@router.get("/sessions/{session_id}/dialogue", response_model=List[DialogueResponse])
def get_session_dialogue(session_id: int, db: Session = Depends(get_db)):
    """Get full dialogue history for a session"""
    dialogue = db.query(DialogueTurn).filter(
        DialogueTurn.session_id == session_id
    ).order_by(DialogueTurn.turn_number).all()

    return dialogue


# Concept Mastery
@router.get("/mastery/concept/{concept_id}")
def get_concept_mastery(concept_id: int, db: Session = Depends(get_db)):
    """Get user's mastery of a specific concept"""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    mastery = db.query(ConceptMastery).filter(
        ConceptMastery.user_id == user.id,
        ConceptMastery.concept_id == concept_id
    ).first()

    if not mastery:
        return {
            "concept_id": concept_id,
            "current_level": "none",
            "mastery_score": 0.0,
            "confidence_score": 0.0
        }

    return {
        "concept_id": mastery.concept_id,
        "current_level": mastery.current_level,
        "mastery_score": mastery.mastery_score,
        "confidence_score": mastery.confidence_score,
        "times_practiced": mastery.times_practiced,
        "struggling_areas": mastery.struggling_areas,
        "strengths": mastery.strengths,
        "misconceptions": mastery.misconceptions
    }


@router.get("/insights")
def get_learning_insights(db: Session = Depends(get_db)):
    """Get AI-generated insights about learning patterns"""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    insights = db.query(LearningInsight).filter(
        LearningInsight.user_id == user.id
    ).order_by(LearningInsight.created_at.desc()).limit(10).all()

    return [{
        'id': i.id,
        'type': i.insight_type,
        'category': i.category,
        'title': i.title,
        'description': i.description,
        'actionable': i.actionable,
        'suggested_actions': i.suggested_actions
    } for i in insights]
