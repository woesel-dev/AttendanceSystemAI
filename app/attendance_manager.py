"""
Database-backed attendance management system.
Handles student enrollment, time windows, and attendance tracking using SQLite.
"""
from datetime import datetime, time, date
from typing import Dict, List, Optional
from flask import current_app
from app.models import db, Student, Classroom, AttendanceRecord, enrollment_table


class AttendanceManager:
    """Manages students, classes, enrollments, and attendance records using database."""
    
    def add_student(self, student_id: str, name: str, **kwargs):
        """Register a new student."""
        with current_app.app_context():
            # Check if student already exists
            student = Student.query.get(student_id)
            if student:
                # Update existing student
                student.name = name
                if 'email' in kwargs:
                    student.email = kwargs.get('email')
            else:
                # Create new student
                student = Student(
                    id=student_id,
                    name=name,
                    email=kwargs.get('email')
                )
                db.session.add(student)
            
            db.session.commit()
    
    def add_classroom(self, classroom_id: str, name: str, 
                     time_window_start: str = "08:00", 
                     time_window_end: str = "18:00",
                     subject: Optional[str] = None,
                     department: Optional[str] = None):
        """Register a new classroom with time window for attendance."""
        with current_app.app_context():
            # Parse time strings to Time objects
            start_hour, start_min = map(int, time_window_start.split(':'))
            end_hour, end_min = map(int, time_window_end.split(':'))
            start_time = time(start_hour, start_min)
            end_time = time(end_hour, end_min)
            
            # Check if classroom already exists
            classroom = Classroom.query.get(classroom_id)
            if classroom:
                # Update existing classroom
                classroom.name = name
                classroom.time_window_start = start_time
                classroom.time_window_end = end_time
                if subject:
                    classroom.subject = subject
                if department:
                    classroom.department = department
            else:
                # Create new classroom
                classroom = Classroom(
                    id=classroom_id,
                    name=name,
                    time_window_start=start_time,
                    time_window_end=end_time,
                    subject=subject,
                    department=department
                )
                db.session.add(classroom)
            
            db.session.commit()
    
    def enroll_student(self, student_id: str, classroom_id: str) -> bool:
        """Enroll a student in a classroom."""
        with current_app.app_context():
            student = Student.query.get(student_id)
            classroom = Classroom.query.get(classroom_id)
            
            if not student or not classroom:
                return False
            
            # Check if already enrolled
            if classroom in student.enrollments:
                return True  # Already enrolled
            
            # Add enrollment
            student.enrollments.append(classroom)
            db.session.commit()
            
            return True
    
    def is_student_enrolled(self, student_id: str, classroom_id: str) -> bool:
        """Check if a student is enrolled in a classroom."""
        with current_app.app_context():
            print(f"[IS_ENROLLED] Checking enrollment: student_id='{student_id}', classroom_id='{classroom_id}'")
            
            student = Student.query.get(student_id)
            classroom = Classroom.query.get(classroom_id)
            
            if not student:
                print(f"[IS_ENROLLED] Student '{student_id}' not found in database")
                return False
            
            if not classroom:
                print(f"[IS_ENROLLED] Classroom '{classroom_id}' not found in database")
                return False
            
            is_enrolled = classroom in student.enrollments
            if is_enrolled:
                print(f"[IS_ENROLLED] Student '{student_id}' IS enrolled in classroom '{classroom_id}'")
            else:
                print(f"[IS_ENROLLED] Student '{student_id}' is NOT enrolled in classroom '{classroom_id}'")
                # List enrolled classrooms for this student
                student_classrooms = [c.id for c in student.enrollments]
                print(f"[IS_ENROLLED] Student '{student_id}' is enrolled in: {student_classrooms}")
            
            return is_enrolled
    
    def is_within_time_window(self, classroom_id: str, current_time: Optional[datetime] = None) -> bool:
        """Check if current time is within the attendance time window for a classroom."""
        with current_app.app_context():
            print(f"[TIME_WINDOW] Checking time window for classroom_id='{classroom_id}'")
            
            classroom = Classroom.query.get(classroom_id)
            if not classroom:
                print(f"[TIME_WINDOW] Classroom '{classroom_id}' not found in database")
                return False
            
            if current_time is None:
                current_time = datetime.now()
            
            current_time_only = current_time.time()
            start_time = classroom.time_window_start
            end_time = classroom.time_window_end
            
            print(f"[TIME_WINDOW] Current time: {current_time_only.strftime('%H:%M:%S')}")
            print(f"[TIME_WINDOW] Window: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
            
            is_within = start_time <= current_time_only <= end_time
            
            if is_within:
                print(f"[TIME_WINDOW] Current time IS within window")
            else:
                print(f"[TIME_WINDOW] Current time IS NOT within window")
            
            return is_within
    
    def get_active_classroom(self, current_time: Optional[datetime] = None) -> Optional[str]:
        """
        Find the active classroom based on current time and time windows.
        Returns the classroom_id of the classroom that is currently in session, or None if no class is active.
        """
        with current_app.app_context():
            if current_time is None:
                current_time = datetime.now()
            
            print(f"[GET_ACTIVE_CLASSROOM] Looking for active classroom at {current_time.strftime('%H:%M:%S')}")
            
            # Get all classrooms
            classrooms = Classroom.query.all()
            current_time_only = current_time.time()
            
            # Find classroom with current time within its time window
            for classroom in classrooms:
                start_time = classroom.time_window_start
                end_time = classroom.time_window_end
                
                if start_time <= current_time_only <= end_time:
                    print(f"[GET_ACTIVE_CLASSROOM] Found active classroom: {classroom.id} ({classroom.name})")
                    print(f"[GET_ACTIVE_CLASSROOM] Time window: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
                    return classroom.id
            
            print(f"[GET_ACTIVE_CLASSROOM] No active classroom found")
            return None
    
    def mark_attendance(self, student_id: str, classroom_id: str, 
                       timestamp: Optional[datetime] = None,
                       ai_headcount: Optional[int] = None,
                       qr_scan_count: Optional[int] = None) -> bool:
        """Mark attendance for a student in a classroom."""
        with current_app.app_context():
            print(f"[MARK_ATTENDANCE] Called with student_id='{student_id}', classroom_id='{classroom_id}'")
            
            if timestamp is None:
                timestamp = datetime.now()
            
            print(f"[MARK_ATTENDANCE] Checking for existing attendance records...")
            # Check if already marked today (prevent duplicates)
            today = timestamp.date()
            existing = AttendanceRecord.query.filter_by(
                student_id=student_id,
                classroom_id=classroom_id
            ).filter(
                db.func.date(AttendanceRecord.timestamp) == today
            ).first()
            
            if existing:
                print(f"[MARK_ATTENDANCE] DENIED: Attendance already marked today")
                print(f"[MARK_ATTENDANCE] Existing record ID: {existing.id}, Timestamp: {existing.timestamp}")
                return False  # Already marked today
            
            print(f"[MARK_ATTENDANCE] No existing record found for today. Creating new attendance record...")
            
            # Create new attendance record
            record = AttendanceRecord(
                student_id=student_id,
                classroom_id=classroom_id,
                timestamp=timestamp,
                status='present',
                ai_headcount=ai_headcount,
                qr_scan_count=qr_scan_count
            )
            db.session.add(record)
            db.session.commit()
            
            print(f"[MARK_ATTENDANCE] SUCCESS: Attendance record created with ID: {record.id}")
            return True
    
    def get_attendance_count(self, classroom_id: str, date: Optional[datetime] = None) -> int:
        """Get the count of students who marked attendance for a classroom on a given date."""
        with current_app.app_context():
            if date is None:
                date = datetime.now()
            
            target_date = date.date()
            
            # Count distinct students who marked attendance on this date
            count = db.session.query(
                db.func.count(db.func.distinct(AttendanceRecord.student_id))
            ).filter_by(
                classroom_id=classroom_id
            ).filter(
                db.func.date(AttendanceRecord.timestamp) == target_date
            ).scalar()
            
            return count or 0
    
    def get_attendance_list(self, classroom_id: str, date: Optional[datetime] = None) -> List[Dict]:
        """Get the list of attendance records for a classroom on a given date."""
        with current_app.app_context():
            if date is None:
                date = datetime.now()
            
            target_date = date.date()
            
            records = AttendanceRecord.query.filter_by(
                classroom_id=classroom_id
            ).filter(
                db.func.date(AttendanceRecord.timestamp) == target_date
            ).order_by(AttendanceRecord.timestamp.desc()).all()
            
            return [record.to_dict() for record in records]
    
    def add_admin_data(self, classroom_id: str, subject: str, department: str, 
                      classroom: str, start_time: str, end_time: str, 
                      student_ids: List[str]) -> bool:
        """
        Add admin data for a classroom.
        Stores: subject, department, classroom, start_time, end_time, student_ids list.
        """
        with current_app.app_context():
            # Register the classroom with admin data
            self.add_classroom(
                classroom_id=classroom_id,
                name=classroom,
                time_window_start=start_time,
                time_window_end=end_time,
                subject=subject,
                department=department
            )
            
            # Register students if they don't exist and enroll them
            for student_id in student_ids:
                # Check if student exists
                student = Student.query.get(student_id)
                if not student:
                    self.add_student(student_id, f'Student {student_id}')
                
                # Enroll student
                self.enroll_student(student_id, classroom_id)
            
            return True
    
    def get_admin_data(self, classroom_id: Optional[str] = None) -> Dict:
        """Get admin data. If classroom_id is None, returns all admin data."""
        with current_app.app_context():
            if classroom_id:
                classroom = Classroom.query.get(classroom_id)
                if not classroom:
                    return {}
                
                # Get enrolled student IDs
                student_ids = [student.id for student in classroom.students]
                
                return {
                    'subject': classroom.subject,
                    'department': classroom.department,
                    'classroom': classroom.name,
                    'start_time': classroom.time_window_start.strftime('%H:%M') if classroom.time_window_start else None,
                    'end_time': classroom.time_window_end.strftime('%H:%M') if classroom.time_window_end else None,
                    'student_ids': student_ids
                }
            else:
                return self.get_all_admin_data()
    
    def get_all_admin_data(self) -> Dict:
        """Get all admin data."""
        with current_app.app_context():
            classrooms = Classroom.query.all()
            result = {}
            
            for classroom in classrooms:
                # Get enrolled student IDs
                student_ids = [student.id for student in classroom.students]
                
                result[classroom.id] = {
                    'subject': classroom.subject,
                    'department': classroom.department,
                    'classroom': classroom.name,
                    'start_time': classroom.time_window_start.strftime('%H:%M') if classroom.time_window_start else None,
                    'end_time': classroom.time_window_end.strftime('%H:%M') if classroom.time_window_end else None,
                    'student_ids': student_ids
                }
            
            return result
    
    # Property to maintain backward compatibility with routes that access enrollments directly
    @property
    def enrollments(self) -> Dict[str, List[str]]:
        """Get enrollments as a dictionary for backward compatibility."""
        with current_app.app_context():
            result = {}
            classrooms = Classroom.query.all()
            for classroom in classrooms:
                result[classroom.id] = [student.id for student in classroom.students]
            return result
    
    @property
    def students(self) -> Dict[str, Dict]:
        """Get students as a dictionary for backward compatibility."""
        with current_app.app_context():
            result = {}
            all_students = Student.query.all()
            for student in all_students:
                result[student.id] = student.to_dict()
            return result
    
    @property
    def classrooms(self) -> Dict[str, Dict]:
        """Get classrooms as a dictionary for backward compatibility."""
        with current_app.app_context():
            result = {}
            all_classrooms = Classroom.query.all()
            for classroom in all_classrooms:
                result[classroom.id] = classroom.to_dict()
            return result


# Global instance
attendance_manager = AttendanceManager()
