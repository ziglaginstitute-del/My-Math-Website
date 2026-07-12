# Ziglag Institute - Math Portal

A bespoke, responsive web application and STEM coaching directory designed for mathematics educators, students, and organizations. The portal features interactive course navigators, homework coaching tools, a resource vault, and organizational profile systems.

## Key Features

- 📐 **Syllabus & Courses Explorer**: A dynamic course catalog filtering system covering school mathematics, AP exam preps, and university-level Pure Math.
- 👨‍🏫 **1-on-1 Tutoring Coordinator**: An interactive whiteboard booking flow and receipt generator.
- 📂 **Resource Vault**: A categorized catalog supporting handouts, mock exams, and PDF booklets.
- ✉️ **Interactive Contact Wizard**: A questions-based multi-step form that validates queries and saves submissions directly to the database.
- 👥 **Our People Directory**: A database-driven layout presenting organization members, tutors, and founders.
- ☁️ **Cloud Deployment Ready**: Optimized with configuration profiles (`Procfile`, `render.yaml`, `.env.example`, `.gitignore`) for seamless hosting on platforms like **Render** or **PythonAnywhere**.
- 🗄️ **Flexible Database**: Configured to run on a local SQLite database for development, with automated postgresql integration for production cloud hosting.

## Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy (supporting PostgreSQL & SQLite)
- **Frontend**: Vanilla HTML5, CSS3 (Modern Glassmorphism & Blueprint grid themes), Javascript (Client State Engine)
- **Environment**: Python-dotenv (for API Keys & SMTP mail configurations)
- **Production Runner**: Gunicorn
