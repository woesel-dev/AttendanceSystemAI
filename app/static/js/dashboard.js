// Dashboard JavaScript

let currentClassroomId = null;
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    const headcountBtn = document.getElementById('headcountBtn');
    const headcountImageInput = document.getElementById('headcountImage');
    const fileNameSpan = document.getElementById('fileName');
    
    // Handle image file selection
    headcountImageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileNameSpan.textContent = file.name;
            headcountBtn.disabled = false;
        } else {
            fileNameSpan.textContent = '';
            headcountBtn.disabled = true;
        }
    });
    
    // Load initial data
    loadCurrentClass();
    loadAttendanceStats();
    loadRecentScans();
    
    // Set up auto-refresh every 5 seconds
    refreshInterval = setInterval(() => {
        loadCurrentClass();
        loadAttendanceStats();
        loadRecentScans();
    }, 5000);
    
    // Headcount check button
    headcountBtn.addEventListener('click', function() {
        runHeadcountCheck();
    });
});

// Load current class information
async function loadCurrentClass() {
    try {
        const response = await fetch('/api/dashboard/current-class');
        const data = await response.json();
        
        const classInfoDiv = document.getElementById('classInfo');
        
        if (response.ok && data.classroom_id) {
            currentClassroomId = data.classroom_id;
            
            classInfoDiv.innerHTML = `
                <div class="class-info-item">
                    <span class="class-info-label">Subject:</span>
                    <span class="class-info-value">${data.subject || 'N/A'}</span>
                </div>
                <div class="class-info-item">
                    <span class="class-info-label">Department:</span>
                    <span class="class-info-value">${data.department || 'N/A'}</span>
                </div>
                <div class="class-info-item">
                    <span class="class-info-label">Classroom:</span>
                    <span class="class-info-value">${data.classroom || 'N/A'}</span>
                </div>
                <div class="class-info-item">
                    <span class="class-info-label">Time:</span>
                    <span class="class-info-value class-info-time">${data.start_time || 'N/A'} - ${data.end_time || 'N/A'}</span>
                </div>
            `;
        } else {
            currentClassroomId = null;
            classInfoDiv.innerHTML = `
                <div class="no-class">
                    <div class="no-class-icon">📚</div>
                    <p>No active class at this time</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">Check back during class hours or add a class in the admin panel.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading current class:', error);
        document.getElementById('classInfo').innerHTML = 
            '<div class="loading">Error loading class information</div>';
    }
}

// Load attendance statistics
async function loadAttendanceStats() {
    if (!currentClassroomId) {
        document.getElementById('scannedCount').textContent = '0';
        document.getElementById('totalEnrolled').textContent = '0';
        document.getElementById('attendanceRate').textContent = '0%';
        return;
    }
    
    try {
        const response = await fetch(`/api/dashboard/stats?classroom_id=${currentClassroomId}`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('scannedCount').textContent = data.scanned_count || 0;
            document.getElementById('totalEnrolled').textContent = data.total_enrolled || 0;
            
            const rate = data.total_enrolled > 0 
                ? Math.round((data.scanned_count / data.total_enrolled) * 100) 
                : 0;
            document.getElementById('attendanceRate').textContent = rate + '%';
        }
    } catch (error) {
        console.error('Error loading attendance stats:', error);
    }
}

// Load recent scans
async function loadRecentScans() {
    if (!currentClassroomId) {
        document.getElementById('recentScans').innerHTML = 
            '<div class="empty-state">No active class</div>';
        return;
    }
    
    try {
        const response = await fetch(`/api/dashboard/recent-scans?classroom_id=${currentClassroomId}`);
        const data = await response.json();
        
        const recentScansDiv = document.getElementById('recentScans');
        
        if (response.ok && data.scans && data.scans.length > 0) {
            recentScansDiv.innerHTML = data.scans.map(scan => {
                const time = new Date(scan.timestamp).toLocaleTimeString();
                return `
                    <div class="scan-item">
                        <div class="scan-item-info">
                            <div class="scan-item-student">${scan.student_id}</div>
                            <div class="scan-item-time">${time}</div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            recentScansDiv.innerHTML = '<div class="empty-state">No scans yet</div>';
        }
    } catch (error) {
        console.error('Error loading recent scans:', error);
    }
}

