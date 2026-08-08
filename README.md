# 🏔️ Trek Management System

A comprehensive, role-based web application built with **Flask**, designed to streamline the coordination of trekking activities. It replaces manual coordination with a robust system allowing Admins, Trek Staff, and Users (Trekkers) to efficiently manage trek approvals, track bookings, avoid overbooking, and maintain comprehensive trek histories.

## ✨ Features

### 🛡️ Admin
- **Dashboard Analytics:** View total treks, users, staff, and bookings.
- **Trek Management:** Create new treks, set capacity/difficulty, and manage schedules.
- **Staff Assignment:** Approve new staff registrations and assign staff to specific treks.
- **User Management:** View all registered users and blacklist/restore accounts if necessary.
- **Historical Data:** View complete logs of all bookings and past treks.

### 🏕️ Trek Staff
- **Assigned Treks:** View treks assigned by the Admin.
- **Participant Management:** See the list of users booked for their assigned trek.
- **Attendance Tracking:** Mark participants as Present/Absent for completed treks.
- **Status Updates:** Update available slots and toggle trek status (Open/Closed/Completed).

### 🥾 Users (Trekkers)
- **Browse Treks:** Search and filter available open treks by location and difficulty.
- **Booking System:** Book available slots for upcoming treks (prevents overbooking).
- **History & Cancellations:** View booking status, trekking history, and cancel active bookings.
- **Profile Management:** Update personal details, contact info, and passwords.

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask-Login
- **Database:** SQLite, SQLAlchemy (ORM)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 Templating
- **Architecture:** Monolithic, Server-Side Rendered (No JS used for core logic)

## 🚀 Local Setup Instructions

Follow these steps to run the project locally on your machine:

1. **Clone the repository** (or extract the ZIP file) and navigate into the project directory:
   ```bash
   cd trek_management-
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   - On macOS/Linux: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`

4. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   *(The database and default admin account are generated automatically upon running)*
   ```bash
   python app.py
   ```

6. **Access the application:**
   Open your web browser and navigate to: `http://127.0.0.1:5000`

### 🔑 Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`

---
*Developed by Rudraksh Tyagi*
