const API_BASE = '/api/portal';
let currentTab = 'dashboard';
let currentCorrectionTab = 'pending';
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCorrectionTabs();
    initEventListeners();
    loadDashboard();
    startAutoRefresh();
});

function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            switchTab(tabId);
        });
    });
}

function initCorrectionTabs() {
    document.querySelectorAll('.correction-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.correction-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCorrectionTab = tab.dataset.correctionTab;
            loadCorrections();
        });
    });
}

function initEventListeners() {
    document.getElementById('add-policy-btn')?.addEventListener('click', showAddPolicyModal);
    document.getElementById('new-request-btn')?.addEventListener('click', showNewRequestModal);
    document.getElementById('activity-filter')?.addEventListener('change', loadActivity);
    document.getElementById('activity-search')?.addEventListener('input', debounce(loadActivity, 300));
}

function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`.tab[data-tab="${tabId}"]`)?.classList.add('active');
    document.getElementById(tabId)?.classList.add('active');
    
    switch (tabId) {
        case 'dashboard': loadDashboard(); break;
        case 'activity': loadActivity(); break;
        case 'corrections': loadCorrections(); break;
        case 'policies': loadPolicies(); break;
        case 'access': loadAccessRequests(); break;
    }
}

function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        if (currentTab === 'dashboard') {
            loadDashboard();
        }
    }, 30000);
}

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        updateConnectionStatus(true);
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        updateConnectionStatus(false);
        throw error;
    }
}

function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('connection-status');
    if (connected) {
        statusDot.classList.remove('disconnected');
    } else {
        statusDot.classList.add('disconnected');
    }
}

async function loadDashboard() {
    try {
        const [health, stats, metrics] = await Promise.all([
            apiCall('/health'),
            apiCall('/stats'),
            apiCall('/metrics')
        ]);
        
        document.getElementById('api-version').textContent = `v${health.version || '1.0.0'}`;
        
        document.getElementById('stat-sessions').textContent = stats.active_sessions || 0;
        document.getElementById('stat-corrections').textContent = stats.corrections_today || 0;
        document.getElementById('stat-accuracy').textContent = `${Math.round(stats.cle_accuracy * 100) || 0}%`;
        document.getElementById('stat-policies').textContent = stats.active_policies || 0;
        
        const healthList = document.getElementById('health-list');
        healthList.innerHTML = Object.entries(health.dependencies || {}).map(([name, status]) => `
            <div class="health-item">
                <span class="health-label">${name}</span>
                <span class="health-status ${status === 'healthy' ? 'healthy' : status === 'degraded' ? 'degraded' : 'unhealthy'}">${status}</span>
            </div>
        `).join('');
        
        const activityFeed = document.getElementById('recent-activity');
        if (metrics.recent_activity && metrics.recent_activity.length > 0) {
            activityFeed.innerHTML = metrics.recent_activity.map(activity => `
                <div class="activity-item">
                    <span>${activity.type}: ${activity.description}</span>
                    <span>${formatTime(activity.timestamp)}</span>
                </div>
            `).join('');
        } else {
            activityFeed.innerHTML = '<div class="activity-item">No recent activity</div>';
        }
        
        renderChart(metrics.request_volume || []);
        
    } catch (error) {
        console.error('Dashboard load failed:', error);
    }
}

function renderChart(data) {
    const chartBars = document.getElementById('chart-bars');
    if (!chartBars || !data.length) {
        if (chartBars) {
            chartBars.innerHTML = '<div class="empty-state">No data available</div>';
        }
        return;
    }
    
    const maxValue = Math.max(...data.map(d => d.count), 1);
    
    chartBars.innerHTML = data.map(d => {
        const height = (d.count / maxValue) * 100;
        return `<div class="chart-bar" style="height: ${height}%" title="${d.label}: ${d.count}"></div>`;
    }).join('');
}

