
import unittest
import os
from app import create_app
from app.models import db, User

class TestAutoSeed(unittest.TestCase):
    def setUp(self):
        # Use an in-memory DB to ensure it starts empty
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        self.app = create_app()
        self.app.config['TESTING'] = True

    def tearDown(self):
        # Clean up
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

    def test_auto_seed(self):
        """Test that the database is automatically seeded on startup."""
        with self.app.app_context():
            # Check for seeded users
            student = User.query.filter_by(role='Student').first()
            teacher = User.query.filter_by(role='Teacher').first()
            admin = User.query.filter_by(role='Admin').first()
            
            self.assertIsNotNone(student, "Student should be auto-seeded")
            self.assertIsNotNone(teacher, "Teacher should be auto-seeded")
            self.assertIsNotNone(admin, "Admin should be auto-seeded")
            
            self.assertEqual(student.email, 'tenzin_202400015@smit.smu.edu.in')
            self.assertEqual(teacher.email, 'teacher@smit.smu.edu.in')
            self.assertEqual(admin.email, 'admin@smit.smu.edu.in')

if __name__ == '__main__':
    unittest.main()
