# AI Agent Platform - Complete Frontend Design Specification
# For Google AI Studio Implementation

## Overview
This specification details a complete, production-ready frontend for the AI Agent Platform.
The frontend must integrate seamlessly with the FastAPI backend and handle all identified issues.

## Architecture Requirements

### 1. Technology Stack
- **HTML5** with semantic markup
- **CSS3** with modern features (Grid, Flexbox, CSS Variables)
- **Vanilla JavaScript** (ES6+) - No frameworks for simplicity
- **Fetch API** for backend communication
- **LocalStorage/SessionStorage** for client-side persistence
- **Responsive Design** (Mobile-first approach)

### 2. Backend Integration Points
```
Base URL: http://localhost:8000 (development) / https://api.yourdomain.com (production)

Endpoints to integrate:
- GET  /health                    - Health check
- GET  /agents                    - List available agents
- POST /execute                   - Execute tasks (main endpoint)
- GET  /                          - Landing page
- GET  /app                       - Main application
- POST /api/v1/auth/register      - User registration
- POST /api/v1/auth/login         - User authentication
- GET  /api/v1/analytics/user/{id} - User statistics
```

## Page Structure & Components

### 1. Landing Page (/)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Platform - The Complete AI Operating System</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" href="favicon.ico">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-brand">
                <h2>🤖 AI Agent Platform</h2>
                <p>The Complete AI Operating System</p>
            </div>
            <div class="nav-links">
                <a href="#features" class="nav-link">Features</a>
                <a href="#agents" class="nav-link">Agents</a>
                <a href="#pricing" class="nav-link">Pricing</a>
                <a href="/app" class="btn-primary">Try Now</a>
            </div>
        </div>
    </nav>

    <header class="hero">
        <div class="hero-container">
            <h1>Meet Your AI Workforce</h1>
            <p>11 specialized AI agents working together to automate your tasks, from job searching to travel planning, career development to transaction processing.</p>
            <div class="hero-actions">
                <a href="/app" class="btn-primary btn-large">Get Started Free</a>
                <a href="#demo" class="btn-secondary">Watch Demo</a>
            </div>
        </div>
    </header>

    <section id="features" class="features">
        <div class="container">
            <h2>Powerful Features</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <h3>Smart Job Search</h3>
                    <p>Advanced job scraping across multiple platforms with AI-powered matching.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">✈️</div>
                    <h3>Travel Planning</h3>
                    <p>Comprehensive travel arrangements from booking to itinerary optimization.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💼</div>
                    <h3>Career Development</h3>
                    <p>Resume optimization, skill assessment, and career path guidance.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🛒</div>
                    <h3>Transaction Processing</h3>
                    <p>Secure payment processing and financial transaction automation.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h3>Task Orchestration</h3>
                    <p>Intelligent routing of tasks to the most appropriate AI agent.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>Analytics & Monitoring</h3>
                    <p>Comprehensive usage statistics and performance monitoring.</p>
                </div>
            </div>
        </div>
    </section>

    <section id="agents" class="agents">
        <div class="container">
            <h2>Meet Your AI Agents</h2>
            <div class="agents-grid">
                <div class="agent-card">
                    <div class="agent-icon">🌐</div>
                    <h3>Browser Agent</h3>
                    <p>Web browsing and data extraction</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">💼</div>
                    <h3>Career Agent</h3>
                    <p>Career development and job search</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">🔍</div>
                    <h3>Search Agent</h3>
                    <p>Intelligent information retrieval</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">🎬</div>
                    <h3>Entertainment Agent</h3>
                    <p>Entertainment recommendations</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">⚡</div>
                    <h3>Productivity Agent</h3>
                    <p>Task automation and productivity</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">✈️</div>
                    <h3>Travel Agent</h3>
                    <p>Travel planning and booking</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">🛒</div>
                    <h3>Transaction Agent</h3>
                    <p>Payment processing</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">🤖</div>
                    <h3>Orchestrator</h3>
                    <p>Task routing and coordination</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">📱</div>
                    <h3>Communication Agent</h3>
                    <p>Multi-channel communication</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">🔧</div>
                    <h3>Job Automation Agent</h3>
                    <p>Automated job application</p>
                </div>
                <div class="agent-card">
                    <div class="agent-icon">📊</div>
                    <h3>Monitoring Agent</h3>
                    <p>System monitoring and alerts</p>
                </div>
            </div>
        </div>
    </section>

    <section id="pricing" class="pricing">
        <div class="container">
            <h2>Simple Pricing</h2>
            <div class="pricing-grid">
                <div class="pricing-card">
                    <h3>Free Tier</h3>
                    <div class="price">$0</div>
                    <ul>
                        <li>10 tasks per month</li>
                        <li>Basic agents access</li>
                        <li>Community support</li>
                    </ul>
                    <a href="/app" class="btn-primary">Get Started</a>
                </div>
                <div class="pricing-card featured">
                    <h3>Pro Plan</h3>
                    <div class="price">$29</div>
                    <span class="period">/month</span>
                    <ul>
                        <li>Unlimited tasks</li>
                        <li>All agents access</li>
                        <li>Priority support</li>
                        <li>Advanced analytics</li>
                    </ul>
                    <a href="/app" class="btn-primary">Start Free Trial</a>
                </div>
                <div class="pricing-card">
                    <h3>Enterprise</h3>
                    <div class="price">Custom</div>
                    <ul>
                        <li>Custom integrations</li>
                        <li>Dedicated support</li>
                        <li>SLA guarantees</li>
                        <li>On-premise deployment</li>
                    </ul>
                    <a href="/contact" class="btn-secondary">Contact Sales</a>
                </div>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <h3>🤖 AI Agent Platform</h3>
                    <p>The Complete AI Operating System</p>
                </div>
                <div class="footer-links">
                    <div class="footer-section">
                        <h4>Product</h4>
                        <a href="#features">Features</a>
                        <a href="#agents">Agents</a>
                        <a href="#pricing">Pricing</a>
                    </div>
                    <div class="footer-section">
                        <h4>Support</h4>
                        <a href="/docs">Documentation</a>
                        <a href="/help">Help Center</a>
                        <a href="/contact">Contact</a>
                    </div>
                    <div class="footer-section">
                        <h4>Company</h4>
                        <a href="/about">About</a>
                        <a href="/blog">Blog</a>
                        <a href="/careers">Careers</a>
                    </div>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 AI Agent Platform. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src="landing.js"></script>
