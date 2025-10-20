"""
Learning Path Engine - Creates and adapts personalized learning journeys

Features:
- Builds concept dependency graphs
- Creates personalized curriculum sequences
- Adapts based on performance and understanding
- Identifies optimal next concepts to learn
- Manages prerequisite relationships
"""
from typing import List, Dict, Optional, Set
from collections import defaultdict, deque
import json


class LearningPathEngine:
    """
    Manages personalized learning paths and curriculum adaptation
    """

    def create_learning_path(
        self,
        topic_id: int,
        concepts: List[Dict],
        user_profile: Dict,
        target_depth: str = "apply"
    ) -> Dict:
        """
        Create an optimal learning path through concepts

        Args:
            topic_id: The topic being learned
            concepts: Available concepts with prerequisites
            user_profile: User's current knowledge and preferences
            target_depth: Target understanding level (Bloom's)

        Returns:
            Structured learning path with sequenced concepts
        """
        # Build dependency graph
        graph = self._build_dependency_graph(concepts)

        # Topological sort for valid learning order
        ordered_concepts = self._topological_sort(graph, concepts)

        # Personalize based on user's current knowledge
        personalized_sequence = self._personalize_sequence(
            ordered_concepts,
            user_profile,
            concepts
        )

        # Estimate time and difficulty
        path_stats = self._calculate_path_stats(personalized_sequence, concepts)

        return {
            "topic_id": topic_id,
            "concept_sequence": [c['id'] for c in personalized_sequence],
            "total_concepts": len(personalized_sequence),
            "estimated_hours": path_stats['total_hours'],
            "difficulty_curve": path_stats['difficulty_curve'],
            "milestones": self._identify_milestones(personalized_sequence),
            "target_depth": target_depth
        }

    def get_next_concept(
        self,
        learning_path: Dict,
        concept_masteries: List[Dict],
        concepts: List[Dict]
    ) -> Optional[Dict]:
        """
        Determine the next concept to learn based on:
        - Prerequisite mastery
        - Current progress
        - Optimal difficulty progression

        Returns:
            Next concept to study, or None if path complete
        """
        sequence = learning_path.get('concept_sequence', [])
        current_idx = learning_path.get('current_concept_index', 0)

        # Check if path is complete
        if current_idx >= len(sequence):
            return None

        # Get mastery status for all concepts
        mastery_map = {m['concept_id']: m for m in concept_masteries}

        # Find next unmastered concept with prerequisites met
        for idx in range(current_idx, len(sequence)):
            concept_id = sequence[idx]
            concept = next((c for c in concepts if c['id'] == concept_id), None)

            if not concept:
                continue

            # Check if prerequisites are mastered
            prereqs_met = self._check_prerequisites_met(
                concept,
                mastery_map,
                threshold=0.7  # 70% mastery required
            )

            if prereqs_met:
                # Check if this concept is already mastered
                mastery = mastery_map.get(concept_id)
                if not mastery or mastery.get('mastery_score', 0) < 0.8:
                    return {
                        'concept': concept,
                        'index': idx,
                        'progress': (idx / len(sequence)) * 100,
                        'prerequisites_status': 'met'
                    }

        # All concepts in path are mastered
        return None

    def adapt_path(
        self,
        learning_path: Dict,
        recent_performance: List[Dict],
        concept_masteries: List[Dict]
    ) -> Dict:
        """
        Adapt learning path based on performance

        Adjustments:
        - Skip concepts already mastered
        - Add remedial concepts for struggles
        - Adjust pace based on performance
        - Modify difficulty progression
        """
        adaptations = {
            "adjustments_made": [],
            "pace_change": None,
            "concepts_added": [],
            "concepts_skipped": []
        }

        # Analyze recent performance
        avg_performance = sum(p.get('score', 0) for p in recent_performance) / max(len(recent_performance), 1)

        # Adjust pace
        current_pace = learning_path.get('pace', 'moderate')
        if avg_performance > 0.9 and current_pace != 'fast':
            adaptations['pace_change'] = 'fast'
            adaptations['adjustments_made'].append("Increased pace due to strong performance")
        elif avg_performance < 0.6 and current_pace != 'slow':
            adaptations['pace_change'] = 'slow'
            adaptations['adjustments_made'].append("Slowed pace to strengthen fundamentals")

        # Identify struggling areas
        struggling_concepts = [
            m['concept_id']
            for m in concept_masteries
            if m.get('mastery_score', 0) < 0.5
        ]

        if struggling_concepts:
            adaptations['adjustments_made'].append(
                f"Identified {len(struggling_concepts)} concepts needing review"
            )

        # Skip mastered concepts
        mastered_concepts = [
            m['concept_id']
            for m in concept_masteries
            if m.get('mastery_score', 0) > 0.9
        ]

        if mastered_concepts:
            adaptations['concepts_skipped'] = mastered_concepts
            adaptations['adjustments_made'].append(
                f"Skipping {len(mastered_concepts)} mastered concepts"
            )

        return adaptations

    def suggest_review_concepts(
        self,
        concept_masteries: List[Dict],
        learning_path: Dict,
        max_suggestions: int = 5
    ) -> List[Dict]:
        """
        Suggest concepts for review based on:
        - Spaced repetition timing
        - Prerequisite for upcoming concepts
        - Declining mastery scores
        """
        suggestions = []

        for mastery in concept_masteries:
            score = 0

            # Recently learned but not fully mastered
            if 0.6 < mastery.get('mastery_score', 0) < 0.85:
                score += 3

            # Is a prerequisite for upcoming concepts
            # (would need to check graph - simplified here)
            if mastery.get('is_prerequisite', False):
                score += 2

            # Haven't practiced recently
            if mastery.get('days_since_practice', 0) > 7:
                score += 2

            # Has known misconceptions
            if mastery.get('misconceptions', []):
                score += 1

            if score > 0:
                suggestions.append({
                    'concept_id': mastery['concept_id'],
                    'priority_score': score,
                    'reason': self._get_review_reason(mastery)
                })

        # Sort by priority and return top suggestions
        suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
        return suggestions[:max_suggestions]

    def identify_knowledge_gaps(
        self,
        concept_masteries: List[Dict],
        concepts: List[Dict]
    ) -> List[Dict]:
        """
        Identify gaps in knowledge based on the dependency graph
        """
        gaps = []

        mastery_map = {m['concept_id']: m for m in concept_masteries}

        for concept in concepts:
            mastery = mastery_map.get(concept['id'])

            if mastery and mastery.get('mastery_score', 0) > 0.7:
                # Check if prerequisites are weaker than this concept
                prereqs = concept.get('prerequisites', [])
                weak_prereqs = [
                    pid for pid in prereqs
                    if mastery_map.get(pid, {}).get('mastery_score', 0) < 0.6
                ]

                if weak_prereqs:
                    gaps.append({
                        'type': 'weak_foundation',
                        'concept_id': concept['id'],
                        'weak_prerequisites': weak_prereqs,
                        'severity': 'high',
                        'recommendation': 'Review foundational concepts before proceeding'
                    })

            # Check for isolated knowledge (know concept but not applications)
            if mastery and mastery.get('current_level') == 'understand':
                gaps.append({
                    'type': 'needs_application',
                    'concept_id': concept['id'],
                    'severity': 'medium',
                    'recommendation': 'Practice applying this concept in different contexts'
                })

        return gaps

    def _build_dependency_graph(self, concepts: List[Dict]) -> Dict[int, List[int]]:
        """Build directed graph of concept dependencies"""
        graph = defaultdict(list)

        for concept in concepts:
            concept_id = concept['id']
            prereqs = concept.get('prerequisites', [])

            for prereq_id in prereqs:
                graph[prereq_id].append(concept_id)

        return dict(graph)

    def _topological_sort(self, graph: Dict, concepts: List[Dict]) -> List[Dict]:
        """
        Topological sort to get valid learning order
        Concepts with no prerequisites come first
        """
        # Calculate in-degree for each concept
        in_degree = defaultdict(int)
        concept_map = {c['id']: c for c in concepts}

        for concept in concepts:
            for prereq in concept.get('prerequisites', []):
                in_degree[concept['id']] += 1

        # Queue of concepts with no prerequisites
        queue = deque([c for c in concepts if in_degree[c['id']] == 0])
        sorted_concepts = []

        while queue:
            # Sort by difficulty (easier first)
            queue = deque(sorted(queue, key=lambda x: x.get('difficulty_level', 1)))
            concept = queue.popleft()
            sorted_concepts.append(concept)

            # Reduce in-degree for dependent concepts
            for dependent_id in graph.get(concept['id'], []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(concept_map[dependent_id])

        return sorted_concepts

    def _personalize_sequence(
        self,
        ordered_concepts: List[Dict],
        user_profile: Dict,
        all_concepts: List[Dict]
    ) -> List[Dict]:
        """
        Personalize the learning sequence based on user profile
        """
        # For now, keep the topological order
        # Could be enhanced to:
        # - Skip concepts user already knows
        # - Prioritize concepts matching user interests
        # - Adjust based on learning style
        return ordered_concepts

    def _calculate_path_stats(self, sequence: List[Dict], concepts: List[Dict]) -> Dict:
        """Calculate statistics about the learning path"""
        total_hours = sum(c.get('estimated_time_minutes', 30) for c in sequence) / 60
        difficulty_curve = [c.get('difficulty_level', 1) for c in sequence]

        return {
            'total_hours': round(total_hours, 1),
            'difficulty_curve': difficulty_curve,
            'avg_difficulty': sum(difficulty_curve) / len(difficulty_curve) if difficulty_curve else 0
        }

    def _identify_milestones(self, sequence: List[Dict]) -> List[Dict]:
        """Identify key milestones in the learning journey"""
        milestones = []
        total = len(sequence)

        # Every 25% is a milestone
        for i, pct in enumerate([0.25, 0.5, 0.75, 1.0]):
            idx = int(total * pct) - 1
            if 0 <= idx < len(sequence):
                milestones.append({
                    'percentage': int(pct * 100),
                    'concept_id': sequence[idx]['id'],
                    'name': f"{int(pct * 100)}% Complete",
                    'description': f"Mastered {sequence[idx]['name']}"
                })

        return milestones

    def _check_prerequisites_met(
        self,
        concept: Dict,
        mastery_map: Dict,
        threshold: float = 0.7
    ) -> bool:
        """Check if all prerequisites are mastered"""
        prereqs = concept.get('prerequisites', [])

        for prereq_id in prereqs:
            mastery = mastery_map.get(prereq_id)
            if not mastery or mastery.get('mastery_score', 0) < threshold:
                return False

        return True

    def _get_review_reason(self, mastery: Dict) -> str:
        """Generate human-readable reason for review suggestion"""
        reasons = []

        if 0.6 < mastery.get('mastery_score', 0) < 0.85:
            reasons.append("solidify understanding")

        if mastery.get('days_since_practice', 0) > 7:
            reasons.append("refresh memory")

        if mastery.get('misconceptions', []):
            reasons.append("address misconceptions")

        return ", ".join(reasons) if reasons else "periodic review"
