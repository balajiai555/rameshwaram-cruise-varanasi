# Rameshwaram Cruise Varanasi 🚢

A Django-based web application for booking cruise tickets, managing schedules, seats, OTP authentication, and PDF ticket generation for Rameshwaram Cruise in Varanasi.

---

## 📋 Prerequisites

- **Python 3.12** or higher installed on your system.
- **Git** installed on your system.

---

## 🚀 Quick Start & Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/balajiai555/rameshwaram-cruise-varanasi.git
cd rameshwaram-cruise-varanasi
```

*(Note: If your cloned directory structure has an inner folder, `cd` into the project root directory containing `manage.py`)*

---

### 2. Create & Activate Virtual Environment (Recommended)

#### On Windows (PowerShell / Command Prompt):
```bash
python -m venv venv
.\venv\Scripts\activate
```

#### On Linux / macOS:
```bash
python3.12 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

Install required packages using `requirements.txt` (or `req.txt`):

```bash
pip install -r requirements.txt
```
*or*
```bash
pip install -r req.txt
```

---

### 4. Database Setup & Migrations

Run database migrations to prepare the database schema:

```bash
python manage.py migrate
```

---

### 5. Start the Development Server

Run the Django local development server accessible on all network interfaces:

```bash
python manage.py runserver 0.0.0.0:8000
```

Access the application in your browser at: `http://localhost:8000` or `http://127.0.0.1:8000`.

---

## 📁 Key Features

- **Cruise Schedule & Seat Booking System**: Interactive seat selection and real-time status updates.
- **OTP Authentication**: Secure user verification flow.
- **Ticket Generation**: Automated PDF ticket generation and email delivery.
- **Admin & Dashboard Management**: Comprehensive control panel for schedules, table availability, and bookings.

---

## 📄 License & Legal Notice

**Copyright (c) 2026 Balaji AI Lab. All Rights Reserved.**

This repository and its source code are proprietary and confidential property of **Balaji AI Lab** (Owner: **Chandan Gupta**). 

Unauthorized copying, distribution, modification, or use of this codebase without prior written permission from Chandan Gupta is strictly prohibited. Any unauthorized use will be subject to legal action under the jurisdiction of the **Kushinagar Court** (Kushinagar, Uttar Pradesh, India).

Refer to the [LICENSE](LICENSE) file for full details.


