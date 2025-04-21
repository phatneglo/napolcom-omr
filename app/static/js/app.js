/**
 * Main JavaScript file for NAPOLCOM OMR Processing System
 */

// Check if user is authenticated
function checkAuthentication() {
    const token = localStorage.getItem('token');
    if (!token && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Update user info in navbar
function updateUserInfo() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    // Parse token and extract username
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const username = payload.sub;
        
        const usernameElement = document.getElementById('username');
        if (usernameElement) {
            usernameElement.textContent = username;
        }
    } catch (e) {
        console.error('Error parsing token:', e);
    }
}

// API request helper
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return null;
    }
    
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    try {
        const response = await fetch(`/api/v1${endpoint}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Unauthorized - token may have expired
            localStorage.removeItem('token');
            window.location.href = '/login';
            return null;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const container = document.querySelector('.messages');
    if (!container) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 150);
    }, 5000);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// Add event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!checkAuthentication()) return;
    
    // Update user info
    updateUserInfo();
    
    // Setup logout button
    const logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
});
