"""
AI Service for generating personalized quiz questions and learning user preferences
Uses Anthropic's Claude API for intelligent question generation
"""
import json
from typing import List, Dict, Optional
from anthropic import Anthropic
from ..core.config import settings


class AILearningService:
    """AI service that learns user preferences and generates personalized content"""

    def __init__(self):
        if settings.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.client = None

    def generate_questions(
        self,
        topic_name: str,
        topic_description: str,
        num_questions: int = 5,
        difficulty: str = 'medium',
        question_types: Optional[List[str]] = None,
        user_context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate quiz questions using AI based on topic and user preferences

        Args:
            topic_name: Name of the topic
            topic_description: Description/context of the topic
            num_questions: Number of questions to generate
            difficulty: 'easy', 'medium', or 'hard'
            question_types: List of preferred question types
            user_context: Additional user context for personalization

        Returns:
            List of generated questions
        """
        if not self.client:
            return self._generate_fallback_questions(topic_name, num_questions)

        question_types = question_types or ['flashcard', 'multiple_choice', 'open_ended']
        user_context = user_context or {}

        prompt = f"""You are an expert educator creating quiz questions based on Make It Stick principles.

Topic: {topic_name}
Description: {topic_description}
Difficulty Level: {difficulty}
Number of Questions: {num_questions}
Question Types: {', '.join(question_types)}

User Context:
- Average accuracy: {user_context.get('avg_accuracy', 'N/A')}
- Learning preferences: {user_context.get('preferences', 'N/A')}

Generate {num_questions} high-quality learning questions that:
1. Promote retrieval practice (testing enhances learning)
2. Encourage elaboration (connecting to existing knowledge)
3. Require generation (producing answers, not just recognition)
4. Vary in difficulty to maintain desirable difficulty
5. Are personalized to the user's level and preferences

Return ONLY a JSON array of questions in this exact format:
[
  {{
    "question_text": "The question text here",
    "answer_text": "The correct answer",
    "question_type": "flashcard|multiple_choice|open_ended|elaboration",
    "difficulty": "easy|medium|hard",
    "explanation": "Why this answer is correct and how it connects to broader concepts",
    "options": ["option1", "option2", "option3", "option4"] (only for multiple_choice, null otherwise),
    "tags": ["tag1", "tag2"]
  }}
]

Important: Return ONLY the JSON array, no other text."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Try to extract JSON from response
            if response_text.startswith('['):
                questions = json.loads(response_text)
            else:
                # Try to find JSON in the response
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                if start != -1 and end > start:
                    questions = json.loads(response_text[start:end])
                else:
                    return self._generate_fallback_questions(topic_name, num_questions)

            return questions

        except Exception as e:
            print(f"Error generating questions with AI: {e}")
            return self._generate_fallback_questions(topic_name, num_questions)

    def generate_elaboration_prompt(self, question_text: str, answer_text: str) -> str:
        """
        Generate an elaboration prompt for a question
        Make It Stick principle: Elaboration deepens understanding
        """
        if not self.client:
            return f"Explain why this is the answer and how it connects to what you already know."

        prompt = f"""Create a brief elaboration prompt for this learning question.

Question: {question_text}
Answer: {answer_text}

Generate a follow-up question that encourages the learner to:
1. Connect this to their existing knowledge
2. Think about why this answer makes sense
3. Consider real-world applications

Return only the elaboration question, nothing else."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Error generating elaboration: {e}")
            return "How does this answer connect to what you already know about this topic?"

    def analyze_user_performance(self, review_history: List[Dict]) -> Dict:
        """
        Analyze user performance to learn preferences and adjust recommendations

        Args:
            review_history: List of recent review sessions

        Returns:
            Dictionary with learned preferences and recommendations
        """
        if not review_history:
            return {
                'recommended_difficulty': 'medium',
                'recommended_session_length': 20,
                'recommended_question_types': ['flashcard', 'multiple_choice'],
                'insights': ['Not enough data yet. Keep practicing!']
            }

        # Calculate metrics
        total_reviews = len(review_history)
        correct_reviews = sum(1 for r in review_history if r.get('is_correct'))
        accuracy = correct_reviews / total_reviews if total_reviews > 0 else 0

        # Analyze question type performance
        type_performance = {}
        for review in review_history:
            q_type = review.get('question_type', 'flashcard')
            if q_type not in type_performance:
                type_performance[q_type] = {'correct': 0, 'total': 0}
            type_performance[q_type]['total'] += 1
            if review.get('is_correct'):
                type_performance[q_type]['correct'] += 1

        # Determine best question types
        best_types = sorted(
            type_performance.keys(),
            key=lambda t: type_performance[t]['correct'] / max(type_performance[t]['total'], 1),
            reverse=True
        )

        # Determine difficulty
        if accuracy > 0.85:
            recommended_difficulty = 'hard'
        elif accuracy > 0.65:
            recommended_difficulty = 'medium'
        else:
            recommended_difficulty = 'easy'

        insights = []
        if accuracy > 0.8:
            insights.append("Great job! You're mastering this material.")
        elif accuracy > 0.6:
            insights.append("Good progress. Keep up the consistent practice.")
        else:
            insights.append("Consider reviewing fundamentals or reducing difficulty.")

        return {
            'recommended_difficulty': recommended_difficulty,
            'recommended_session_length': 20,
            'recommended_question_types': best_types[:2] if best_types else ['flashcard'],
            'accuracy': accuracy,
            'insights': insights
        }

    def _generate_fallback_questions(self, topic_name: str, num_questions: int) -> List[Dict]:
        """Generate simple fallback questions when AI is not available"""
        return [
            {
                "question_text": f"What is an important concept in {topic_name}? (Question {i+1})",
                "answer_text": "Add your answer here",
                "question_type": "open_ended",
                "difficulty": "medium",
                "explanation": "This is a template question. Edit it to match your learning needs.",
                "options": None,
                "tags": [topic_name.lower()]
            }
            for i in range(num_questions)
        ]
