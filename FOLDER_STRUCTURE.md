# Project Folder Structure

```
smart-attendance-with-cv/
│
├── app.py                          # Main Flask application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── .gitignore                      # Git ignore file
│
└── app/                           # Main application package
    ├── __init__.py                # Flask app initialization
    ├── routes.py                  # API routes (attendance, face recognition)
    ├── face_recognition_utils.py  # Face recognition helper functions
    ├── attendance_manager.py      # In-memory attendance tracking
    │
    ├── templates/                 # HTML templates
    │   ├── student.html           # Student attendance page
    │   └── teacher_dashboard.html # Teacher dashboard
    │
    ├── static/                    # Static assets
    │   ├── css/                   # Stylesheets
    │   │   ├── student.css
    │   │   └── dashboard.css
    │   ├── js/                    # JavaScript files
    │   │   ├── student.js         # Camera & face capture logic
    │   │   └── dashboard.js       # Dashboard live updates
    │   └── images/                # Image assets
    │
    ├── uploads/                   # Temporary uploaded face images
    ├── registered_faces/          # Registered student face encodings
    │
```

## Directory Purposes

- **app.py**: Main entry point that runs the Flask server
- **app/__init__.py**: Initializes Flask app and registers blueprints
- **app/routes.py**: Contains all API endpoints:
  - `/` - Student attendance page
  - `/dashboard` - Teacher dashboard
  - `/api/register` - Register new student
  - `/api/verify` - Verify face and mark attendance
  - `/api/attendance` - Get attendance data
- **app/face_recognition_utils.py**: Handles face encoding and matching
- **app/attendance_manager.py**: In-memory storage for students and attendance
- **templates/**: HTML pages for student and teacher interfaces
- **static/**: Frontend assets (CSS, JS, images)
- **uploads/**: Temporary storage for captured face images
- **registered_faces/**: Stores registered student face encodings (JSON format)
