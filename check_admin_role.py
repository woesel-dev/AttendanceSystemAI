from app import create_app, db
from app.models import User

app = create_app()

def check_and_fix_admin_role():
    with app.app_context():
        email = 'admin@smit.smu.edu.in'
        user = User.query.filter_by(email=email).first()
        
        if user:
            print(f"User found: {user.email}")
            print(f"Current Role: '{user.role}'")
            
            if user.role != 'Admin':
                print(f"Role is incorrect. Updating to 'Admin'...")
                user.role = 'Admin'
                db.session.commit()
                print("Role updated successfully.")
            else:
                print("Role is correct.")
        else:
            print(f"User {email} not found.")

if __name__ == "__main__":
    check_and_fix_admin_role()
