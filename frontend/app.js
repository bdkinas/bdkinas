// API base URL
const API_BASE = 'http://localhost:8000';

// Global state
let currentSession = null;
let currentQuestions = [];
let currentQuestionIndex = 0;
let sessionAnswers = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadTopics();

    // Set up form handlers
    document.getElementById('create-topic-form').addEventListener('submit', handleCreateTopic);
});

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

// Load user stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/reviews/stats`);
        const stats = await response.json();

        document.getElementById('total-topics').textContent = stats.total_topics;
        document.getElementById('questions-due').textContent = stats.questions_due_today;
        document.getElementById('avg-accuracy').textContent = `${stats.average_accuracy}%`;
        document.getElementById('streak-days').textContent = stats.streak_days;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load topics
async function loadTopics() {
    try {
        const response = await fetch(`${API_BASE}/topics/`);
        const topics = await response.json();

        const topicsList = document.getElementById('topics-list');
        if (topics.length === 0) {
            topicsList.innerHTML = '<p class="text-center">No topics yet. Create your first topic above!</p>';
            return;
        }

        topicsList.innerHTML = topics.map(topic => `
            <div class="topic-item">
                <div class="topic-header">
                    <div>
                        <div class="topic-title">${escapeHtml(topic.name)}</div>
                        <div class="topic-meta">
                            ${topic.total_questions} questions |
                            Mastery: ${Math.round(topic.mastery_level * 100)}%
                        </div>
                    </div>
                </div>
                <p>${escapeHtml(topic.description)}</p>
                <div class="topic-actions">
                    <button onclick="generateQuestions(${topic.id})" class="btn btn-primary">
                        Generate AI Questions
                    </button>
                    <button onclick="deleteTopic(${topic.id})" class="btn btn-danger">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading topics:', error);
    }
}

// Create topic
async function handleCreateTopic(e) {
    e.preventDefault();

    const name = document.getElementById('topic-name').value;
    const description = document.getElementById('topic-description').value;

    try {
        const response = await fetch(`${API_BASE}/topics/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });

        if (response.ok) {
            document.getElementById('create-topic-form').reset();
            loadTopics();
            loadStats();
            alert('Topic created successfully!');
        }
    } catch (error) {
        console.error('Error creating topic:', error);
        alert('Failed to create topic');
    }
}

// Generate questions for a topic
async function generateQuestions(topicId) {
    const numQuestions = prompt('How many questions to generate?', '5');
    if (!numQuestions) return;

    const difficulty = prompt('Difficulty level? (easy/medium/hard)', 'medium');

    try {
        const response = await fetch(`${API_BASE}/topics/${topicId}/generate-questions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                num_questions: parseInt(numQuestions),
                difficulty: difficulty
            })
        });

        if (response.ok) {
            const result = await response.json();
            alert(result.message);
            loadTopics();
            loadStats();
        } else {
            alert('Failed to generate questions. Make sure ANTHROPIC_API_KEY is set in backend/.env');
        }
    } catch (error) {
        console.error('Error generating questions:', error);
        alert('Failed to generate questions');
    }
}

// Delete topic
async function deleteTopic(topicId) {
    if (!confirm('Are you sure you want to delete this topic and all its questions?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/topics/${topicId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadTopics();
            loadStats();
        }
    } catch (error) {
        console.error('Error deleting topic:', error);
    }
}

// Start learning session
async function startSession() {
    const sessionType = document.getElementById('session-type').value;
    const maxQuestions = parseInt(document.getElementById('max-questions').value);

    try {
        // Create session
        const sessionResponse = await fetch(`${API_BASE}/reviews/start-session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_type: sessionType,
                max_questions: maxQuestions
            })
        });

        currentSession = await sessionResponse.json();

        // Get questions
        const questionsResponse = await fetch(
            `${API_BASE}/reviews/next-questions/${currentSession.id}?limit=${maxQuestions}`
        );
        currentQuestions = await questionsResponse.json();

        if (currentQuestions.length === 0) {
            alert('No questions available. Create some topics and generate questions first!');
            return;
        }

        // Reset state
        currentQuestionIndex = 0;
        sessionAnswers = [];

        // Show session tab
        showTab('session');
        document.querySelectorAll('.tab-btn').forEach((btn, i) => {
            btn.classList.toggle('active', i === 2);
        });

        // Display first question
        displayQuestion();
    } catch (error) {
        console.error('Error starting session:', error);
        alert('Failed to start session');
    }
}

// Display current question
function displayQuestion() {
    if (currentQuestionIndex >= currentQuestions.length) {
        endSession();
        return;
    }

    const question = currentQuestions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / currentQuestions.length) * 100;

    let questionHtml = `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${progress}%"></div>
        </div>
        <p style="text-align: center; margin-bottom: 20px;">
            Question ${currentQuestionIndex + 1} of ${currentQuestions.length}
        </p>
        <div class="question-card">
            <div class="question-meta">
                <span>Topic: ${escapeHtml(question.topic_name)}</span>
                <span>Difficulty: ${question.difficulty}</span>
                <span>Type: ${question.question_type}</span>
            </div>
            <div class="question-text">${escapeHtml(question.question_text)}</div>
    `;

    if (question.question_type === 'multiple_choice' && question.options) {
        questionHtml += '<div class="options">';
        question.options.forEach((option, i) => {
            questionHtml += `
                <button class="option-btn" onclick="selectOption(${i}, '${escapeHtml(option)}')">
                    ${escapeHtml(option)}
                </button>
            `;
        });
        questionHtml += '</div>';
    } else {
        questionHtml += `
            <textarea id="answer-input" class="answer-input"
                placeholder="Type your answer here..."></textarea>
            <button onclick="submitAnswer()" class="btn btn-primary">Submit Answer</button>
        `;
    }

    questionHtml += '</div>';

    document.getElementById('session-container').innerHTML = questionHtml;
}

