# Project Folder Structure

```
.
├── Procfile                    # Render deployment configuration
├── README.md                   # Project documentation
├── app                         # Main application package
│   ├── __init__.py             # App initialization and database setup
│   ├── attendance_manager.py   # Core attendance logic
│   ├── headcount_detector.py   # OpenCV logic for headcount
│   ├── models.py               # SQLAlchemy database models
│   ├── routes.py               # Flask routes and view functions
│   ├── static
│   │   ├── css                 # Stylesheets (admin.css, dashboard.css, etc.)
│   │   └── js                  # Javascript files (admin.js, dashboard.js, etc.)
│   └── templates               # HTML templates (login.html, dashboard.html, etc.)
├── app.py                      # Application entry point
├── check_admin_role.py         # Utility script
├── requirements.txt            # Python dependencies
├── seed_db.py                  # Database seeding logic
├── verify_autoseed.py          # Auto-seed verification script
├── verify_login.py             # Login verification script
├── verify_manual_checkin.py    # Manual check-in verification script
└── verify_security.py          # Security verification script
```
