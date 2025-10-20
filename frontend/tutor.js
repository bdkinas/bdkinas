// AI Tutor Interface
const API_BASE = 'http://localhost:8000';

// Global state
let currentSessionId = null;
let currentMode = null;
let currentConcept = null;
let currentTopicId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTopicsForTutor();
    loadKnowledgeDashboard();
    loadLearningPaths();

    // Enter key to send message
    document.getElementById('user-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// Mode Selection
function selectMode(mode) {
    currentMode = mode;

    const descriptions = {
        'exploration': 'The AI will ask you questions to discover what you already know about this concept.',
        'depth_check': 'The AI will probe how deeply you understand this concept using Bloom\'s Taxonomy.',
        'teaching': 'The AI will teach you this concept using explanations, examples, and guided questions.',
        'practice': 'Apply this concept in realistic scenarios with AI guidance.',
        'reflection': 'Reflect on your learning journey and develop metacognitive skills.'
    };

    document.getElementById('mode-description').textContent = descriptions[mode];
    document.getElementById('mode-selection').style.display = 'none';
    document.getElementById('concept-selection').style.display = 'block';
}

function backToModeSelection() {
    document.getElementById('concept-selection').style.display = 'none';
    document.getElementById('learning-paths-view').style.display = 'none';
    document.getElementById('mode-selection').style.display = 'block';
}

// Load topics and concepts
async function loadTopicsForTutor() {
    try {
        const response = await fetch(`${API_BASE}/topics/`);
        const topics = await response.json();

        const topicsList = document.getElementById('topics-list');

        if (topics.length === 0) {
            topicsList.innerHTML = '<p>No topics yet. Go to Quiz Mode to create topics first.</p>';
            return;
        }

        let html = '';
        for (const topic of topics) {
            // Get concepts for this topic
            const conceptsResponse = await fetch(`${API_BASE}/tutoring/concepts/topic/${topic.id}`);
            const concepts = await conceptsResponse.json();

            html += `
                <div class="topic-item-tutor">
                    <h3>${escapeHtml(topic.name)}</h3>
                    <p>${escapeHtml(topic.description)}</p>
                    ${concepts.length === 0 ?
                        `<button onclick="createConceptsForTopic(${topic.id})" class="btn btn-primary">Create Concepts</button>` :
                        `<div class="concept-list">
                            ${concepts.map(c => `
                                <div class="concept-item" onclick="startTutoringWithConcept(${c.id}, '${escapeHtml(c.name)}')">
                                    <div>
                                        <div class="concept-name">${escapeHtml(c.name)}</div>
                                        <div class="concept-difficulty">Difficulty: Level ${c.difficulty_level}/5</div>
                                    </div>
                                    <span class="mastery-badge mastery-none">Start Learning</span>
                                </div>
                            `).join('')}
                        </div>`
                    }
                </div>
            `;
        }

        topicsList.innerHTML = html;
    } catch (error) {
        console.error('Error loading topics:', error);
    }
}

// Create concepts for a topic
async function createConceptsForTopic(topicId) {
    if (!confirm('This will use AI to generate concepts for this topic. Continue?')) {
        return;
    }

    try {
        // For simplicity, create a few basic concepts
        // In a real app, you'd use AI to generate these
        const conceptNames = [
            'Fundamentals',
            'Core Concepts',
            'Applications',
            'Advanced Topics'
        ];

        for (let i = 0; i < conceptNames.length; i++) {
            await fetch(`${API_BASE}/tutoring/concepts`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic_id: topicId,
                    name: conceptNames[i],
                    description: `${conceptNames[i]} to master`,
                    prerequisites: i > 0 ? [i] : [],
                    difficulty_level: i + 1,
                    estimated_time_minutes: 30
                })
            });
        }

        alert('Concepts created! Reloading...');
        loadTopicsForTutor();
    } catch (error) {
        console.error('Error creating concepts:', error);
        alert('Failed to create concepts');
    }
}

// Start tutoring session
async function startTutoringWithConcept(conceptId, conceptName) {
    currentConcept = {id: conceptId, name: conceptName};

    try {
        const response = await fetch(`${API_BASE}/tutoring/sessions/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                concept_id: conceptId,
                session_type: currentMode
            })
        });

        const session = await response.json();
        currentSessionId = session.session_id;

        // Show session view
        document.getElementById('concept-selection').style.display = 'none';
        document.getElementById('tutoring-session').style.display = 'block';

        // Update header
        document.getElementById('session-concept').textContent = conceptName;
        const modeLabels = {
            'exploration': '🔍 Exploration Mode',
            'depth_check': '🎯 Depth Check Mode',
            'teaching': '📚 Teaching Mode',
            'practice': '💪 Practice Mode',
            'reflection': '🤔 Reflection Mode'
        };
        document.getElementById('session-mode').textContent = modeLabels[currentMode];

        // Clear chat and add AI's opening message
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';

        addMessageToChat('ai', session.message, 'greeting');

    } catch (error) {
        console.error('Error starting session:', error);
        alert('Failed to start tutoring session');
    }
}

// Send message
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();

    if (!message || !currentSessionId) return;

    // Add user message to chat
    addMessageToChat('user', message);
    input.value = '';

    // Show thinking indicator
    document.getElementById('thinking-indicator').style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/tutoring/sessions/continue`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: currentSessionId,
                user_message: message
            })
        });

        const aiResponse = await response.json();

        // Hide thinking indicator
        document.getElementById('thinking-indicator').style.display = 'none';

        // Add AI response
        addMessageToChat('ai', aiResponse.message, aiResponse.intent);

    } catch (error) {
        console.error('Error sending message:', error);
        document.getElementById('thinking-indicator').style.display = 'none';
        addMessageToChat('ai', 'Sorry, I encountered an error. Please try again.', 'error');
    }
}

