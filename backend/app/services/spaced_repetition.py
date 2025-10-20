"""
Spaced Repetition Service using SM-2 Algorithm
Based on Make It Stick principles for optimal memory retention
"""
from datetime import datetime, timedelta
from typing import Tuple


class SpacedRepetitionService:
    """
    Implements the SM-2 algorithm for spaced repetition

    Quality ratings (0-5):
    0 - Complete blackout
    1 - Incorrect, but recognized answer
    2 - Incorrect, but seemed easy
    3 - Correct, but difficult
    4 - Correct, with hesitation
    5 - Perfect response
    """

    @staticmethod
    def calculate_next_review(
        quality: int,
        repetitions: int,
        easiness_factor: float,
        interval_days: float
    ) -> Tuple[int, float, float, datetime]:
        """
        Calculate next review parameters based on SM-2 algorithm

        Args:
            quality: User's response quality (0-5)
            repetitions: Number of successful repetitions
            easiness_factor: Current easiness factor (EF)
            interval_days: Current interval in days

        Returns:
            Tuple of (new_repetitions, new_easiness_factor, new_interval_days, next_review_date)
        """
        # Calculate new easiness factor
        new_ef = max(1.3, easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

        # If quality < 3, start over
        if quality < 3:
            new_repetitions = 0
            new_interval = 0
        else:
            new_repetitions = repetitions + 1

            # Calculate new interval
            if new_repetitions == 1:
                new_interval = 1
            elif new_repetitions == 2:
                new_interval = 6
            else:
                new_interval = interval_days * new_ef

        # Calculate next review date
        next_review = datetime.utcnow() + timedelta(days=new_interval)

        return new_repetitions, new_ef, new_interval, next_review

    @staticmethod
    def get_due_questions(questions, current_time=None):
        """Get questions that are due for review"""
        if current_time is None:
            current_time = datetime.utcnow()

        return [q for q in questions if q.next_review_date <= current_time]

    @staticmethod
    def get_new_questions(questions, limit=5):
        """Get new questions that haven't been reviewed yet"""
        new_questions = [q for q in questions if q.times_reviewed == 0]
        return new_questions[:limit]

    @staticmethod
    def interleave_questions(questions, interleaving_ratio=0.3):
        """
        Apply interleaving - mix questions from different topics
        This is a key Make It Stick principle

        Args:
            questions: List of questions
            interleaving_ratio: Ratio of how much to mix topics (0-1)

        Returns:
            Shuffled list of questions with topics interleaved
        """
        if not questions or interleaving_ratio == 0:
            return questions

        # Group by topic
        from collections import defaultdict
        topic_groups = defaultdict(list)
        for q in questions:
            topic_groups[q.topic_id].append(q)

        # Interleave questions from different topics
        interleaved = []
        topic_lists = list(topic_groups.values())

        while any(topic_lists):
            for topic_list in topic_lists:
                if topic_list:
                    interleaved.append(topic_list.pop(0))

        return interleaved

    @staticmethod
    def adjust_difficulty(question, is_correct: bool, response_time_seconds: float = None):
        """
        Adaptively adjust question difficulty based on performance
        Make It Stick principle: Desirable difficulty
        """
        current_difficulty = question.difficulty

        # Simple difficulty adjustment logic
        if is_correct and question.times_correct / max(question.times_reviewed, 1) > 0.9:
            # User is finding this too easy
            if current_difficulty == 'easy':
                return 'medium'
            elif current_difficulty == 'medium':
                return 'hard'
        elif not is_correct and question.times_correct / max(question.times_reviewed, 1) < 0.4:
            # User is struggling
            if current_difficulty == 'hard':
                return 'medium'
            elif current_difficulty == 'medium':
                return 'easy'

        return current_difficulty
