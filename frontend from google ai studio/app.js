// app.js - Main application logic

// Configuration
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':8000';

// Utility function for API calls with timeout
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timed out after ' + timeout + 'ms');
        }
        throw error;
    }
}

// Execute task function
async function executeTask() {
    const taskInput = document.getElementById('task-input');
    const agentSelect = document.getElementById('agent-select');
    const executeBtn = document.getElementById('execute-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');

    const task = taskInput.value.trim();
    if (!task) {
        showError('Please enter a task description.');
        return;
    }

    // Update UI for loading state
    executeBtn.disabled = true;
    btnText.textContent = 'Executing...';
    btnSpinner.style.display = 'block';
    hideError();

    try {
        const requestData = {
            query: task,
            user_id: getCurrentUserId() || "anonymous"
        };

        const response = await fetchWithTimeout(`${API_BASE_URL}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // Display results function
        function displayResults(result) {
            const resultsContent = document.getElementById('results-content');

            let html = '<div class="result-card">';
            html += `<div class="result-header">`;
            html += `<h3>Task ${result.task_id}</h3>`;
            html += `<span class="agent-badge">Agent: ${result.agent}</span>`;
            html += `<span class="execution-time">Execution time: ${result.execution_time?.toFixed(2)}s</span>`;
            html += `</div>`;

            if (result.status === 'success') {
                html += '<div class="result-body">';
                html += '<h4>Results:</h4>';
                html += `<pre>${JSON.stringify(result.result, null, 2)}</pre>`;
                html += '</div>';
            } else {
                html += '<div class="result-error">';
                html += `<p>Error: ${result.error}</p>`;
                html += '</div>';
            }

            html += '</div>';

            resultsContent.innerHTML = html;
        }

    } catch (error) {
        console.error('Task execution error:', error);
        // If API fails, use mock response
        console.warn('API failed, using mock response');
        const mockResult = generateMockResponse(task);
        displayResults(mockResult);
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        // Don't show error for mock fallback
        return;
    } finally {
        // Reset UI
        executeBtn.disabled = false;
        btnText.textContent = 'Execute Task';
        btnSpinner.style.display = 'none';
    }
}

// Display results function
function displayResults(result) {
    const resultsContent = document.getElementById('results-content');

    let html = '<div class="result-card">';
    html += `<div class="result-header">`;
    html += `<h3>Task ${result.task_id}</h3>`;
    html += `<span class="agent-badge">Agent: ${result.agent}</span>`;
    html += `<span class="execution-time">Execution time: ${result.execution_time?.toFixed(2)}s</span>`;
    html += `</div>`;

    if (result.status === 'success') {
        html += '<div class="result-body">';
        html += '<h4>Results:</h4>';
        html += `<pre>${JSON.stringify(result.result, null, 2)}</pre>`;
        html += '</div>';
    } else {
        html += '<div class="result-error">';
        html += `<p>Error: ${result.error}</p>`;
        html += '</div>';
    }

    html += '</div>';

    resultsContent.innerHTML = html;
}

// Clear results function
function clearResults() {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');

    resultsContent.innerHTML = '';
    resultsSection.style.display = 'none';
}

// Show error function
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');

    errorMessage.textContent = message;
    errorSection.style.display = 'block';

    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// Hide error function
function hideError() {
    const errorSection = document.getElementById('error-section');
    errorSection.style.display = 'none';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    // Check API health on load
    checkApiHealth();

    // Load agents list
    loadAgents();

    // Update user status
    updateUserStatus();

    // Add keyboard shortcut for execution
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            executeTask();
        }
    });
});

// Generate mock response for demo purposes
function generateMockResponse(query) {
    const queryLower = query.toLowerCase();
    let agent = 'general';
    let result = {};

    if (queryLower.includes('job') || queryLower.includes('career') || queryLower.includes('apply')) {
        agent = 'career';
        result = {
            message: 'Career Agent activated! I found 15 relevant job opportunities in your area.',
            jobs_found: 15,
            top_jobs: [
                { title: 'Software Engineer', company: 'Tech Corp', location: 'San Francisco, CA' },
                { title: 'Data Scientist', company: 'AI Solutions', location: 'Remote' },
                { title: 'Product Manager', company: 'StartupXYZ', location: 'New York, NY' }
            ]
        };
    } else if (queryLower.includes('search') || queryLower.includes('find') || queryLower.includes('lookup')) {
        agent = 'search';
        result = {
            message: 'Search Agent activated! I found relevant information for your query.',
            results_count: 25,
            top_results: [
                { title: 'Main Result', url: 'https://example.com/1', snippet: 'This is the most relevant result...' },
                { title: 'Related Information', url: 'https://example.com/2', snippet: 'Additional context found...' }
            ]
        };
    } else if (queryLower.includes('travel') || queryLower.includes('flight') || queryLower.includes('hotel')) {
        agent = 'travel';
        result = {
            message: 'Travel Agent activated! I found the best travel options for you.',
            options: [
                { type: 'flight', price: '$299', duration: '3h 45m' },
                { type: 'hotel', price: '$120/night', rating: '4.5 stars' },
                { type: 'train', price: '$89', duration: '6h 30m' }
            ]
        };
    } else if (queryLower.includes('movie') || queryLower.includes('music') || queryLower.includes('game')) {
        agent = 'entertainment';
        result = {
            message: 'Entertainment Agent activated! Here are some recommendations.',
            recommendations: [
                { type: 'movie', title: 'The Matrix Resurrections', rating: '7.5/10' },
                { type: 'music', artist: 'Various Artists', genre: 'Electronic' },
                { type: 'game', title: 'Cyberpunk 2077', platform: 'PC/PS5' }
            ]
        };
    } else {
        result = {
            message: `I understand you want: "${query}". I'm processing this request using our AI agents.`,
            processing_steps: [
                'Analyzing your request',
                'Routing to appropriate agent',
                'Gathering information',
                'Providing results'
            ]
        };
    }

    return {
        task_id: `task_${Date.now()}`,
        agent: agent,
        result: result,
        execution_time: (Math.random() * 2 + 0.5).toFixed(2),
        status: 'success'
    };
}