// Add message to chat
function addMessageToChat(speaker, message, intent = null) {
    const chatMessages = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${speaker}`;

    let speakerLabel = speaker === 'ai' ? '🤖 AI Coach' : '👤 You';

    messageDiv.innerHTML = `
        <div class="message-speaker">${speakerLabel}</div>
        <div class="message-text">${escapeHtml(message)}</div>
        ${intent ? `<div class="message-meta">${intent}</div>` : ''}
    `;

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    const chatContainer = document.getElementById('chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// End tutoring session
async function endTutoringSession() {
    if (!currentSessionId) return;

    if (!confirm('End this tutoring session?')) return;

    try {
        const response = await fetch(`${API_BASE}/tutoring/sessions/${currentSessionId}/end`, {
            method: 'POST'
        });

        const summary = await response.json();

        // Show summary
        alert(`Session Summary:

Turns: ${summary.turns}
Depth Achieved: ${summary.depth_achieved || 'N/A'}
Insights: ${summary.insights?.join(', ') || 'None'}
Areas to Review: ${summary.areas_to_review?.join(', ') || 'None'}

Great job! Keep practicing to deepen your understanding.`);

        // Reset and go back
        currentSessionId = null;
        document.getElementById('tutoring-session').style.display = 'none';
        document.getElementById('mode-selection').style.display = 'block';

        // Reload dashboard
        loadKnowledgeDashboard();

    } catch (error) {
        console.error('Error ending session:', error);
        alert('Failed to end session properly');
    }
}

// Learning Paths
function showLearningPaths() {
    document.getElementById('mode-selection').style.display = 'none';
    document.getElementById('learning-paths-view').style.display = 'block';
}

async function loadLearningPaths() {
    try {
        const response = await fetch(`${API_BASE}/tutoring/learning-paths`);
        const paths = await response.json();

        const pathsList = document.getElementById('paths-list');

        if (paths.length === 0) {
            pathsList.innerHTML = `
                <p>No learning paths yet. Learning paths provide a structured curriculum through concepts.</p>
                <button onclick="createLearningPath()" class="btn btn-primary">Create Learning Path</button>
            `;
            return;
        }

        pathsList.innerHTML = paths.map(path => `
            <div class="path-item">
                <div class="path-header">
                    <div>
                        <h3>${escapeHtml(path.name)}</h3>
                        <p>${escapeHtml(path.description || '')}</p>
                    </div>
                    <button onclick="continueOnPath(${path.id})" class="btn btn-primary">
                        Continue Learning
                    </button>
                </div>
                <div class="path-progress">
                    <div class="path-progress-fill" style="width: ${path.progress_percentage}%"></div>
                </div>
                <div class="path-stats">
                    <span>${path.progress_percentage.toFixed(0)}% Complete</span>
                    <span>${path.concepts_mastered}/${path.total_concepts} Concepts Mastered</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading learning paths:', error);
    }
}

async function createLearningPath() {
    // Get topics
    const topicsResponse = await fetch(`${API_BASE}/topics/`);
    const topics = await topicsResponse.json();

    if (topics.length === 0) {
        alert('Create a topic first in Quiz Mode!');
        return;
    }

    // Simple selection (in real app, would be a nice modal)
    const topicId = parseInt(prompt('Enter topic ID to create learning path:\n' +
        topics.map(t => `${t.id}: ${t.name}`).join('\n')));

    if (!topicId) return;

    try {
        const response = await fetch(`${API_BASE}/tutoring/learning-paths`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                topic_id: topicId,
                target_depth: 'apply'
            })
        });

        if (response.ok) {
            alert('Learning path created!');
            loadLearningPaths();
        }
    } catch (error) {
        console.error('Error creating learning path:', error);
        alert('Failed to create learning path');
    }
}

async function continueOnPath(pathId) {
    try {
        const response = await fetch(`${API_BASE}/tutoring/learning-paths/${pathId}/next-concept`);
        const nextConcept = await response.json();

        if (nextConcept.completed) {
            alert('Congratulations! You\'ve completed this learning path!');
            return;
        }

        // Start tutoring session with next concept
        currentMode = 'teaching';
        await startTutoringWithConcept(
            nextConcept.concept.id,
            nextConcept.concept.name
        );

    } catch (error) {
        console.error('Error continuing on path:', error);
        alert('Failed to get next concept');
    }
}

// Knowledge Dashboard
async function loadKnowledgeDashboard() {
    try {
        // In a real app, would fetch actual mastery data
        // For now, show placeholder
        const masteryOverview = document.getElementById('mastery-overview');

        masteryOverview.innerHTML = `
            <div class="mastery-card">
                <h3>Concepts Learning</h3>
                <div class="mastery-score">0</div>
                <div class="mastery-level-label">Start exploring!</div>
            </div>
            <div class="mastery-card">
                <h3>Average Depth</h3>
                <div class="mastery-score">-</div>
                <div class="mastery-level-label">No data yet</div>
            </div>
            <div class="mastery-card">
                <h3>Tutoring Sessions</h3>
                <div class="mastery-score">0</div>
                <div class="mastery-level-label">Begin your journey</div>
            </div>
        `;

    } catch (error) {
        console.error('Error loading knowledge dashboard:', error);
    }
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