// Select multiple choice option
function selectOption(optionIndex, optionText) {
    // Show confidence slider
    const question = currentQuestions[currentQuestionIndex];

    const feedbackHtml = `
        <div class="question-card">
            <div class="question-text">${escapeHtml(question.question_text)}</div>
            <p><strong>Your answer:</strong> ${escapeHtml(optionText)}</p>

            <div style="margin: 20px 0;">
                <label>Was your answer correct?</label>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button onclick="recordAnswer('${escapeHtml(optionText)}', true)"
                            class="btn btn-success">Correct</button>
                    <button onclick="recordAnswer('${escapeHtml(optionText)}', false)"
                            class="btn btn-danger">Incorrect</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('session-container').innerHTML = feedbackHtml;
}

// Submit open-ended answer
function submitAnswer() {
    const answer = document.getElementById('answer-input').value.trim();
    if (!answer) {
        alert('Please enter an answer');
        return;
    }

    const question = currentQuestions[currentQuestionIndex];

    const feedbackHtml = `
        <div class="question-card">
            <div class="question-text">${escapeHtml(question.question_text)}</div>
            <p><strong>Your answer:</strong> ${escapeHtml(answer)}</p>

            <div style="margin: 20px 0;">
                <label>Was your answer correct?</label>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button onclick="recordAnswer('${escapeHtml(answer)}', true)"
                            class="btn btn-success">Correct</button>
                    <button onclick="recordAnswer('${escapeHtml(answer)}', false)"
                            class="btn btn-danger">Incorrect</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('session-container').innerHTML = feedbackHtml;
}

// Record answer and move to next question
async function recordAnswer(userAnswer, isCorrect) {
    const question = currentQuestions[currentQuestionIndex];

    // Show confidence slider
    const confidenceHtml = `
        <div class="question-card">
            <p style="margin-bottom: 20px;">
                ${isCorrect ? 'Correct!' : 'Keep practicing!'}
            </p>
            <div class="confidence-slider">
                <label>How confident were you? (1-5)</label>
                <input type="range" id="confidence" min="1" max="5" value="${isCorrect ? 4 : 2}">
                <div class="confidence-labels">
                    <span>Not at all</span>
                    <span>Very confident</span>
                </div>
            </div>
            <button onclick="submitConfidence('${escapeHtml(userAnswer)}', ${isCorrect})"
                    class="btn btn-primary">Next Question</button>
        </div>
    `;

    document.getElementById('session-container').innerHTML = confidenceHtml;
}

// Submit confidence and move to next
async function submitConfidence(userAnswer, isCorrect) {
    const confidence = parseInt(document.getElementById('confidence').value);
    const question = currentQuestions[currentQuestionIndex];

    try {
        await fetch(`${API_BASE}/reviews/submit-answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSession.id,
                question_id: question.id,
                user_answer: userAnswer,
                is_correct: isCorrect,
                confidence: confidence
            })
        });

        sessionAnswers.push({
            question: question.question_text,
            isCorrect: isCorrect,
            confidence: confidence
        });

        currentQuestionIndex++;
        displayQuestion();
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Failed to submit answer');
    }
}

// End session
async function endSession() {
    try {
        const response = await fetch(
            `${API_BASE}/reviews/end-session/${currentSession.id}`,
            { method: 'POST' }
        );
        const summary = await response.json();

        const summaryHtml = `
            <div class="session-summary">
                <h2>Session Complete!</h2>
                <div class="summary-stats">
                    <div class="stat-item">
                        <div class="stat-value">${summary.total_questions}</div>
                        <div class="stat-label">Questions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${summary.correct_answers}</div>
                        <div class="stat-label">Correct</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${summary.accuracy}%</div>
                        <div class="stat-label">Accuracy</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${Math.round(summary.duration_minutes)}</div>
                        <div class="stat-label">Minutes</div>
                    </div>
                </div>
                <p style="margin: 20px 0;">
                    You reviewed questions from ${summary.topics_covered} different topic(s).
                    This interleaving strengthens your memory!
                </p>
                <button onclick="showTab('review')" class="btn btn-primary">
                    Start Another Session
                </button>
            </div>
        `;

        document.getElementById('session-container').innerHTML = summaryHtml;

        // Refresh stats
        loadStats();

        // Reset state
        currentSession = null;
        currentQuestions = [];
        currentQuestionIndex = 0;
        sessionAnswers = [];

    } catch (error) {
        console.error('Error ending session:', error);
    }
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