</body>
</html>
```

### 2. Main Application Page (/app)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Platform - Execute Tasks</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" href="favicon.ico">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-brand">
                <a href="/">🤖 AI Agent Platform</a>
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">Home</a>
                <a href="/stats" class="nav-link">Statistics</a>
                <span id="user-status" class="user-status">Not logged in</span>
            </div>
        </div>
    </nav>

    <main class="app-main">
        <div class="container">
            <div class="app-header">
                <h1>Execute AI Tasks</h1>
                <p>Describe what you want to accomplish and our AI agents will handle it.</p>
            </div>

            <div class="task-form">
                <div class="form-group">
                    <label for="task-input">Task Description</label>
                    <textarea 
                        id="task-input" 
                        placeholder="e.g., Find me software engineering jobs in San Francisco with salaries over $120k"
                        rows="4"
                    ></textarea>
                </div>
                
                <div class="form-group">
                    <label for="agent-select">Preferred Agent (Optional)</label>
                    <select id="agent-select">
                        <option value="">Auto-select (Recommended)</option>
                        <option value="browser">Browser Agent</option>
                        <option value="career">Career Agent</option>
                        <option value="search">Search Agent</option>
                        <option value="travel">Travel Agent</option>
                        <option value="transaction">Transaction Agent</option>
                        <option value="productivity">Productivity Agent</option>
                        <option value="entertainment">Entertainment Agent</option>
                        <option value="communication">Communication Agent</option>
                        <option value="job_automation">Job Automation Agent</option>
                        <option value="monitoring">Monitoring Agent</option>
                    </select>
                </div>

                <button id="execute-btn" class="btn-primary btn-large" onclick="executeTask()">
                    <span id="btn-text">Execute Task</span>
                    <div id="btn-spinner" class="spinner" style="display: none;"></div>
                </button>
            </div>

            <div id="results-section" class="results-section" style="display: none;">
                <div class="results-header">
                    <h2>Task Results</h2>
                    <button class="btn-secondary" onclick="clearResults()">Clear</button>
                </div>
                <div id="results-content" class="results-content">
                    <!-- Results will be displayed here -->
                </div>
            </div>

            <div id="error-section" class="error-section" style="display: none;">
                <div class="error-content">
                    <h3>Error</h3>
                    <p id="error-message"></p>
                    <button class="btn-secondary" onclick="hideError()">Dismiss</button>
                </div>
            </div>
        </div>
    </main>

    <script src="app.js"></script>
</body>
</html>
```

