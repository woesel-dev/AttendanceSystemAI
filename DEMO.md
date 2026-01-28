# Navigation & Demo Guide

Follow these steps to experience the full **Smart Attendance AI** ecosystem.

## 1. The Command Center (Laptop)
### Step 1: Admin Configuration
* **Login**: Navigate to `/login` and use `admin@smit.smu.edu.in`.
* **OTP**: Retrieve the 6-digit verification code from your server terminal/logs.
* **Action**: Navigate to the **Admin Panel** and create a new **Classroom** (e.g., "E-315", "Object Oriented Programming").
* **Action**: Log out to clear the session.

### Step 2: Teacher Session
* **Login**: Use `teacher@smit.smu.edu.in` and the OTP from the terminal.
* **Action**: Select the classroom you just created and open the **QR Scanner**.
* **Note**: Keep this tab open—the laptop's camera is now the active "Bouncer".

---

## 2. The Student Experience (Mobile Phone)
### Step 3: Instant Enrollment
* **Access**: On a mobile phone, visit the live URL and log in using the format: `name_studentID@smit.smu.edu.in`.
* **Example**: `john_202400123@smit.smu.edu.in`.
* **Feature**: The system automatically parses the email to generate a unique **Digital ID** and **QR Code** on the fly.

---

## 3. Verification & AI Headcount
### Step 4: Real-time Scanning
* **Action**: Hold the phone's QR code up to the laptop's camera.
* **Result**: The scanner validates the ID and marks the student present instantly in the database.

### Step 5: AI Validation & Manual Override
* **Action**: Back on the Teacher Dashboard, upload a photo of the classroom.
* **AI Feature**: The system runs **Computer Vision** to detect the headcount and compare it with digital scans.
* **Backup**: Use the **Manual Present** button for students whose devices are unavailable.