// Run AI headcount check
async function runHeadcountCheck() {
    if (!currentClassroomId) {
        showHeadcountResult('info', 'No Active Class', 'Please wait for a class to be active before running AI headcount.');
        return;
    }
    
    const headcountImageInput = document.getElementById('headcountImage');
    const file = headcountImageInput.files[0];
    
    if (!file) {
        showHeadcountResult('info', 'No Image Selected', 'Please select a classroom photo first.');
        return;
    }
    
    const headcountBtn = document.getElementById('headcountBtn');
    const originalText = headcountBtn.innerHTML;
    
    // Disable button and show loading
    headcountBtn.disabled = true;
    headcountBtn.innerHTML = '<span class="btn-icon">⏳</span> Processing with AI...';
    
    // Hide debug image initially
    const debugImageContainer = document.getElementById('debugImageContainer');
    const debugImage = document.getElementById('debug-image');
    if (debugImageContainer) {
        debugImageContainer.style.display = 'none';
    }
    
    try {
        // Step 1: Get the scanned attendance count
        const statsResponse = await fetch(`/api/dashboard/stats?classroom_id=${currentClassroomId}`);
        const statsData = await statsResponse.json();
        const scannedCount = statsData.scanned_count || 0;
        
        // Step 2: Upload image to /headcount endpoint for AI detection
        const formData = new FormData();
        formData.append('image', file);
        formData.append('classroom_id', currentClassroomId);
        
        const headcountResponse = await fetch('/headcount', {
            method: 'POST',
            body: formData
        });
        
        const headcountData = await headcountResponse.json();
        
        if (headcountResponse.ok) {
            // Get headcount from AI detection
            const detectedCount = headcountData.headcount || 0;
            const comparison = headcountData.comparison || {};
            
            // Update debug image with timestamp to prevent caching
            if (debugImageContainer && debugImage) {
                const timestamp = new Date().getTime();
                debugImage.src = `/static/uploads/debug_active.jpg?t=${timestamp}`;
                debugImageContainer.style.display = 'block';
            }
            
            // Step 3: Compare AI headcount with scanned attendance count
            let message, type, details;
            
            if (comparison.status === 'mismatch') {
                // Mismatch detected - Proxy suspected
                type = 'error';
                message = '⚠ Proxy Suspected';
                details = `
                    <div class="result-details">
                        <p class="result-stat"><strong>AI Headcount:</strong> ${comparison.detected_count || 0} person(s)</p>
                        <p class="result-stat"><strong>Scanned Count:</strong> ${comparison.scanned_count || 0} scan(s)</p>
                        <p class="result-stat"><strong>Difference:</strong> ${Math.abs(comparison.difference || 0)}</p>
                        <p class="alert-message"><strong>⚠️ Mismatch Detected!</strong><br>The number of people detected by AI doesn't match the number of QR code scans. This may indicate proxy attendance.</p>
                    </div>
                `;
            } else {
                // Match - Attendance verified
                type = 'success';
                message = '✅ Attendance Verified';
                details = `
                    <div class="result-details">
                        <p class="result-stat"><strong>AI Headcount:</strong> ${comparison.detected_count || 0} person(s)</p>
                        <p class="result-stat"><strong>Scanned Count:</strong> ${comparison.scanned_count || 0} scan(s)</p>
                        <p class="success-message"><strong>✓ Verification Successful!</strong><br>The AI headcount matches the scanned attendance count. No proxy attendance detected.</p>
                    </div>
                `;
            }
            
            showHeadcountResult(type, message, details);
        } else {
            // Hide debug image on error
            if (debugImageContainer) {
                debugImageContainer.style.display = 'none';
            }
            showHeadcountResult('info', 'AI Detection Failed', headcountData.error || 'Unable to process image with AI.');
        }
    } catch (error) {
        // Hide debug image on error
        if (debugImageContainer) {
            debugImageContainer.style.display = 'none';
        }
        showHeadcountResult('info', 'Error', 'Failed to run AI headcount: ' + error.message);
    } finally {
        // Re-enable button
        headcountBtn.disabled = false;
        headcountBtn.innerHTML = originalText;
    }
}

// Show headcount result
function showHeadcountResult(type, title, details) {
    const resultDiv = document.getElementById('headcountResult');
    resultDiv.className = `headcount-result show ${type}`;
    resultDiv.innerHTML = `
        <h3>${title}</h3>
        ${details}
    `;
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        resultDiv.classList.remove('show');
    }, 10000);
}
