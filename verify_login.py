import sys
import os
import sqlite3
from datetime import datetime, timedelta
import unittest

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Student

class TestLoginSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for pure logic test
        # OR use the actual file if we want to test persistence/migrations.
        # Given I need to test if the columns work on the REAL db, I should probably use the file 
        # but safely. For now let's use in-memory to verify LOGIC first. 
        # Actually, the user wants the SYSTEM to work. 
        # So I should also fix the real DB.
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def test_login_flow(self):
        email = "test.student@smit.smu.edu.in"
        
        # 1. Login Request
        print(f"\nTesting Login for {email}...")
        response = self.client.post('/login', json={'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertIn('OTP sent', response.get_json()['message'])
        
        # 2. Get OTP from DB
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            self.assertIsNotNone(user)
            self.assertIsNotNone(user.otp)
            otp = user.otp
            print(f"Generated OTP: {otp}")
            
        # 3. Verify OTP
        print(f"Verifying OTP...")
        response = self.client.post('/verify', json={'email': email, 'otp': otp})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['redirect_url'], '/student/profile') # Should be updated to include ID if linked? 
        # In my logic: if user.role == 'Student' -> /student/profile (with param if linked)
        # Here I didn't link a student record, so it defaults to /student/profile.
        
    def test_invalid_domain(self):
        email = "hacker@evil.com"
        print(f"\nTesting Invalid Domain for {email}...")
        response = self.client.post('/login', json={'email': email})
        self.assertEqual(response.status_code, 403)
        self.assertIn('Access restricted', response.get_json()['error'])

    def test_invalid_otp(self):
        email = "valid@smit.smu.edu.in"
        
        # Login first to create user
        self.client.post('/login', json={'email': email})
        
        print(f"\nTesting Invalid OTP...")
        response = self.client.post('/verify', json={'email': email, 'otp': '000000'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid OTP', response.get_json()['error'])

    def test_form_login_flow(self):
        """Test the HTML form-based login flow using sessions."""
        email = "form.student@smit.smu.edu.in"
        
        # 1. GET Login Page
        print(f"\n[Form] Testing GET Login Page...")
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Attendance Login', response.data)

        # 2. POST Email (Form)
        print(f"[Form] Posting email {email}...")
        response = self.client.post('/login', data={'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'OTP sent!', response.data)
        
        # Check if stored in session (requires creating context or checking cookie/response)
        # Flask test client handles cookies automatically.
        
        # 3. Get OTP from DB
        with self.app.app_context():
            user = User.query.filter_by(email=email).first()
            self.assertIsNotNone(user, "User should be created")
            otp = user.otp
            print(f"[Form] Generated OTP: {otp}")

        # 4. POST OTP (Form) - Verify
        print(f"[Form] Verifying OTP...")
        response = self.client.post('/verify', data={'email': email, 'otp': otp})
        
        # Should redirect to profile
        self.assertEqual(response.status_code, 302) 
        self.assertIn('/student/profile', response.location)
        print("[Form] Redirected to:", response.location)

def update_real_db_schema():
    """Helper to ensure real DB has the new columns if using sqlite file."""
    db_path = 'instance/attendance.db' # Flask usually puts sqlite in instance/
    # Based on app config 'sqlite:///attendance.db', it might be in root or instance
    # create_app has 'sqlite:///attendance.db', usually relative to app root.
    
    if not os.path.exists('attendance.db'):
        print("attendance.db not found in root, trying instance/...")
        if os.path.exists('instance/attendance.db'):
            db_path = 'instance/attendance.db'
        else:
             print("DB not found. allowing create_all to handle it.")
             return

    print(f"Checking schema in {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if otp column exists in users
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'otp' not in columns:
        print("Adding 'otp' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN otp VARCHAR(6)")
    
    if 'otp_expiry' not in columns:
        print("Adding 'otp_expiry' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN otp_expiry DATETIME")
    
    # Check students table for date_joined
    cursor.execute("PRAGMA table_info(students)")
    student_columns = [row[1] for row in cursor.fetchall()]

    if 'date_joined' not in student_columns:
        print("Adding 'date_joined' column to students...")
        cursor.execute("ALTER TABLE students ADD COLUMN date_joined DATE")

    if 'user_id' not in student_columns:
         print("Adding 'user_id' column to students...")
         cursor.execute("ALTER TABLE students ADD COLUMN user_id INTEGER REFERENCES users(id)")

    conn.commit()
    conn.close()
    print("Schema check complete.")

if __name__ == '__main__':
    # Fix schema first
    try:
        update_real_db_schema()
    except Exception as e:
        print(f"Warning: DB update failed: {e}")

    # Run tests
    unittest.main()
