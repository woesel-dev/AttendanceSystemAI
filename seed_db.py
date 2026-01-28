def seed_database(app=None):
    """Populate database with initial data."""
    # Use provided app or create new one if running as script
    created_app = False
    if app is None:
        from app import create_app
        app = create_app()
        created_app = True

    with app.app_context():
        from app.models import db, User, Student
        from datetime import date

        # Ensure tables exist
        db.create_all()
        print("Database tables ensured.")
        
        # 1. Create Student User
        student_email = 'tenzin_202400015@smit.smu.edu.in'
        student_user = User.query.filter_by(email=student_email).first()
        
        if not student_user:
            student_user = User(
                email=student_email,
                role='Student', # Capitalized based on model constraints
                password_hash='seeded_user' # Placeholder hash
            )
            db.session.add(student_user)
            db.session.commit() # Commit to get ID
            print(f"Created user: {student_email}")
        else:
            print(f"User already exists: {student_email}")

        # 2. Link Student Profile
        student_id = '202400015'
        student_profile = Student.query.filter_by(id=student_id).first()
        
        if not student_profile:
            student_profile = Student(
                id=student_id,
                name='Tenzin',
                email=student_email,
                date_joined=date.today(),
                user=student_user # Link relationship
            )
            db.session.add(student_profile)
            db.session.commit()
            print(f"Created student profile: {student_id}")
        else:
            print(f"Student profile already exists: {student_id}")
            # Ensure link
            if student_profile.user != student_user:
                student_profile.user = student_user
                db.session.commit()
                print(f"Linked student profile {student_id} to user {student_email}")

        # 3. Create Teacher User
        teacher_email = 'teacher@smit.smu.edu.in'
        teacher_user = User.query.filter_by(email=teacher_email).first()
        
        if not teacher_user:
            teacher_user = User(
                email=teacher_email,
                role='Teacher',
                password_hash='seeded_teacher'
            )
            db.session.add(teacher_user)
            db.session.commit()
            print(f"Created teacher user: {teacher_email}")
        else:
             print(f"Teacher user already exists: {teacher_email}")

        # 4. Create Admin User
        admin_email = 'admin@smit.smu.edu.in'
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            admin_user = User(
                email=admin_email,
                role='Admin',
                password_hash='seeded_admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created admin user: {admin_email}")
        else:
             if admin_user.role != 'Admin':
                 admin_user.role = 'Admin'
                 db.session.commit()
                 print(f"Updated admin user role to Admin: {admin_email}")
             else:
                 print(f"Admin user already exists and has correct role: {admin_email}")

        print("Database seeding complete!")

if __name__ == "__main__":
    seed_database()