async function loadActivity() {
    try {
        const filter = document.getElementById('activity-filter')?.value || 'all';
        const search = document.getElementById('activity-search')?.value || '';
        
        const data = await apiCall(`/activity?filter=${filter}&search=${encodeURIComponent(search)}`);
        
        const tbody = document.getElementById('activity-table');
        if (data.activities && data.activities.length > 0) {
            tbody.innerHTML = data.activities.map(activity => `
                <tr>
                    <td>${formatTime(activity.timestamp)}</td>
                    <td><span class="status-badge ${activity.type}">${activity.type}</span></td>
                    <td>${activity.agent_id || 'N/A'}</td>
                    <td>${activity.details || '-'}</td>
                    <td><span class="status-badge ${activity.status}">${activity.status}</span></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5">No activity found</td></tr>';
        }
    } catch (error) {
        console.error('Activity load failed:', error);
    }
}

async function loadCorrections() {
    try {
        const data = await apiCall(`/corrections?status=${currentCorrectionTab}`);
        
        document.getElementById('pending-count').textContent = data.counts?.pending || 0;
        document.getElementById('approved-count').textContent = data.counts?.approved || 0;
        document.getElementById('rejected-count').textContent = data.counts?.rejected || 0;
        
        const list = document.getElementById('corrections-list');
        if (data.corrections && data.corrections.length > 0) {
            list.innerHTML = data.corrections.map(correction => `
                <div class="correction-item">
                    <div class="correction-info">
                        <div class="correction-tool">
                            <span class="tool-from">${correction.original_tool}</span>
                            <span class="tool-arrow">→</span>
                            <span class="tool-to">${correction.corrected_tool}</span>
                        </div>
                        <div class="correction-meta">
                            Confidence: ${Math.round(correction.confidence * 100)}% | 
                            Occurrences: ${correction.occurrence_count} |
                            ${formatTime(correction.created_at)}
                        </div>
                    </div>
                    ${currentCorrectionTab === 'pending' ? `
                        <div class="correction-actions">
                            <button class="btn btn-primary btn-sm" onclick="approveCorrection('${correction.id}')">Approve</button>
                            <button class="btn btn-secondary btn-sm" onclick="rejectCorrection('${correction.id}')">Reject</button>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            list.innerHTML = '<div class="empty-state">No corrections in this category</div>';
        }
    } catch (error) {
        console.error('Corrections load failed:', error);
    }
}

async function approveCorrection(id) {
    try {
        await apiCall(`/corrections/${id}/approve`, { method: 'POST' });
        loadCorrections();
    } catch (error) {
        console.error('Approve failed:', error);
    }
}

async function rejectCorrection(id) {
    try {
        await apiCall(`/corrections/${id}/reject`, { method: 'POST' });
        loadCorrections();
    } catch (error) {
        console.error('Reject failed:', error);
    }
}

async function loadPolicies() {
    try {
        const data = await apiCall('/policies');
        
        const tbody = document.getElementById('policies-table');
        if (data.policies && data.policies.length > 0) {
            tbody.innerHTML = data.policies.map(policy => `
                <tr>
                    <td>${policy.name}</td>
                    <td>${policy.resource}</td>
                    <td>${policy.action}</td>
                    <td><span class="status-badge ${policy.effect}">${policy.effect}</span></td>
                    <td>${policy.conditions || '-'}</td>
                    <td><span class="status-badge ${policy.enabled ? 'success' : 'danger'}">${policy.enabled ? 'Active' : 'Disabled'}</span></td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="togglePolicy('${policy.id}')">Toggle</button>
                        <button class="btn btn-secondary btn-sm" onclick="editPolicy('${policy.id}')">Edit</button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="7">No policies found</td></tr>';
        }
    } catch (error) {
        console.error('Policies load failed:', error);
    }
}

async function togglePolicy(id) {
    try {
        await apiCall(`/policies/${id}/toggle`, { method: 'POST' });
        loadPolicies();
    } catch (error) {
        console.error('Toggle failed:', error);
    }
}

function editPolicy(id) {
    showModal('Edit Policy', `
        <form id="policy-form">
            <div class="form-group">
                <label>Policy Name</label>
                <input type="text" name="name" placeholder="e.g., Production Deletion Restriction">
            </div>
            <div class="form-group">
                <label>Resource</label>
                <input type="text" name="resource" placeholder="e.g., database.tables">
            </div>
            <div class="form-group">
                <label>Action</label>
                <input type="text" name="action" placeholder="e.g., delete">
            </div>
            <div class="form-group">
                <label>Effect</label>
                <select name="effect">
                    <option value="allow">Allow</option>
                    <option value="deny">Deny</option>
                </select>
            </div>
            <div class="form-group">
                <label>Conditions (JSON)</label>
                <textarea name="conditions" placeholder='{"env": "production", "requires_approval": true}'></textarea>
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Policy</button>
            </div>
        </form>
    `);
    
    document.getElementById('policy-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const policy = {
            name: formData.get('name'),
            resource: formData.get('resource'),
            action: formData.get('action'),
            effect: formData.get('effect'),
            conditions: formData.get('conditions')
        };
        
        try {
            await apiCall(`/policies${id ? '/' + id : ''}`, {
                method: id ? 'PUT' : 'POST',
                body: JSON.stringify(policy)
            });
            closeModal();
            loadPolicies();
        } catch (error) {
            console.error('Save failed:', error);
        }
    });
}

