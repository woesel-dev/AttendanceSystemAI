# 🎓 Smart Attendance AI: Role-Based Computer Vision System

Smart Attendance AI modernizes classroom management by replacing paper sheets with secure QR code scanning and AI-powered verification. This role-based system empowers students with digital IDs while providing teachers with real-time dashboards and computer vision tools to validate attendance headcounts efficiently.


## Key Features

-   **Secure RBAC**: Domain-restricted login (example: `@smit.smu.edu.in`) ensures only authorized users can access the system, backed by secure OTP verification.
-   **Digital Student IDs**: Every student receives an auto-generated, permanent QR code for quick and contactless check-ins.
-   **Teacher Dashboard**: A comprehensive command center for teachers to access live scanners, view enrolled students, and track real-time attendance stats.
-   **AI Validation**: Integrated computer vision (OpenCV) automatically counts heads in classroom photos to verify scanning data and prevent proxy attendance.

## 🔐 Authentication & Security

The system uses a domain-restricted, Two-Factor Authentication (2FA) flow.

- **Email Restriction**: Only users with `@smit.smu.edu.in` addresses can attempt login.
- **Console-Based OTP**: For this hackathon demo, the 6-digit verification code is printed directly to the **Server Terminal/Logs** rather than sent via SMS or Email.

### Why Console OTP?
- **Cost-Efficiency**: Avoids the need for paid API credits (Twilio/SendGrid) during the prototyping phase.
- **Speed**: Instant code delivery for rapid testing and judging.
- **Privacy**: No actual student emails are sent across the public internet during development.

> **To log in:** Enter your college email, check the terminal where the Flask app is running, and copy the code shown there.

## Tech Stack

-   **Python** (Core Logic)
-   **Flask** (Web Framework)
-   **SQLAlchemy** (Database ORM)
-   **OpenCV** (Computer Vision & Face Detection)
-   **Gunicorn** (Production Server)

## Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Seed the Database**
    Populate the database with initial roles and users:
    ```bash
    python seed_db.py
    ```

4.  **Run Locally**
    Start the development server:
    ```bash
    python app.py
    ```
    The app will be accessible at `http://0.0.0.0:8000`.

## 🚀 Live Demo
Ready to test the app? Check out our **[Navigation Guide](DEMO.md)** for a step-by-step walkthrough of the Admin, Teacher, and Student flows.

## Deployment

This application is optimized for deployment on **Render**.

-   **Procfile**: Included for Gunicorn execution (`web: gunicorn app:app`).
-   **Auto-Seeding**: The application automatically checks for an empty database on startup and seeds initial Admin, Teacher, and Student accounts, ensuring a ready-to-use environment upon deployment.
