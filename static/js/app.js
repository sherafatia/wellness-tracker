// Wellness Tracker JavaScript

let currentUserId = null;

function updateRangeValue(fieldId) {
    const range = document.getElementById(fieldId);
    const valueSpan = document.getElementById(fieldId + '_value');
    valueSpan.textContent = range.value;
}

async function createUser() {
    const username = document.getElementById('username').value.trim();
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUserId = data.id;
            document.getElementById('user-section').style.display = 'none';
            document.getElementById('wellness-form').style.display = 'block';
            document.getElementById('reset-btn').style.display = 'block';
            
            // Check if user already has reports today
            loadUserData();
        } else {
            alert(data.error || 'Error creating user');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    }
}

async function submitWellnessReport(event) {
    event.preventDefault();
    
    const formData = {
        mood_score: parseInt(document.getElementById('mood_score').value),
        energy_level: parseInt(document.getElementById('energy_level').value),
        sleep_quality: parseInt(document.getElementById('sleep_quality').value),
        stress_level: parseInt(document.getElementById('stress_level').value),
        physical_symptoms: document.getElementById('physical_symptoms').value
    };
    
    try {
        const response = await fetch(`/api/users/${currentUserId}/reports`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show results
            document.getElementById('wellness-form').style.display = 'none';
            document.getElementById('results-section').style.display = 'block';
            
            // Display wellness score
            document.getElementById('wellness-score').textContent = data.wellness_score;
            
            // Display AI insights if available
            if (data.ai_insights) {
                document.getElementById('insights-text').textContent = data.ai_insights;
                document.getElementById('ai-insights').style.display = 'block';
            }
            
            // Load user summary and reports
            loadUserSummary();
            loadRecentReports();
        } else {
            alert(data.error || 'Error submitting report');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    }
}

async function loadUserData() {
    try {
        // Check if user has already submitted today's report
        const reportsResponse = await fetch(`/api/users/${currentUserId}/reports?days=1`);
        const reports = await reportsResponse.json();
        
        if (reports.length > 0) {
            const today = new Date().toISOString().split('T')[0];
            const hasReportToday = reports.some(report => report.report_date === today);
            
            if (hasReportToday) {
                // Show results instead of form
                document.getElementById('wellness-form').style.display = 'none';
                document.getElementById('results-section').style.display = 'block';
                
                const todayReport = reports.find(report => report.report_date === today);
                document.getElementById('wellness-score').textContent = todayReport.wellness_score;
                
                if (todayReport.ai_insights) {
                    document.getElementById('insights-text').textContent = todayReport.ai_insights;
                    document.getElementById('ai-insights').style.display = 'block';
                }
                
                loadUserSummary();
                loadRecentReports();
            }
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

async function loadUserSummary() {
    try {
        const response = await fetch(`/api/users/${currentUserId}/wellness-summary`);
        const summary = await response.json();
        
        if (response.ok) {
            const summaryHtml = `
                <div class="row">
                    <div class="col-md-3 col-sm-6">
                        <div class="metric-card">
                            <div class="metric-value">${summary.average_wellness_score}</div>
                            <div class="metric-label">Avg Wellness Score</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="metric-card">
                            <div class="metric-value">${summary.averages.mood_score}</div>
                            <div class="metric-label">Avg Mood</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="metric-card">
                            <div class="metric-value">${summary.averages.energy_level}</div>
                            <div class="metric-label">Avg Energy</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="metric-card">
                            <div class="metric-value">${summary.averages.sleep_quality}</div>
                            <div class="metric-label">Avg Sleep</div>
                        </div>
                    </div>
                </div>
                <p class="text-muted">Based on ${summary.total_reports} reports</p>
            `;
            
            document.getElementById('summary-content').innerHTML = summaryHtml;
        }
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

async function loadRecentReports() {
    try {
        const response = await fetch(`/api/users/${currentUserId}/reports?days=7`);
        const reports = await response.json();
        
        if (response.ok && reports.length > 0) {
            const reportsHtml = reports.map(report => `
                <div class="report-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${new Date(report.report_date).toLocaleDateString()}</strong>
                            <small class="text-muted ms-2">Wellness Score: ${report.wellness_score}</small>
                        </div>
                        <div class="text-end">
                            <small>Mood: ${report.mood_score} | Energy: ${report.energy_level} | Sleep: ${report.sleep_quality} | Stress: ${report.stress_level}</small>
                        </div>
                    </div>
                    ${report.physical_symptoms ? `<div class="mt-2"><small><strong>Symptoms:</strong> ${report.physical_symptoms}</small></div>` : ''}
                    ${report.ai_insights ? `<div class="mt-2"><small><strong>AI Insights:</strong> ${report.ai_insights}</small></div>` : ''}
                </div>
            `).join('');
            
            document.getElementById('recent-reports').innerHTML = reportsHtml;
        } else {
            document.getElementById('recent-reports').innerHTML = '<p class="text-muted">No recent reports found.</p>';
        }
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

function resetApp() {
    // Reset all forms and show user creation section
    currentUserId = null;
    document.getElementById('user-section').style.display = 'block';
    document.getElementById('wellness-form').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('reset-btn').style.display = 'none';
    document.getElementById('username').value = '';
    document.getElementById('wellnessReportForm').reset();
    
    // Reset range value displays
    ['mood_score', 'energy_level', 'sleep_quality', 'stress_level'].forEach(field => {
        document.getElementById(field).value = 5;
        document.getElementById(field + '_value').textContent = '5';
    });
}

// Initialize range value displays
document.addEventListener('DOMContentLoaded', function() {
    ['mood_score', 'energy_level', 'sleep_quality', 'stress_level'].forEach(field => {
        updateRangeValue(field);
    });
    
    // Add form submit handler
    document.getElementById('wellnessReportForm').addEventListener('submit', submitWellnessReport);
});