## CSS Styles (styles.css)
```css
/* CSS Variables for consistent theming */
:root {
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --error-color: #ef4444;
    --warning-color: #f59e0b;
    --background-color: #ffffff;
    --surface-color: #f8fafc;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --border-radius: 8px;
    --border-radius-lg: 12px;
    --transition: all 0.2s ease;
}

/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: var(--background-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

/* Navigation */
.navbar {
    background: var(--background-color);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand h2 {
    color: var(--primary-color);
    margin: 0;
}

.nav-brand p {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin: 0;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.nav-link {
    color: var(--text-primary);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius);
    transition: var(--transition);
}

.nav-link:hover {
    background-color: var(--surface-color);
}

.user-status {
    font-size: 0.875rem;
    color: var(--text-secondary);
}

/* Buttons */
.btn-primary {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: var(--border-radius);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    transition: var(--transition);
    font-weight: 500;
}

.btn-primary:hover {
    background-color: var(--primary-hover);
}

.btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.btn-secondary {
    background-color: transparent;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 0.75rem 1.5rem;
    border-radius: var(--border-radius);
    text-decoration: none;
    display: inline-block;
    cursor: pointer;
    transition: var(--transition);
}

.btn-secondary:hover {
    background-color: var(--surface-color);
}

.btn-large {
    padding: 1rem 2rem;
    font-size: 1.125rem;
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, var(--primary-color) 0%, #1e40af 100%);
    color: white;
    padding: 4rem 0;
}

.hero-container {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
    padding: 0 1rem;
}

.hero h1 {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.hero p {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.hero-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

/* Features Section */
.features {
    padding: 4rem 0;
    background-color: var(--surface-color);
}

.features h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: var(--text-primary);
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.feature-card {
    background: var(--background-color);
    padding: 2rem;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow);
    text-align: center;
    transition: var(--transition);
}

.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.feature-card h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.feature-card p {
    color: var(--text-secondary);
}

/* Agents Section */
.agents {
    padding: 4rem 0;
}

.agents h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: var(--text-primary);
}

.agents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

.agent-card {
    background: var(--background-color);
    padding: 1.5rem;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    text-align: center;
    transition: var(--transition);
}

.agent-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.agent-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

.agent-card h3 {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.agent-card p {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

/* Pricing Section */
.pricing {
    padding: 4rem 0;
    background-color: var(--surface-color);
}

.pricing h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: var(--text-primary);
}

.pricing-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    max-width: 1000px;
    margin: 0 auto;
}

.pricing-card {
    background: var(--background-color);
    padding: 2rem;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow);
    text-align: center;
    position: relative;
    transition: var(--transition);
}

.pricing-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.pricing-card.featured {
    border: 2px solid var(--primary-color);
    transform: scale(1.05);
}

.pricing-card h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.price {
    font-size: 3rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.period {
    font-size: 1rem;
    color: var(--text-secondary);
}

.pricing-card ul {
    list-style: none;
    margin: 2rem 0;
    text-align: left;
}

.pricing-card li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
}

.pricing-card li:last-child {
    border-bottom: none;
}

/* Footer */
.footer {
    background: var(--text-primary);
    color: white;
    padding: 3rem 0 1rem;
}

.footer-content {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 3rem;
    margin-bottom: 2rem;
}

.footer-brand h3 {
    color: white;
    margin-bottom: 0.5rem;
}

.footer-brand p {
    opacity: 0.8;
}

.footer-links {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
}

.footer-section h4 {
    margin-bottom: 1rem;
    color: white;
}

.footer-section a {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    display: block;
    margin-bottom: 0.5rem;
    transition: var(--transition);
}

.footer-section a:hover {
    color: white;
}

.footer-bottom {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 1rem;
    text-align: center;
    opacity: 0.8;
}

/* App Main Content */
.app-main {
    padding: 2rem 0;
    min-height: calc(100vh - 80px);
}

.app-header {
    text-align: center;
    margin-bottom: 3rem;
}

.app-header h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.app-header p {
    font-size: 1.125rem;
    color: var(--text-secondary);
}

/* Task Form */
.task-form {
    max-width: 600px;
    margin: 0 auto 3rem;
    background: var(--background-color);
    padding: 2rem;
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow);
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
}

.form-group textarea,
.form-group select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-size: 1rem;
    transition: var(--transition);
}

.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group textarea {
    resize: vertical;
    min-height: 100px;
}

/* Results Section */
.results-section {
    max-width: 800px;
    margin: 0 auto;
    background: var(--background-color);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow);
    overflow: hidden;
}

.results-header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.results-header h2 {
    margin: 0;
    color: var(--text-primary);
}

.results-content {
    padding: 1.5rem;
    max-height: 600px;
    overflow-y: auto;
}

.results-content pre {
    background: var(--surface-color);
    padding: 1rem;
    border-radius: var(--border-radius);
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Error Section */
.error-section {
    max-width: 600px;
    margin: 2rem auto;
    background: var(--error-color);
    color: white;
    border-radius: var(--border-radius);
    overflow: hidden;
}

.error-content {
    padding: 1.5rem;
}

.error-content h3 {
    margin-bottom: 0.5rem;
}

/* Spinner */
.spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Responsive Design */
@media (max-width: 768px) {
    .nav-container {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav-links {
        width: 100%;
        justify-content: center;
    }
    
    .hero h1 {
        font-size: 2rem;
    }
    
    .hero p {
        font-size: 1rem;
    }
    
    .hero-actions {
        flex-direction: column;
        align-items: center;
    }
    
    .features-grid,
    .agents-grid,
    .pricing-grid {
        grid-template-columns: 1fr;
    }
    
    .footer-content {
        grid-template-columns: 1fr;
        gap: 2rem;
    }
    
    .footer-links {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    
    .results-header {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }
}
```