function showAddPolicyModal() {
    editPolicy(null);
}

async function loadAccessRequests() {
    try {
        const data = await apiCall('/access-requests');
        
        const tbody = document.getElementById('requests-table');
        if (data.requests && data.requests.length > 0) {
            tbody.innerHTML = data.requests.map(request => `
                <tr>
                    <td>${request.requester}</td>
                    <td>${request.tool}</td>
                    <td>${request.justification || '-'}</td>
                    <td><span class="status-badge ${request.status}">${request.status}</span></td>
                    <td>${formatTime(request.requested_at)}</td>
                    <td>
                        ${request.status === 'pending' ? `
                            <button class="btn btn-primary btn-sm" onclick="approveRequest('${request.id}')">Approve</button>
                            <button class="btn btn-danger btn-sm" onclick="rejectRequest('${request.id}')">Reject</button>
                        ` : '-'}
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6">No access requests</td></tr>';
        }
    } catch (error) {
        console.error('Access requests load failed:', error);
    }
}

function showNewRequestModal() {
    showModal('New Access Request', `
        <form id="request-form">
            <div class="form-group">
                <label>Your Name</label>
                <input type="text" name="requester" placeholder="John Doe">
            </div>
            <div class="form-group">
                <label>Tool Name</label>
                <input type="text" name="tool" placeholder="e.g., aws.ec2.describe">
            </div>
            <div class="form-group">
                <label>Justification</label>
                <textarea name="justification" placeholder="Why do you need access to this tool?"></textarea>
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Submit Request</button>
            </div>
        </form>
    `);
    
    document.getElementById('request-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const request = {
            requester: formData.get('requester'),
            tool: formData.get('tool'),
            justification: formData.get('justification')
        };
        
        try {
            await apiCall('/access-requests', {
                method: 'POST',
                body: JSON.stringify(request)
            });
            closeModal();
            loadAccessRequests();
        } catch (error) {
            console.error('Request failed:', error);
        }
    });
}

async function approveRequest(id) {
    try {
        await apiCall(`/access-requests/${id}/approve`, { method: 'POST' });
        loadAccessRequests();
    } catch (error) {
        console.error('Approve failed:', error);
    }
}

async function rejectRequest(id) {
    try {
        await apiCall(`/access-requests/${id}/reject`, { method: 'POST' });
        loadAccessRequests();
    } catch (error) {
        console.error('Reject failed:', error);
    }
}

function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal').classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

document.getElementById('modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'modal') {
        closeModal();
    }
});

function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    
    return date.toLocaleDateString();
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
