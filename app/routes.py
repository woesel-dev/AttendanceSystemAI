"""
Flask routes for the attendance system.
"""
from flask import request, jsonify, render_template, send_file, session, redirect, url_for
from datetime import datetime
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import io
import qrcode
from app.attendance_manager import attendance_manager
from app.headcount_detector import headcount_detector
from app.models import db, User, Student, AttendanceRecord
import random
from datetime import timedelta


def register_routes(app):
    """Register all routes with the Flask app."""
    
    @app.before_request
    def require_login():
        """
        Global login requirement.
        Redirects to login page if user is not logged in.
        Excludes login page, static files, and verification/logout routes.
        """
        allowed_endpoints = ['login', 'verify_otp', 'static', 'login_reset', 'logout', 'exclude_from_auth']
        
        # Check if the endpoint is allowed or if user is logged in
        if request.endpoint and request.endpoint not in allowed_endpoints and 'user_id' not in session:
            # For API requests, return 401 instead of redirecting
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            
            return redirect(url_for('login'))
    
    @app.route('/')
    def home_page():
        """Serve the home page (redirects to login)."""
        return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        """Logout user and clear session."""
        session.clear()
        return redirect(url_for('login'))
    
    @app.route('/student/profile')
    def student_profile():
        """Serve the student profile page."""
        student_id = request.args.get('student_id')
        student = None
        if student_id:
            # We need to access the students dictionary from attendance_manager
            # But wait, attendance_manager.students returns a dict of data, not Student objects?
            # Let's check get_students or similar. 
            # attendance_manager.students is a property wrapping self.data['students']
            # It returns a dict.
            # Models are better if we want to work with DB objects.
            # user instructions said "Link the Student model to User" in models.py, so we should use DB models.
            student = Student.query.filter_by(id=student_id).first()
        
        return render_template('student_profile.html', student=student)
    
    @app.route('/student/scanner')
    def student_scanner():
        """Serve the QR scanner page."""
        # Scanner Protection: Teacher only
        if session.get('role') != 'Teacher':
            # Redirect to student profile if logged in but wrong role
            return redirect(url_for('student_profile'))
            
        return render_template('scanner.html')

    @app.route('/login/reset')
    def login_reset():
        """
        Clear pending email from session and redirect to login.
        """
        session.pop('pending_email', None)
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Handle login requests.
        GET: Render login page.
        POST: Process email, validate domain (@smit.smu.edu.in), and generate OTP.
        """
        # GET request: Show login page
        if request.method == 'GET':
            # Clear pending email if it's a fresh load of the form, 
            # UNLESS we explicitly want to keep it. using 'reset' param to clear.
            if request.args.get('reset'):
                session.pop('pending_email', None)
            return render_template('login.html')

        # POST request
        try:
            # Handle both JSON and Form data
            if request.is_json:
                data = request.get_json()
                email = data.get('email')
                is_api = True
            else:
                email = request.form.get('email')
                is_api = False

            if not email:
                error_msg = 'Email is required'
                if is_api: return jsonify({'error': error_msg}), 400
                return render_template('login.html', error=error_msg)

            # Domain validation
            if not email.lower().endswith('@smit.smu.edu.in'):
                 error_msg = 'Access restricted to @smit.smu.edu.in domain'
                 if is_api: return jsonify({'error': error_msg}), 403
                 return render_template('login.html', error=error_msg)

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            otp_expiry = datetime.utcnow() + timedelta(minutes=5)

            # Check/Create user
            user = User.query.filter_by(email=email).first()
            if not user:
                # Create new user
                user = User(email=email, password_hash='OTP_AUTH', role='Student')
                db.session.add(user)
            
            user.otp = otp
            user.otp_expiry = otp_expiry
            db.session.commit()

            # PRINT OTP TO TERMINAL as requested
            print(f"\n[LOGIN] OTP for {email}: {otp}\n")

            if is_api:
                return jsonify({'message': 'OTP sent to email (check terminal for demo)', 'email': email}), 200
            else:
                # Store email in session for the next step
                session['pending_email'] = email
                return render_template('login.html', message='OTP sent! Check your terminal.')

        except Exception as e:
            print(f"Login error: {e}")
            if request.is_json: return jsonify({'error': 'Internal server error'}), 500
            return render_template('login.html', error='Internal server error')

    @app.route('/verify', methods=['POST'])
    def verify_otp():
        """
        Verify OTP and return redirect URL based on role.
        """
        try:
            # Handle both JSON and Form data
            if request.is_json:
                data = request.get_json()
                email = data.get('email')
                otp = data.get('otp')
                is_api = True
            else:
                email = request.form.get('email')
                otp = request.form.get('otp')
                is_api = False

            if not email or not otp:
                error_msg = 'Email and OTP are required'
                if is_api: return jsonify({'error': error_msg}), 400
                return render_template('login.html', error=error_msg)

            user = User.query.filter_by(email=email).first()

            if not user:
                 error_msg = 'User not found'
                 if is_api: return jsonify({'error': error_msg}), 404
                 return render_template('login.html', error=error_msg)

            if user.otp != otp:
                error_msg = 'Invalid OTP'
                if is_api: return jsonify({'error': error_msg}), 401
                return render_template('login.html', error=error_msg)
            
            if user.otp_expiry and datetime.utcnow() > user.otp_expiry:
                error_msg = 'OTP has expired'
                if is_api: return jsonify({'error': error_msg}), 401
                return render_template('login.html', error=error_msg)

            # OTP Valid - clear it
            user.otp = None
            user.otp_expiry = None
            db.session.commit()

            # Determine redirect URL
            redirect_url = '/student/profile' # Default
            if user.role == 'Admin':
                redirect_url = '/admin'
            elif user.role == 'Teacher':
                redirect_url = '/dashboard'
            elif user.role == 'Student':
                redirect_url = '/student/profile'
                # Pass student ID if linked
                if user.student:
                     redirect_url = f'/student/profile?student_id={user.student.id}'
            
            # Clear pending email from session on success
            session.pop('pending_email', None)
            # You might want to set a logged_in session variable here
            session['user_id'] = user.id
            session['role'] = user.role

            if is_api:
                return jsonify({
                    'message': 'Login successful',
                    'redirect_url': redirect_url,
                    'role': user.role
                }), 200
            else:
                return redirect(redirect_url)

        except Exception as e:
            print(f"Verify error: {e}")
            if request.is_json: return jsonify({'error': 'Internal server error'}), 500
            return render_template('login.html', error='Internal server error')
    
    @app.route('/api/classrooms', methods=['GET'])
    def get_classrooms():
        """Get list of all classrooms for dropdown selection."""
        try:
            classrooms = attendance_manager.classrooms
            # Convert to list format for frontend
            classroom_list = [
                {
                    'id': classroom_id,
                    'name': data.get('name', classroom_id),
                    'subject': data.get('subject', ''),
                    'department': data.get('department', '')
                }
                for classroom_id, data in classrooms.items()
            ]
            # Sort by name for better UX
            classroom_list.sort(key=lambda x: x['name'])
            return jsonify({'classrooms': classroom_list}), 200
        except Exception as e:
            return jsonify({'error': str(e), 'classrooms': []}), 500
    
    @app.route('/admin')
    def admin_page():
        """Serve the admin page."""
        # Admin Protection: Admin only
        if session.get('role') != 'Admin':
            # Redirect based on role
            if session.get('role') == 'Teacher':
                return redirect(url_for('dashboard'))
            return redirect(url_for('student_profile'))
            
        return render_template('admin.html')
    
    @app.route('/api/admin/add', methods=['POST'])
    def add_admin_data():
        """Add admin data (subject, department, classroom, times, student IDs)."""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            classroom_id = data.get('classroom_id')
            subject = data.get('subject')
            department = data.get('department')
            classroom = data.get('classroom')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            student_ids = data.get('student_ids', [])
            
            # Validate required fields
            if not all([classroom_id, subject, department, classroom, start_time, end_time]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            if not isinstance(student_ids, list) or len(student_ids) == 0:
                return jsonify({'error': 'Student IDs must be a non-empty list'}), 400
            
            # Add admin data
            success = attendance_manager.add_admin_data(
                classroom_id=classroom_id,
                subject=subject,
                department=department,
                classroom=classroom,
                start_time=start_time,
                end_time=end_time,
                student_ids=student_ids
            )
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Classroom {classroom} added successfully',
                    'classroom_id': classroom_id
                }), 201
            else:
                return jsonify({'error': 'Failed to add classroom'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/admin/data', methods=['GET'])
    def get_admin_data():
        """Get all admin data."""
        try:
            classroom_id = request.args.get('classroom_id')
            
            if classroom_id:
                data = attendance_manager.get_admin_data(classroom_id)
                if not data:
                    return jsonify({'error': 'Classroom not found'}), 404
                return jsonify(data), 200
            else:
                data = attendance_manager.get_all_admin_data()
                return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/generate_student_qr/<student_id>', methods=['GET'])
    def generate_student_qr(student_id):
        """
        Generate a QR code for a student.
        The QR code contains only the student_id as a string.
        This is the permanent QR code for each student.
        """
        try:
            # Verify student exists
            if student_id not in attendance_manager.students:
                return jsonify({'error': 'Student not found'}), 404
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # The QR code data is just the student_id string
            qr.add_data(student_id)
            qr.make(fit=True)
            
            # Create image from QR code
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to bytes buffer
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Return image as response
            return send_file(
                img_buffer,
                mimetype='image/png',
                as_attachment=False,
                download_name=f'qr_student_{student_id}.png'
            )
            
        except Exception as e:
            return jsonify({'error': f'Error generating student QR code: {str(e)}'}), 500
    
    @app.route('/api/students', methods=['GET'])
    def get_students():
        """Get list of all students."""
        try:
            students = attendance_manager.students
            # Convert to list format for frontend
            student_list = [
                {
                    'id': student_id,
                    'name': data.get('name', student_id),
                    'email': data.get('email', '')
                }
                for student_id, data in students.items()
            ]
            # Sort by name for better UX
            student_list.sort(key=lambda x: x['name'])
            return jsonify({'students': student_list}), 200
        except Exception as e:
            return jsonify({'error': str(e), 'students': []}), 500
    
    @app.route('/dashboard')
    def dashboard():
        """Serve the teacher dashboard page."""
        # Dashboard Protection: Teacher only
        if session.get('role') != 'Teacher':
            return redirect(url_for('student_profile'))
            
        return render_template('dashboard.html')
    
    @app.route('/api/dashboard/current-class', methods=['GET'])
    def get_current_class():
        """Get the currently active class based on time window."""
        try:
            current_time = datetime.now()
            all_admin_data = attendance_manager.get_all_admin_data()
            
            # Find active class (within time window)
            for classroom_id, class_data in all_admin_data.items():
                if attendance_manager.is_within_time_window(classroom_id, current_time):
                    return jsonify({
                        'classroom_id': classroom_id,
                        'subject': class_data.get('subject'),
                        'department': class_data.get('department'),
                        'classroom': class_data.get('classroom'),
                        'start_time': class_data.get('start_time'),
                        'end_time': class_data.get('end_time')
                    }), 200
            
            # No active class found
            return jsonify({
                'classroom_id': None,
                'message': 'No active class at this time'
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard/stats', methods=['GET'])
    def get_dashboard_stats():
        """Get attendance statistics for a classroom."""
        try:
            classroom_id = request.args.get('classroom_id')
            
            if not classroom_id:
                return jsonify({'error': 'Missing classroom_id'}), 400
            
            # Get scanned count
            scanned_count = attendance_manager.get_attendance_count(classroom_id)
            
            # Get total enrolled
            total_enrolled = 0
            if classroom_id in attendance_manager.enrollments:
                total_enrolled = len(attendance_manager.enrollments[classroom_id])
            
            return jsonify({
                'classroom_id': classroom_id,
                'scanned_count': scanned_count,
                'total_enrolled': total_enrolled
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard/recent-scans', methods=['GET'])
    def get_recent_scans():
        """Get recent attendance scans for a classroom."""
        try:
            classroom_id = request.args.get('classroom_id')
            limit = int(request.args.get('limit', 10))
            
            if not classroom_id:
                return jsonify({'error': 'Missing classroom_id'}), 400
            
            # Get today's attendance records
            records = attendance_manager.get_attendance_list(classroom_id)
            
            # Sort by timestamp (most recent first) and limit
            records.sort(key=lambda x: x['timestamp'], reverse=True)
            recent_records = records[:limit]
            
            return jsonify({
                'classroom_id': classroom_id,
                'scans': recent_records
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard/headcount-check', methods=['POST'])
    def headcount_check():
        """Run a headcount check for a classroom."""
        try:
            data = request.get_json()
            classroom_id = data.get('classroom_id')
            
            if not classroom_id:
                return jsonify({'error': 'Missing classroom_id'}), 400
            
            # Get scanned count
            scanned_count = attendance_manager.get_attendance_count(classroom_id)
            
            # Get total enrolled
            total_enrolled = 0
            if classroom_id in attendance_manager.enrollments:
                total_enrolled = len(attendance_manager.enrollments[classroom_id])
            
            return jsonify({
                'classroom_id': classroom_id,
                'scanned_count': scanned_count,
                'total_enrolled': total_enrolled,
                'missing': total_enrolled - scanned_count
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/headcount', methods=['POST'])
    def headcount():
        """
        AI Headcount Detection Route
        
        This route uses OpenCV HOG (Histogram of Oriented Gradients) person detector
        to count the number of people in a classroom image.
        
        Method: POST
        Input: multipart/form-data with 'image' file (classroom photo)
        Returns: JSON with headcount number
        
        Example Request:
            POST /headcount
            Content-Type: multipart/form-data
            Body: image file (PNG, JPG, etc.)
        
        Example Response:
            {
                "headcount": 12
            }
        """
        try:
            # Step 1: Check if image file is present in the request
            # Flask stores uploaded files in request.files dictionary
            if 'image' not in request.files:
                return jsonify({
                    'error': 'No image file provided',
                    'headcount': 0
                }), 400
            
            # Step 1b: Get classroom_id from request form data
            classroom_id = request.form.get('classroom_id')
            if not classroom_id:
                return jsonify({
                    'error': 'classroom_id is required',
                    'headcount': 0
                }), 400
            
            # Step 2: Get the uploaded file
            file = request.files['image']
            
            # Step 3: Check if a file was actually selected (not empty)
            if file.filename == '':
                return jsonify({
                    'error': 'No file selected',
                    'headcount': 0
                }), 400
            
            # Step 4: Validate file extension
            # Only allow common image formats
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            
            if file_extension not in allowed_extensions:
                return jsonify({
                    'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, bmp, webp',
                    'headcount': 0
                }), 400
            
            # Step 5: Read and decode the image file
            # Check file size before reading (max 10MB for images)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size == 0:
                return jsonify({
                    'error': 'Uploaded file is empty',
                    'headcount': 0
                }), 400
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                return jsonify({
                    'error': 'File too large. Maximum size is 10MB.',
                    'headcount': 0
                }), 400
            
            # Read the file bytes into memory
            file_bytes = file.read()
            
            # Double-check file is not empty after reading
            if not file_bytes or len(file_bytes) == 0:
                return jsonify({
                    'error': 'Failed to read file data',
                    'headcount': 0
                }), 400
            
            # Convert file bytes to numpy array
            # np.frombuffer creates an array from raw bytes
            nparr = np.frombuffer(file_bytes, np.uint8)
            
            # Decode the image using OpenCV
            # cv2.imdecode converts the byte array into an image (BGR format)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Step 6: Check if image was decoded successfully
            if image is None:
                return jsonify({
                    'error': 'Could not decode image. Please ensure it is a valid image file.',
                    'headcount': 0
                }), 400
            
            # Validate image dimensions
            if image.size == 0 or len(image.shape) < 2:
                return jsonify({
                    'error': 'Invalid image format or dimensions',
                    'headcount': 0
                }), 400
            
            # Step 7: Detect and count heads in the image using Haar Cascade
            # Check if detector is available
            if headcount_detector is None:
                return jsonify({
                    'error': 'AI headcount detector is not available. Please check server configuration.',
                    'headcount': 0
                }), 503
            
            # The detect_people method will:
            #   - Convert image to grayscale
            #   - Use Haar Cascade to detect faces/heads
            #   - Return count and detection details
            try:
                detected_count, detections = headcount_detector.detect_people(image)
            except ValueError as ve:
                # Handle image processing errors
                return jsonify({
                    'error': f'Image processing error: {str(ve)}',
                    'headcount': 0
                }), 400
            except Exception as detection_error:
                # Handle other detection errors
                return jsonify({
                    'error': f'Face detection error: {str(detection_error)}',
                    'headcount': 0
                }), 500
            
            # Step 8: Get scanned attendance count for this classroom
            try:
                scanned_count = attendance_manager.get_attendance_count(classroom_id)
            except Exception as attendance_error:
                scanned_count = 0
                print(f"Error getting attendance count: {attendance_error}")
            
            # Step 9: Draw debug boxes on image and save debug image
            # Create a copy of the image for drawing (don't modify original)
            debug_image = image.copy()
            
            # Draw green boxes around detected faces
            for detection in detections:
                x = detection['x']
                y = detection['y']
                w = detection['width']
                h = detection['height']
                # Draw green rectangle (BGR format: (0, 255, 0) = green)
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Ensure the debug uploads directory exists
            debug_dir = os.path.join('app', 'static', 'uploads')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Save the annotated debug image
            debug_image_path = os.path.join(debug_dir, 'debug_active.jpg')
            cv2.imwrite(debug_image_path, debug_image)
            
            # Step 10: Compare detected students with scanned students
            comparison = {
                'detected_count': detected_count,
                'scanned_count': scanned_count,
                'difference': detected_count - scanned_count,
                'status': 'match' if detected_count == scanned_count else 'mismatch'
            }
            
            # Step 11: Return the headcount comparison in JSON format
            return jsonify({
                'headcount': detected_count,
                'comparison': comparison,
                'detections': detections
            }), 200
            
        except Exception as e:
            # Handle any errors that occur during processing
            # Return error message with 0 headcount
            print(f"Error in /headcount endpoint: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': f'Error processing image: {str(e)}',
                'headcount': 0
            }), 500
    
    @app.route('/scan_qr', methods=['POST'])
    def scan_qr():
        """
        Process QR code scan for attendance.
        Automatically detects active classroom based on current time.
        
        Input JSON:
        {
            "student_id": "string"
        }
        
        Returns:
        {
            "status": "accepted" | "rejected",
            "message": "string" (optional)
        }
        """
        try:
            data = request.get_json()
            
            # Validate input
            if not data:
                print("[SCAN_QR] ERROR: No data provided in request")
                return jsonify({
                    'status': 'rejected',
                    'message': 'No data provided'
                }), 400
            
            student_id = data.get('student_id')
            
            # Log received data
            print(f"[SCAN_QR] Received request - student_id: '{student_id}'")
            print(f"[SCAN_QR] student_id type: {type(student_id)}, length: {len(student_id) if student_id else 0}")
            
            if not student_id:
                print(f"[SCAN_QR] ERROR: Missing student_id")
                return jsonify({
                    'status': 'rejected',
                    'message': 'Missing student_id'
                }), 400
            
            # Check if student exists (queries database)
            all_students = attendance_manager.students
            print(f"[SCAN_QR] Available students in database: {list(all_students.keys())}")
            print(f"[SCAN_QR] Checking if '{student_id}' exists in database...")
            
            if student_id not in all_students:
                print(f"[SCAN_QR] DENIED: Student '{student_id}' not found in database")
                print(f"[SCAN_QR] Available students: {list(all_students.keys())}")
                return jsonify({
                    'status': 'rejected',
                    'message': 'Student not found'
                }), 404
            
            print(f"[SCAN_QR] Student '{student_id}' found in database")
            
            # Automatically detect active classroom based on current time
            print(f"[SCAN_QR] Automatically detecting active classroom...")
            active_classroom_id = attendance_manager.get_active_classroom()
            
            if not active_classroom_id:
                print(f"[SCAN_QR] DENIED: No active class found at this time")
                return jsonify({
                    'status': 'rejected',
                    'message': 'No active class found at this time'
                }), 404
            
            print(f"[SCAN_QR] Active classroom detected: '{active_classroom_id}'")
            
            # Check if student is enrolled in the active classroom
            print(f"[SCAN_QR] Checking enrollment for student '{student_id}' in classroom '{active_classroom_id}'...")
            is_enrolled = attendance_manager.is_student_enrolled(student_id, active_classroom_id)
            if not is_enrolled:
                print(f"[SCAN_QR] DENIED: Student '{student_id}' is not enrolled in active classroom '{active_classroom_id}'")
                # Get enrolled students for this classroom
                classroom_enrollments = attendance_manager.enrollments.get(active_classroom_id, [])
                print(f"[SCAN_QR] Enrolled students in '{active_classroom_id}': {classroom_enrollments}")
                return jsonify({
                    'status': 'rejected',
                    'message': 'Student is not enrolled in the active classroom'
                }), 403
            
            print(f"[SCAN_QR] Student '{student_id}' is enrolled in active classroom '{active_classroom_id}'")
            
            # Mark attendance
            print(f"[SCAN_QR] Attempting to mark attendance for student '{student_id}' in classroom '{active_classroom_id}'...")
            success = attendance_manager.mark_attendance(student_id, active_classroom_id)
            
            if not success:
                print(f"[SCAN_QR] DENIED: Attendance already marked for today")
                return jsonify({
                    'status': 'rejected',
                    'message': 'Attendance already marked for today'
                }), 409
            
            print(f"[SCAN_QR] SUCCESS: Attendance marked for student '{student_id}' in classroom '{active_classroom_id}'")
            
            # Get classroom info for response
            classroom_info = attendance_manager.classrooms.get(active_classroom_id, {})
            classroom_name = classroom_info.get('name', active_classroom_id)
            
            return jsonify({
                'status': 'accepted',
                'message': f'Attendance marked successfully for {classroom_name}',
                'classroom_id': active_classroom_id,
                'classroom_name': classroom_name
            }), 200
            
        except Exception as e:
            print(f"[SCAN_QR] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'rejected',
                'message': f'Server error: {str(e)}'
            }), 500
    

    @app.route('/manual_checkin/<student_id>', methods=['POST'])
    def manual_checkin(student_id):
        """
        Manually check in a student for the currently active class.
        Backup method for when QR scanning fails.
        """
        try:
            # Check if user is authorized (Teacher/Admin)
            if 'role' not in session or session['role'] not in ['Teacher', 'Admin']:
                return jsonify({'error': 'Unauthorized'}), 403

            # Automatically detect active classroom
            active_classroom_id = attendance_manager.get_active_classroom()
            
            if not active_classroom_id:
                return jsonify({
                    'status': 'error',
                    'message': 'No active class found at this time'
                }), 404
            
            # Check if student exists
            if student_id not in attendance_manager.students:
                return jsonify({
                    'status': 'error',
                    'message': 'Student not found'
                }), 404
                
            # Check enrollment
            is_enrolled = attendance_manager.is_student_enrolled(student_id, active_classroom_id)
            if not is_enrolled:
                return jsonify({
                    'status': 'error',
                    'message': 'Student is not enrolled in the active classroom'
                }), 403
            
            # Mark attendance
            success = attendance_manager.mark_attendance(student_id, active_classroom_id)
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': 'Attendance already marked for today'
                }), 409
            
            # Get classroom info for response
            classroom_info = attendance_manager.classrooms.get(active_classroom_id, {})
            classroom_name = classroom_info.get('name', active_classroom_id)
            
            return jsonify({
                'status': 'success',
                'message': f'Manual check-in successful for {classroom_name}',
                'classroom_id': active_classroom_id,
                'student_id': student_id
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/dashboard/enrolled-students', methods=['GET'])
    def get_enrolled_students():
        """Get list of enrolled students for the active class with attendance status."""
        try:
            # Get active classroom
            active_classroom_id = attendance_manager.get_active_classroom()
            
            if not active_classroom_id:
                return jsonify({
                    'classroom_id': None,
                    'students': []
                }), 200
            
            # Get enrolled students
            enrollment_ids = attendance_manager.enrollments.get(active_classroom_id, [])
            students_data = []
            
            # Get today's attendance to mark status
            today = datetime.now().date()
            attendance_records = AttendanceRecord.query.filter_by(
                classroom_id=active_classroom_id
            ).filter(
                db.func.date(AttendanceRecord.timestamp) == today
            ).all()
            
            attended_student_ids = {record.student_id for record in attendance_records}
            
            for student_id in enrollment_ids:
                student = attendance_manager.students.get(student_id, {})
                students_data.append({
                    'id': student_id,
                    'name': student.get('name', student_id),
                    'has_attended': student_id in attended_student_ids
                })
            
            # Sort by name
            students_data.sort(key=lambda x: x['name'])
            
            return jsonify({
                'classroom_id': active_classroom_id,
                'students': students_data
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/attendance/<classroom_id>', methods=['GET'])
    def get_attendance(classroom_id):
        """Get attendance count and list for a classroom."""
        try:
            count = attendance_manager.get_attendance_count(classroom_id)
            records = attendance_manager.get_attendance_list(classroom_id)
            
            return jsonify({
                'classroom_id': classroom_id,
                'count': count,
                'records': records
            }), 200
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/student/<student_id>', methods=['GET', 'POST'])
    def student_api(student_id):
        """Get or register a student."""
        if request.method == 'GET':
            """Get student information."""
            try:
                students = attendance_manager.students
                if student_id not in students:
                    return jsonify({'error': 'Student not found'}), 404
                
                student_data = students[student_id]
                return jsonify(student_data), 200
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:  # POST
            """Register a new student."""
            try:
                data = request.get_json() or {}
                name = data.get('name', f'Student {student_id}')
                
                attendance_manager.add_student(student_id, name, **data)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Student registered',
                    'student_id': student_id
                }), 201
            except Exception as e:
                return jsonify({
                    'error': str(e)
                }), 500
    
    @app.route('/api/classroom/<classroom_id>', methods=['POST'])
    def register_classroom(classroom_id):
        """Register a new classroom."""
        try:
            data = request.get_json() or {}
            name = data.get('name', f'Classroom {classroom_id}')
            time_start = data.get('time_window_start', '08:00')
            time_end = data.get('time_window_end', '18:00')
            
            attendance_manager.add_classroom(
                classroom_id, 
                name, 
                time_start, 
                time_end
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Classroom registered',
                'classroom_id': classroom_id
            }), 201
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/enroll', methods=['POST'])
    def enroll_student():
        """Enroll a student in a classroom."""
        try:
            data = request.get_json()
            student_id = data.get('student_id')
            classroom_id = data.get('classroom_id')
            
            if not student_id or not classroom_id:
                return jsonify({
                    'error': 'Missing student_id or classroom_id'
                }), 400
            
            success = attendance_manager.enroll_student(student_id, classroom_id)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Student enrolled'
                }), 200
            else:
                return jsonify({
                    'error': 'Student or classroom not found'
                }), 404
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500