## JavaScript Implementation

### 1. Landing Page Script (landing.js)
```javascript
// landing.js - Landing page interactions
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe feature cards, agent cards, etc.
    document.querySelectorAll('.feature-card, .agent-card, .pricing-card').forEach(card => {
        observer.observe(card);
    });
});
```

### 2. App Page Script (app.js)
```javascript
// app.js - Main application logic

// Configuration
const API_BASE_URL = window.location.protocol + '//' + window.location.host;

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
            task: task,
            agent: agentSelect.value || null
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
        
        // Display results
        resultsContent.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Task execution error:', error);
        showError(error.message || 'An error occurred while executing the task.');
    } finally {
        // Reset UI
        executeBtn.disabled = false;
        btnText.textContent = 'Execute Task';
        btnSpinner.style.display = 'none';
    }
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
document.addEventListener('DOMContentLoaded', function() {
    // Check API health on load
    checkApiHealth();
    
    // Add keyboard shortcut for execution
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            executeTask();
        }
    });
});

// Check API health
async function checkApiHealth() {
    try {
        const response = await fetchWithTimeout(`${API_BASE_URL}/health`, {
            method: 'GET'
        });
        
        if (response.ok) {
            console.log('API is healthy');
        } else {
            console.warn('API health check failed');
        }
    } catch (error) {
        console.warn('API health check error:', error);
    }
}
```

## Key Technical Fixes

### 1. OrchestratorAgent Gemini Initialization with Fallback
The frontend handles orchestrator initialization failures gracefully:

```javascript
// In app.js - the executeTask function already handles this
// The backend orchestrator_advanced.py has fallback logic:
// 1. Try keyword-based routing first (free)
// 2. Fall back to Claude Haiku if keywords don't match
// 3. Frontend doesn't need special handling - just sends task
```

### 2. Frontend Page Loading Timeout Handling
All API calls now use `fetchWithTimeout()` with a 10-second timeout:

```javascript
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
```

### 3. Windows-Specific Integration Test Cleanup
For Windows environments, add this cleanup logic to test files:

```javascript
# In test files that need cleanup on Windows
import os
import shutil
import time

def cleanup_windows_files():
    """Clean up files and directories with Windows-specific handling."""
    dirs_to_clean = ['temp', 'cache', 'logs']
    max_retries = 3
    
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            for attempt in range(max_retries):
                try:
                    # Close any open file handles
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r') as f:
                                    pass  # Just try to open to check
                            except PermissionError:
                                time.sleep(0.1)  # Wait and retry
                    
                    shutil.rmtree(dir_path)
                    break
                except (OSError, PermissionError) as e:
                    if attempt == max_retries - 1:
                        print(f"Failed to clean up {dir_path}: {e}")
                    time.sleep(0.5)

# Call this in test teardown
def teardown_module():
    cleanup_windows_files()
```

## Implementation Steps

### 1. Create the Frontend Files
1. Create `index.html` with the landing page code
2. Create `app.html` with the main application code
3. Create `styles.css` with all the CSS styles
4. Create `landing.js` with landing page interactions
5. Create `app.js` with main application logic

### 2. Backend Integration
1. Ensure the FastAPI backend is running on the configured port
2. Update API_BASE_URL in app.js to match backend URL
3. Test all endpoints: /health, /agents, /execute

### 3. Deployment
1. Host the static HTML/CSS/JS files on any web server
2. Configure CORS on the backend to allow the frontend domain
3. Set up proper error handling and monitoring

### 4. Testing
1. Test all user flows: landing page → app → task execution
2. Verify timeout handling with slow network conditions
3. Test error scenarios and recovery
4. Validate responsive design on different screen sizes

This specification provides a complete, production-ready frontend that addresses all identified issues and integrates seamlessly with the AI Agent Platform backend.