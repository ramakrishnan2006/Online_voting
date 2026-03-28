# 🗳️ VoteHub — College Online Voting System

A secure, full-stack college voting system built with **Flask** (backend) and **HTML/CSS/JS** (frontend).

---

## 📁 Project Structure

```
voting_system/
├── app.py                  # Flask backend (all routes + DB)
├── requirements.txt
├── voting.db               # SQLite DB (auto-created on first run)
├── templates/
│   ├── base.html           # Shared layout
│   ├── home.html           # Landing page
│   ├── login.html          # Student login
│   ├── register.html       # Student registration
│   ├── vote.html           # Voting page
│   ├── thank_you.html      # Vote success page
│   ├── admin_login.html    # Admin login
│   └── results.html        # Admin results dashboard
└── static/
    ├── css/style.css       # Global styles
    └── js/main.js          # Shared JS utilities
```

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## 🔑 Default Credentials

### Admin
- **URL:** `http://localhost:5000/admin/login`
- **Username:** `admin`
- **Password:** `admin123`

### Students
- Register via `/register` with roll number, name, department, email & password

---

## ✨ Features

| Feature | Details |
|---|---|
| **One Vote Per Student** | Roll number prevents duplicate voting |
| **Student Registration** | Roll number + email unique validation |
| **Secure Login** | SHA-256 password hashing |
| **4 Positions** | President, VP, Secretary, Treasurer |
| **8 Candidates** | Pre-loaded sample data |
| **Admin Dashboard** | Live results, turnout stats, winner highlight |
| **Toggle Voting** | Admin can open/close voting anytime |
| **Confetti Animation** | Thank you page celebration |
| **Responsive Design** | Works on mobile & desktop |

---

## 🛡️ Security Features
- Passwords hashed with SHA-256
- Session-based authentication
- Server-side vote duplication check (not just session)
- Admin and student login are completely separate
- CSRF-safe form handling via JSON API

---

## 📊 Pages Overview

| Page | Route | Access |
|---|---|---|
| Home | `/` | Public |
| Student Register | `/register` | Public |
| Student Login | `/login` | Public |
| Vote | `/vote` | Student only |
| Thank You | `/thank_you` | Student only |
| Admin Login | `/admin/login` | Public |
| Results | `/admin/results` | Admin only |
