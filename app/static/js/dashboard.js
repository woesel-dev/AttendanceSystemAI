// Dashboard JavaScript

let currentClassroomId = null;
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', function () {
    const headcountBtn = document.getElementById('headcountBtn');
    const headcountImageInput = document.getElementById('headcountImage');
    const fileNameSpan = document.getElementById('fileName');

    // Handle image file selection
    headcountImageInput.addEventListener('change', function (e) {
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
    headcountBtn.addEventListener('click', function () {
        runHeadcountCheck();
    });
});

// Load current class information and populate dropdown
async function loadCurrentClass() {
    try {
        // Step 1: Get all classrooms for the dropdown
        const classroomsResponse = await fetch('/api/classrooms');
        const classroomsData = await classroomsResponse.json();

        const classroomSelect = document.getElementById('classroomSelect');
        const classInfoDiv = document.getElementById('classInfo');

        // Populate dropdown if empty (first load)
        if (classroomSelect.options.length <= 1) {
            classroomSelect.innerHTML = '<option value="">-- Select Classroom --</option>';
            if (classroomsData.classrooms && classroomsData.classrooms.length > 0) {
                classroomsData.classrooms.forEach(cls => {
                    const option = document.createElement('option');
                    option.value = cls.id;
                    option.textContent = `${cls.name} (${cls.subject})`;
                    classroomSelect.appendChild(option);
                });

                // Add event listener for change
                classroomSelect.addEventListener('change', function () {
                    const selectedId = this.value;
                    if (selectedId) {
                        currentClassroomId = selectedId;
                        loadSpecificClassData(selectedId);

                        // Also trigger reloads for other components
                        loadAttendanceStats();
                        loadRecentScans();
                        loadEnrolledStudents();
                    } else {
                        currentClassroomId = null;
                        classInfoDiv.innerHTML = '<div class="loading">Select a classroom to view details...</div>';
                    }
                });
            } else {
                classroomSelect.innerHTML = '<option value="">No classrooms found</option>';
            }
        }

        // Step 2: Check for active class if nothing selected yet
        if (!currentClassroomId) {
            const activeResponse = await fetch('/api/dashboard/current-class');
            const activeData = await activeResponse.json();

            if (activeResponse.ok && activeData.classroom_id) {
                currentClassroomId = activeData.classroom_id;
                classroomSelect.value = currentClassroomId;
                loadSpecificClassData(currentClassroomId);
            }
        }

        // If we have a selection (either manual or auto), refresh the info display
        if (currentClassroomId) {
            loadSpecificClassData(currentClassroomId);
        }

    } catch (error) {
        console.error('Error loading current class:', error);
        document.getElementById('classInfo').innerHTML =
            '<div class="loading">Error loading class information</div>';
    }
}

// Ensure loadSpecificClassData is defined to show details
async function loadSpecificClassData(classroomId) {
    try {
        const response = await fetch(`/api/admin/data?classroom_id=${classroomId}`);
        const data = await response.json();
        const classInfoDiv = document.getElementById('classInfo');

        if (response.ok && data) {
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
        }
    } catch (error) {
        console.error('Error loading specific class data', error);
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

// ---------------------------------------------------------
// Manual Check-In Logic
// ---------------------------------------------------------

let allEnrolledStudents = [];

// Load enrolled students
async function loadEnrolledStudents() {
    if (!currentClassroomId) {
        document.getElementById('studentList').innerHTML =
            '<div class="empty-state">No active class</div>';
        allEnrolledStudents = [];
        return;
    }

    try {
        const response = await fetch('/api/dashboard/enrolled-students');
        const data = await response.json();

        if (response.ok) {
            allEnrolledStudents = data.students || [];
            renderStudentList(allEnrolledStudents);
        }
    } catch (error) {
        console.error('Error loading enrolled students:', error);
        document.getElementById('studentList').innerHTML =
            '<div class="empty-state">Error loading students</div>';
    }
}

// Render student list
function renderStudentList(students) {
    const listDiv = document.getElementById('studentList');

    if (!students || students.length === 0) {
        listDiv.innerHTML = '<div class="empty-state">No students found</div>';
        return;
    }

    listDiv.innerHTML = students.map(student => {
        const statusClass = student.has_attended ? 'present' : 'absent';
        const buttonDisabled = student.has_attended ? 'disabled' : '';
        const buttonText = student.has_attended ? 'Present' : 'Check In';
        const buttonStyle = student.has_attended ?
            'background-color: #28a745; cursor: default;' : '';

        return `
            <div class="student-item" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee;">
                <div class="student-info">
                    <div style="font-weight: bold;">${student.name}</div>
                    <div style="font-size: 0.8em; color: #666;">${student.id}</div>
                </div>
                <button class="btn btn-sm ${student.has_attended ? 'btn-success' : 'btn-primary'}" 
                    onclick="manualCheckIn('${student.id}')" 
                    ${buttonDisabled}
                    style="${buttonStyle}">
                    ${buttonText}
                </button>
            </div>
        `;
    }).join('');
}

// Search functionality
document.getElementById('studentSearch').addEventListener('input', function (e) {
    const searchTerm = e.target.value.toLowerCase();

    if (!allEnrolledStudents.length) return;

    const filtered = allEnrolledStudents.filter(student =>
        student.name.toLowerCase().includes(searchTerm) ||
        student.id.toLowerCase().includes(searchTerm)
    );

    renderStudentList(filtered);
});

// Perform manual check-in
async function manualCheckIn(studentId) {
    try {
        const btn = event.target; // The button that was clicked
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = '...';

        const response = await fetch(`/manual_checkin/${studentId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            // Success
            // Update local state and re-render to avoid full reload flickers
            const studentIdx = allEnrolledStudents.findIndex(s => s.id === studentId);
            if (studentIdx !== -1) {
                allEnrolledStudents[studentIdx].has_attended = true;

                // Re-filter if search is active
                const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
                const currentList = allEnrolledStudents.filter(student =>
                    student.name.toLowerCase().includes(searchTerm) ||
                    student.id.toLowerCase().includes(searchTerm)
                );
                renderStudentList(currentList);
            }

            // Refresh stats and recent scans
            loadAttendanceStats();
            loadRecentScans();
        } else {
            alert('Error: ' + (data.message || 'Check-in failed'));
            btn.disabled = false;
            btn.textContent = originalText;
        }
    } catch (error) {
        console.error('Error manual check-in:', error);
        alert('Error: ' + error.message);
        const btn = event.target;
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Check In';
        }
    }
}

// Update the auto-refresh interval to include student list
// We don't want to re-render the list if user is searching/interacting,
// so maybe only refresh the data in background or just stick to manual refresh for list?
// Let's create a wrapper for the interval
const originalInterval = refreshInterval;
if (originalInterval) clearInterval(originalInterval);

refreshInterval = setInterval(() => {
    loadCurrentClass();
    loadAttendanceStats();
    loadRecentScans();
    // Only refresh student list if search bar is empty to avoid list jumping while typing
    if (!document.getElementById('studentSearch').value) {
        loadEnrolledStudents();
    }
}, 5000);

// Also add to initial load
loadEnrolledStudents();
