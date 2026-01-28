
import unittest
import json
from datetime import datetime, time, timedelta
import app
from app.models import db, User, Student, Classroom, AttendanceRecord
from app import create_app

class TestManualCheckIn(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create a test student
            self.student_id = "TEST_STUDENT_001"
            self.student = Student(id=self.student_id, name="Test Student")
            db.session.add(self.student)
            
            # Create a test classroom active NOW
            self.classroom_id = "TEST_CLASS_001"
            now = datetime.now()
            start_time = (now - timedelta(hours=1)).time()
            end_time = (now + timedelta(hours=1)).time()
            
            self.classroom = Classroom(
                id=self.classroom_id, 
                name="Test Class",
                time_window_start=start_time,
                time_window_end=end_time
            )
            db.session.add(self.classroom)
            
            # Enroll student
            self.student.enrollments.append(self.classroom)
            
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_manual_checkin_success(self):
        # Login as Teacher
        with self.client.session_transaction() as sess:
            sess['role'] = 'Teacher'
            
        # Call manual checkin
        response = self.client.post(f'/manual_checkin/{self.student_id}')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['student_id'], self.student_id)
        
        # Verify database
        with self.app.app_context():
            record = AttendanceRecord.query.filter_by(
                student_id=self.student_id,
                classroom_id=self.classroom_id
            ).first()
            self.assertIsNotNone(record)
            self.assertEqual(record.status, 'present')

    def test_manual_checkin_unauthorized(self):
        # No login
        response = self.client.post(f'/manual_checkin/{self.student_id}')
        self.assertEqual(response.status_code, 403)

    def test_manual_checkin_not_enrolled(self):
        with self.app.app_context():
            # Create another student not enrolled
            s2 = Student(id="TEST_002", name="Not Enrolled")
            db.session.add(s2)
            db.session.commit()
            
        with self.client.session_transaction() as sess:
            sess['role'] = 'Teacher'
            
        response = self.client.post('/manual_checkin/TEST_002')
        self.assertEqual(response.status_code, 403)

    def test_enrolled_students_api(self):
        # Login as Teacher
        with self.client.session_transaction() as sess:
            sess['role'] = 'Teacher'
            
        # Get list before checkin
        response = self.client.get('/api/dashboard/enrolled-students')
        data = json.loads(response.data)
        
        if response.status_code != 200:
            print(f"\n[ERROR] API Response: {data}")
        
        self.assertEqual(response.status_code, 200)
        students = data['students']
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]['id'], self.student_id)
        self.assertFalse(students[0]['has_attended'])
        
        # Checkin
        self.client.post(f'/manual_checkin/{self.student_id}')
        
        # Get list after checkin
        response = self.client.get('/api/dashboard/enrolled-students')
        data = json.loads(response.data)
        students = data['students']
        self.assertTrue(students[0]['has_attended'])

if __name__ == '__main__':
    unittest.main()