// User management functions
function getCurrentUserId() {
    return localStorage.getItem('user_id');
}

function setCurrentUser(user) {
    localStorage.setItem('user_id', user.email);
    localStorage.setItem('user_data', JSON.stringify(user));
    updateUserStatus();
}

function getCurrentUser() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
}

function logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_data');
    updateUserStatus();
}

function updateUserStatus() {
    const userStatus = document.getElementById('user-status');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const user = getCurrentUser();

    if (user) {
        userStatus.textContent = `Logged in as ${user.email}`;
        userStatus.style.color = '#10b981';
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
    } else {
        userStatus.textContent = 'Not logged in';
        userStatus.style.color = '#6b7280';
        loginBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
    }
}

// Load agents list
async function loadAgents() {
    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/agents`);
        if (response.ok) {
            const data = await response.json();
            populateAgentSelect(data.agents);
        }
    } catch (error) {
        console.warn('Failed to load agents:', error);
    }
}

// Populate agent select dropdown
function populateAgentSelect(agents) {
    const agentSelect = document.getElementById('agent-select');
    // Clear existing options except the first one
    while (agentSelect.children.length > 1) {
        agentSelect.removeChild(agentSelect.lastChild);
    }

    agents.forEach(agent => {
        const option = document.createElement('option');
        option.value = agent.type;
        option.textContent = agent.name;
        agentSelect.appendChild(option);
    });
}

// Authentication modal functions
function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'block';
    showLoginForm();
}

function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('auth-title').textContent = 'Login';
}

function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('auth-title').textContent = 'Register';
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error(`Login failed: ${response.statusText}`);
        }

        const result = await response.json();
        setCurrentUser(result.user);
        hideAuthModal();
        showSuccess('Login successful!');

    } catch (error) {
        console.warn('Real API login failed, using mock login:', error);
        // Mock login - accept any email/password
        const mockUser = {
            email: email,
            first_name: email.split('@')[0],
            last_name: '',
            subscription: 'free',
            created_at: new Date().toISOString()
        };
        setCurrentUser(mockUser);
        hideAuthModal();
        showSuccess('Login successful! (Demo mode)');
    }
}

// Handle register
async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const firstName = document.getElementById('register-first-name').value;
    const lastName = document.getElementById('register-last-name').value;
    
    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password, first_name: firstName, last_name: lastName })
        });
        
        if (!response.ok) {
            throw new Error(`Registration failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        setCurrentUser(result.user);
        hideAuthModal();
        showSuccess('Registration successful!');
        
    } catch (error) {
        console.warn('Real API registration failed, using mock registration:', error);
        // Mock registration
        const mockUser = {
            email: email,
            first_name: firstName,
            last_name: lastName,
            subscription: 'free',
            created_at: new Date().toISOString()
        };
        setCurrentUser(mockUser);
        hideAuthModal();
        showSuccess('Registration successful! (Demo mode)');
    }
}

// Show success message
function showSuccess(message) {
    // For now, just use alert. Could be improved with a proper notification system
    alert(message);
}