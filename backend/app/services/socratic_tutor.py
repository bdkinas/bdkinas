"""
Socratic Tutor Service - AI-powered adaptive teaching and depth assessment

This service implements:
- Socratic questioning to probe understanding depth
- Adaptive teaching based on knowledge gaps
- Bloom's Taxonomy progression
- Metacognition development
- Personalized learning conversations
"""
from typing import List, Dict, Optional, Tuple
from anthropic import Anthropic
import json
from ..core.config import settings
from datetime import datetime


class SocraticTutor:
    """
    An AI tutor that uses Socratic dialogue to teach and assess understanding
    """

    def __init__(self):
        if settings.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.client = None

    def start_tutoring_session(
        self,
        concept: Dict,
        user_profile: Dict,
        session_type: str = 'exploration'
    ) -> Dict:
        """
        Start a new tutoring session for a concept

        Args:
            concept: The concept to teach/explore
            user_profile: User's learning profile and history
            session_type: Type of session (exploration, depth_check, teaching, practice)

        Returns:
            Initial AI message and session context
        """
        if not self.client:
            return self._fallback_session_start(concept, session_type)

        # Build context about the user
        user_context = self._build_user_context(user_profile)

        # Create session-specific prompt
        session_prompts = {
            'exploration': self._exploration_prompt(concept, user_context),
            'depth_check': self._depth_check_prompt(concept, user_context),
            'teaching': self._teaching_prompt(concept, user_context),
            'practice': self._practice_prompt(concept, user_context),
            'reflection': self._reflection_prompt(concept, user_context)
        }

        prompt = session_prompts.get(session_type, session_prompts['exploration'])

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            ai_message = message.content[0].text

            return {
                "message": ai_message,
                "intent": "greeting",
                "session_context": {
                    "concept": concept['name'],
                    "session_type": session_type,
                    "started_at": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            print(f"Error starting tutoring session: {e}")
            return self._fallback_session_start(concept, session_type)

    def continue_dialogue(
        self,
        user_message: str,
        conversation_history: List[Dict],
        concept: Dict,
        session_context: Dict,
        user_profile: Dict
    ) -> Dict:
        """
        Continue the Socratic dialogue based on user's response

        Returns:
            AI response with metadata about intent, depth assessment, etc.
        """
        if not self.client:
            return self._fallback_response(user_message)

        # Analyze user's response for understanding signals
        understanding_analysis = self._analyze_understanding(
            user_message,
            concept,
            conversation_history
        )

        # Determine next move (question, teach, challenge, encourage)
        next_move = self._determine_next_move(
            understanding_analysis,
            session_context,
            user_profile
        )

        # Generate appropriate response
        response = self._generate_response(
            user_message,
            conversation_history,
            concept,
            next_move,
            understanding_analysis,
            user_profile
        )

        return response

    def assess_depth(
        self,
        user_responses: List[str],
        concept: Dict
    ) -> Dict:
        """
        Assess the user's depth of understanding (Bloom's Taxonomy)

        Returns:
            Assessment with level, confidence, gaps, and recommendations
        """
        if not self.client:
            return {"level": "understand", "confidence": 0.5}

        prompt = f"""Analyze these responses about the concept "{concept['name']}" and assess understanding depth.

Concept: {concept['name']}
Description: {concept.get('description', 'N/A')}

User responses:
{chr(10).join(f"- {r}" for r in user_responses)}

Assess their understanding using Bloom's Taxonomy:
1. REMEMBER - Can recall facts
2. UNDERSTAND - Can explain concepts
3. APPLY - Can use in new situations
4. ANALYZE - Can break down and examine
5. EVALUATE - Can judge and critique
6. CREATE - Can generate new ideas

Return a JSON object with:
{{
  "level": "remember|understand|apply|analyze|evaluate|create",
  "confidence": 0.0-1.0,
  "evidence": ["quote or observation that supports this assessment"],
  "knowledge_gaps": ["specific gaps in understanding"],
  "strengths": ["what they clearly understand"],
  "misconceptions": ["any incorrect beliefs detected"],
  "next_steps": ["what to focus on next"]
}}

Return ONLY the JSON object."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Extract JSON
            if '{' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                assessment = json.loads(response_text[start:end])
                return assessment
            else:
                return {"level": "understand", "confidence": 0.5}

        except Exception as e:
            print(f"Error assessing depth: {e}")
            return {"level": "understand", "confidence": 0.5}

    def generate_teaching_content(
        self,
        concept: Dict,
        knowledge_gaps: List[str],
        learning_style: str = "balanced"
    ) -> Dict:
        """
        Generate personalized teaching content based on identified gaps

        Args:
            concept: The concept to teach
            knowledge_gaps: Specific areas the user struggles with
            learning_style: User's preferred learning style

        Returns:
            Teaching content with explanations, examples, analogies
        """
        if not self.client:
            return self._fallback_teaching(concept)

        style_approaches = {
            "visual": "Use visual metaphors, diagrams descriptions, and spatial relationships",
            "verbal": "Use clear explanations, definitions, and written descriptions",
            "logical": "Use logical progression, cause-effect, and systematic breakdowns",
            "exploratory": "Use questions, discovery, and exploration",
            "balanced": "Use a mix of approaches"
        }

        prompt = f"""Create personalized teaching content for this concept.

Concept: {concept['name']}
Description: {concept.get('description', '')}

The learner struggles with:
{chr(10).join(f"- {gap}" for gap in knowledge_gaps)}

Learning style preference: {style_approaches.get(learning_style, style_approaches['balanced'])}

Provide teaching content as JSON:
{{
  "core_explanation": "Clear explanation addressing their gaps",
  "key_points": ["3-5 essential points to understand"],
  "examples": [
    {{"scenario": "real-world example", "explanation": "how it applies"}}
  ],
  "analogies": ["helpful comparisons to things they might know"],
  "practice_suggestions": ["ways to deepen understanding"],
  "connection_questions": ["questions to connect to prior knowledge"]
}}

Return ONLY the JSON object."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            if '{' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                teaching_content = json.loads(response_text[start:end])
                return teaching_content
            else:
                return self._fallback_teaching(concept)

        except Exception as e:
            print(f"Error generating teaching content: {e}")
            return self._fallback_teaching(concept)

    def _build_user_context(self, user_profile: Dict) -> str:
        """Build context string about the user for prompts"""
        context_parts = []

        if user_profile.get('avg_accuracy'):
            context_parts.append(f"Average accuracy: {user_profile['avg_accuracy']*100:.0f}%")

        if user_profile.get('learning_style'):
            context_parts.append(f"Learning style: {user_profile['learning_style']}")

        if user_profile.get('strengths'):
            context_parts.append(f"Strengths: {', '.join(user_profile['strengths'][:3])}")

        if user_profile.get('struggles'):
            context_parts.append(f"Areas for growth: {', '.join(user_profile['struggles'][:3])}")

        return "\n".join(context_parts) if context_parts else "New learner"

    def _exploration_prompt(self, concept: Dict, user_context: str) -> str:
        """Prompt for exploration session"""
        return f"""You are a Socratic tutor helping a student explore the concept: {concept['name']}.

Concept description: {concept.get('description', 'N/A')}

Student context:
{user_context}

Your approach:
1. Start with an engaging question to assess their current knowledge
2. Be encouraging and curious
3. Don't teach yet - just explore what they already know
4. Use Socratic questions: "What do you think...", "Why might...", "How would..."
5. Keep it conversational and supportive

Generate your opening message to start the exploration. Be warm, encouraging, and curious about what they already know."""

    def _depth_check_prompt(self, concept: Dict, user_context: str) -> str:
        """Prompt for depth assessment"""
        return f"""You are a Socratic tutor assessing depth of understanding for: {concept['name']}.

Concept: {concept.get('description', 'N/A')}

Student context:
{user_context}

Your goal is to probe their depth of understanding using Bloom's Taxonomy:
- Understanding: Can they explain it?
- Application: Can they use it in new contexts?
- Analysis: Can they break it down?

Start with a question that reveals how deeply they understand this concept. Not just recall, but true comprehension.

Be encouraging but intellectually curious."""

    def _teaching_prompt(self, concept: Dict, user_context: str) -> str:
        """Prompt for teaching session"""
        return f"""You are teaching the concept: {concept['name']}.

Concept: {concept.get('description', 'N/A')}

Student context:
{user_context}

Your teaching approach:
1. Explain clearly with examples
2. Use analogies they can relate to
3. Check understanding with questions
4. Connect to what they already know
5. Be encouraging and patient

Start your teaching. Make it engaging, clear, and connected to real life."""

    def _practice_prompt(self, concept: Dict, user_context: str) -> str:
        """Prompt for practice session"""
        return f"""Help the student practice applying: {concept['name']}.

Concept: {concept.get('description', 'N/A')}

Student context:
{user_context}

Your approach:
1. Present a realistic scenario where they need to apply this concept
2. Guide them through it with questions
3. Give feedback on their reasoning
4. Help them see patterns

Create an engaging practice scenario and guide them through it."""

    def _reflection_prompt(self, concept: Dict, user_context: str) -> str:
        """Prompt for reflection session"""
        return f"""Guide reflection on learning: {concept['name']}.

Help the student think about their thinking (metacognition):
- What did they learn?
- What was challenging?
- How does this connect to other knowledge?
- What strategies worked?

Ask thoughtful questions that promote self-awareness and learning strategies."""

    def _analyze_understanding(
        self,
        user_message: str,
        concept: Dict,
        history: List[Dict]
    ) -> Dict:
        """Analyze user's message for understanding signals"""
        # Simple heuristic analysis (could be enhanced with AI)
        signals = {
            "confidence": 0.5,
            "depth_indicators": [],
            "confusion_signals": [],
            "engagement": 0.5
        }

        message_lower = user_message.lower()

        # Positive signals
        if any(word in message_lower for word in ["because", "therefore", "which means", "for example"]):
            signals["confidence"] += 0.2
            signals["depth_indicators"].append("explains reasoning")

        if "?" in user_message:
            signals["engagement"] += 0.2
            signals["depth_indicators"].append("asks questions")

        # Confusion signals
        if any(word in message_lower for word in ["confused", "don't understand", "not sure", "maybe"]):
            signals["confidence"] -= 0.2
            signals["confusion_signals"].append("expresses uncertainty")

        if len(user_message.split()) < 5:
            signals["engagement"] -= 0.1
            signals["confusion_signals"].append("brief response")

        signals["confidence"] = max(0.0, min(1.0, signals["confidence"]))
        signals["engagement"] = max(0.0, min(1.0, signals["engagement"]))

        return signals

    def _determine_next_move(
        self,
        understanding: Dict,
        context: Dict,
        profile: Dict
    ) -> str:
        """Determine what the AI should do next"""
        confidence = understanding.get("confidence", 0.5)

        if confidence < 0.3:
            return "teach"  # They're confused, provide teaching
        elif confidence < 0.6:
            return "guide"  # They partially understand, guide them
        elif confidence < 0.8:
            return "challenge"  # They understand well, challenge them deeper
        else:
            return "extend"  # They've mastered it, extend to new applications

    def _generate_response(
        self,
        user_message: str,
        history: List[Dict],
        concept: Dict,
        next_move: str,
        understanding: Dict,
        profile: Dict
    ) -> Dict:
        """Generate AI's next response in the dialogue"""
        if not self.client:
            return self._fallback_response(user_message)

        # Build conversation context
        conversation = "\n".join([
            f"{turn['speaker']}: {turn['message']}"
            for turn in history[-6:]  # Last 6 turns
        ])

        move_instructions = {
            "teach": "They seem confused. Provide a clear, encouraging explanation. Use examples and analogies.",
            "guide": "They partially understand. Ask a guiding question that helps them discover the answer.",
            "challenge": "They understand well. Ask a deeper question that extends their thinking (apply, analyze).",
            "extend": "They've mastered this. Challenge them with novel applications or connections to other concepts."
        }

        prompt = f"""You are a Socratic tutor teaching: {concept['name']}.

Recent conversation:
{conversation}
Student: {user_message}

Next move: {move_instructions[next_move]}

Understanding signals:
- Confidence: {understanding['confidence']:.1%}
- Indicators: {', '.join(understanding.get('depth_indicators', ['none']))}
- Concerns: {', '.join(understanding.get('confusion_signals', ['none']))}

Respond as the tutor. Be:
- Encouraging and supportive
- Intellectually curious
- Clear and concise
- Socratic (ask questions when appropriate)

Your response:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )

            ai_response = message.content[0].text.strip()

            return {
                "message": ai_response,
                "intent": next_move,
                "understanding_assessment": understanding,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Error generating response: {e}")
            return self._fallback_response(user_message)

    def _fallback_session_start(self, concept: Dict, session_type: str) -> Dict:
        """Fallback when AI is not available"""
        messages = {
            'exploration': f"Let's explore {concept['name']} together! What do you already know about this topic?",
            'depth_check': f"Tell me what you understand about {concept['name']} in your own words.",
            'teaching': f"Let me teach you about {concept['name']}. {concept.get('description', '')}",
            'practice': f"Let's practice applying {concept['name']}. Ready?",
        }

        return {
            "message": messages.get(session_type, messages['exploration']),
            "intent": "greeting",
            "session_context": {"concept": concept['name'], "session_type": session_type}
        }

    def _fallback_response(self, user_message: str) -> Dict:
        """Fallback response when AI unavailable"""
        return {
            "message": "That's interesting! Can you explain more about your thinking?",
            "intent": "question",
            "understanding_assessment": {"confidence": 0.5}
        }

    def _fallback_teaching(self, concept: Dict) -> Dict:
        """Fallback teaching content"""
        return {
            "core_explanation": concept.get('description', f"Core concepts of {concept['name']}"),
            "key_points": ["Understanding the fundamentals", "Applying in practice", "Connecting to other concepts"],
            "examples": [],
            "analogies": [],
            "practice_suggestions": ["Try explaining it in your own words", "Find real-world examples"],
            "connection_questions": ["How does this relate to what you already know?"]
        }
