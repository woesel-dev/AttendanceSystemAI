
import unittest
import json
from app import create_app
from app.models import db

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_global_login_requirement(self):
        """Test that unauthenticated access redirects to login."""
        # endpoints to test
        endpoints = [
            '/dashboard', 
            '/student/profile', 
            '/student/scanner', 
            '/admin'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Should redirect (302) to /login
            self.assertEqual(response.status_code, 302, f"Failed for {endpoint}")
            self.assertIn('/login', response.location)

    def test_allowed_routes(self):
        """Test routes that should be accessible without login."""
        # /login should return 200
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

        # /static/... (mocking a request to check if it's allowed by before_request)
        # We can't easily request a real static file without setup, but we can verify logic via a fake endpoint if we had one
        # or rely on the fact that /login works means allowed_routes works for login.

    def test_scanner_access(self):
        """Test role-based access for scanner."""
        # 1. As Student (Authenticated but wrong role)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Student'
        
        response = self.client.get('/student/scanner')
        # Should redirect to student_profile (Student logged in effectively)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/student/profile', response.location)
        
        # 2. As Admin (Wrong role)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['role'] = 'Admin'
        
        response = self.client.get('/student/scanner')
        # Should redirect to student_profile (default fallback for non-teacher)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/student/profile', response.location) # Or dashboard if we implemented that logic, but current implementation goes to profile
        
        # 3. As Teacher (Correct role)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['role'] = 'Teacher'
        
        response = self.client.get('/student/scanner')
        self.assertEqual(response.status_code, 200)

    def test_admin_access(self):
        """Test role-based access for admin page."""
        # 1. As Student
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Student'
        
        response = self.client.get('/admin')
        # Redirect to student_profile
        self.assertEqual(response.status_code, 302)
        self.assertIn('/student/profile', response.location)
        
        # 2. As Teacher
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['role'] = 'Teacher'
        
        response = self.client.get('/admin')
        # Redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard', response.location)
        
        # 3. As Admin
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['role'] = 'Admin'
        
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_access(self):
        """Test protect /dashboard."""
        # 1. As Student
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Student'
        
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/student/profile', response.location)
        
        # 2. As Teacher
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['role'] = 'Teacher'
            
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)

    def test_api_protection(self):
        """Test that API endpoints return 401 instead of redirect."""
        response = self.client.get('/api/students')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Authentication required')

if __name__ == '__main__':
    unittest.main()
