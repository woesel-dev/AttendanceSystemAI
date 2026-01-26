// Admin page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('adminForm');
    const messageDiv = document.getElementById('message');
    const refreshBtn = document.getElementById('refreshBtn');
    const dataList = document.getElementById('dataList');

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            subject: document.getElementById('subject').value.trim(),
            department: document.getElementById('department').value.trim(),
            classroom: document.getElementById('classroom').value.trim(),
            startTime: document.getElementById('startTime').value,
            endTime: document.getElementById('endTime').value,
            studentIds: document.getElementById('studentIds').value.trim()
        };

        // Validate
        if (!formData.subject || !formData.department || !formData.classroom || 
            !formData.startTime || !formData.endTime || !formData.studentIds) {
            showMessage('Please fill in all required fields', 'error');
            return;
        }

        // Parse student IDs (split by newline and filter empty)
        const studentIdsList = formData.studentIds
            .split('\n')
            .map(id => id.trim())
            .filter(id => id.length > 0);

        if (studentIdsList.length === 0) {
            showMessage('Please enter at least one student ID', 'error');
            return;
        }

        // Create classroom_id from subject and classroom (or use classroom as ID)
        const classroomId = formData.classroom.replace(/\s+/g, '_').toUpperCase();

        // Prepare data for API
        const apiData = {
            classroom_id: classroomId,
            subject: formData.subject,
            department: formData.department,
            classroom: formData.classroom,
            start_time: formData.startTime,
            end_time: formData.endTime,
            student_ids: studentIdsList
        };

        try {
            const response = await fetch('/api/admin/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiData)
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(result.message || 'Classroom added successfully!', 'success');
                form.reset();
                loadAdminData(); // Refresh the classrooms list
                loadStudents(); // Refresh the students list (students are created when classrooms are added)
            } else {
                showMessage(result.error || 'Failed to add classroom', 'error');
            }
        } catch (error) {
            showMessage('Error: ' + error.message, 'error');
        }
    });

    // Handle refresh button
    refreshBtn.addEventListener('click', function() {
        loadAdminData();
    });

    // Handle refresh students button
    const refreshStudentsBtn = document.getElementById('refreshStudentsBtn');
    refreshStudentsBtn.addEventListener('click', function() {
        loadStudents();
    });

    // Load admin data on page load
    loadAdminData();
    loadStudents();

    // Function to show message
    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }

    // Function to load and display admin data
    async function loadAdminData() {
        try {
            const response = await fetch('/api/admin/data');
            const data = await response.json();

            if (response.ok) {
                displayAdminData(data);
            } else {
                dataList.innerHTML = '<div class="empty-state">Failed to load data</div>';
            }
        } catch (error) {
            dataList.innerHTML = '<div class="empty-state">Error loading data: ' + error.message + '</div>';
        }
    }

    // Function to display admin data
    function displayAdminData(data) {
        if (!data || Object.keys(data).length === 0) {
            dataList.innerHTML = '<div class="empty-state">No classrooms added yet. Add one using the form above.</div>';
            return;
        }

        let html = '';
        for (const [classroomId, info] of Object.entries(data)) {
            html += `
                <div class="data-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h3 style="margin: 0;">${info.classroom || classroomId}</h3>
                        <button 
                            class="btn btn-primary" 
                            onclick="generateQRCode('${classroomId}')"
                            style="padding: 8px 16px; font-size: 0.9em;"
                            title="Generate QR code for this classroom">
                            📱 Generate QR
                        </button>
                    </div>
                    <div class="field">
                        <span class="field-label">Classroom ID:</span>
                        <span class="field-value">${classroomId}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Subject:</span>
                        <span class="field-value">${info.subject || 'N/A'}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Department:</span>
                        <span class="field-value">${info.department || 'N/A'}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Time:</span>
                        <span class="field-value">${info.start_time || 'N/A'} - ${info.end_time || 'N/A'}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Students (${info.student_ids ? info.student_ids.length : 0}):</span>
                        <div class="field-value">
                            <div class="student-list">
                                ${info.student_ids ? info.student_ids.map(id => 
                                    `<span class="student-badge">${id}</span>`
                                ).join('') : '<span>No students</span>'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        dataList.innerHTML = html;
    }

    // Function to generate and display QR code
    function generateQRCode(classroomId) {
        // Open QR code in new tab
        const qrUrl = `/admin/generate_qr/${encodeURIComponent(classroomId)}`;
        window.open(qrUrl, '_blank');
    }

    // Make function available globally
    window.generateQRCode = generateQRCode;

    // Function to load and display students
    async function loadStudents() {
        try {
            const response = await fetch('/api/students');
            const data = await response.json();

            if (response.ok) {
                displayStudents(data.students || []);
            } else {
                document.getElementById('studentsList').innerHTML = '<div class="empty-state">Failed to load students</div>';
            }
        } catch (error) {
            document.getElementById('studentsList').innerHTML = '<div class="empty-state">Error loading students: ' + error.message + '</div>';
        }
    }

    // Function to display students
    function displayStudents(students) {
        const studentsList = document.getElementById('studentsList');
        
        if (!students || students.length === 0) {
            studentsList.innerHTML = '<div class="empty-state">No students found. Students are automatically added when classrooms are created.</div>';
            return;
        }

        let html = '';
        for (const student of students) {
            html += `
                <div class="data-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h3 style="margin: 0;">${student.name || student.id}</h3>
                        <button 
                            class="btn btn-primary" 
                            onclick="generateStudentQRCode('${student.id}')"
                            style="padding: 8px 16px; font-size: 0.9em;"
                            title="Generate QR code for this student">
                            📱 Download Student QR
                        </button>
                    </div>
                    <div class="field">
                        <span class="field-label">Student ID:</span>
                        <span class="field-value">${student.id}</span>
                    </div>
                    ${student.email ? `
                    <div class="field">
                        <span class="field-label">Email:</span>
                        <span class="field-value">${student.email}</span>
                    </div>
                    ` : ''}
                </div>
            `;
        }
        studentsList.innerHTML = html;
    }

    // Function to generate and display student QR code
    function generateStudentQRCode(studentId) {
        // Open QR code in new tab
        const qrUrl = `/admin/generate_student_qr/${encodeURIComponent(studentId)}`;
        window.open(qrUrl, '_blank');
    }

    // Make function available globally
    window.generateStudentQRCode = generateStudentQRCode;
});
