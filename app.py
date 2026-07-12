import os
import logging
from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Set up basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-key-12345')

# Database URI configuration
db_url = os.getenv('DATABASE_URL', 'sqlite:///math_portal.db')
# Handle Render's postgres:// vs postgresql:// scheme discrepancy
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database models
class ContactSubmission(db.Model):
    __tablename__ = 'contact_submissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    sphere = db.Column(db.String(50), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    preferred_contact = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    avatar = db.Column(db.String(10), nullable=True) # Emoji avatar
    email = db.Column(db.String(100), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    github = db.Column(db.String(200), nullable=True)
    youtube = db.Column(db.String(200), nullable=True)
    display_order = db.Column(db.Integer, default=0)

# Routes
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/index.html')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/courses.html')
def courses():
    return send_from_directory('.', 'courses.html')

@app.route('/tutoring.html')
def tutoring():
    return send_from_directory('.', 'tutoring.html')

@app.route('/vault.html')
def vault():
    return send_from_directory('.', 'vault.html')

@app.route('/course-view.html')
def course_view():
    return send_from_directory('.', 'course-view.html')

@app.route('/contact.html')
def contact_page():
    return send_from_directory('.', 'contact.html')

@app.route('/people.html')
def people_page():
    return send_from_directory('.', 'people.html')

@app.route('/api/people', methods=['GET'])
def get_people():
    try:
        members = Member.query.order_by(Member.display_order.asc(), Member.name.asc()).all()
        members_list = []
        for m in members:
            members_list.append({
                'id': m.id,
                'name': m.name,
                'role': m.role,
                'bio': m.bio,
                'avatar': m.avatar or '👨‍🏫',
                'email': m.email or '',
                'linkedin': m.linkedin or '',
                'github': m.github or '',
                'youtube': m.youtube or ''
            })
        return jsonify(members_list)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server database error: {str(e)}'}), 500

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    sphere = data.get('sphere')
    question_type = data.get('question_type')
    message = data.get('message')
    preferred_contact = data.get('preferred_contact')
    phone = data.get('phone')

    if not name or not email or not message:
        return jsonify({'success': False, 'message': 'Name, Email, and Message are required.'}), 400

    try:
        submission = ContactSubmission(
            name=name,
            email=email,
            sphere=sphere or 'general',
            question_type=question_type or 'general',
            message=message,
            preferred_contact=preferred_contact,
            phone=phone
        )
        db.session.add(submission)
        db.session.commit()

        # Simulated Email Sending logging
        logging.info(f"Simulating email dispatch to {os.getenv('CONTACT_EMAIL', 'info@ziglaginstitute.com')}")
        logging.info(f"From: {email} ({name})")
        logging.info(f"Subject: Math Portal Inquiry - {question_type} ({sphere})")
        logging.info(f"Message: {message}")

        # Optional: Send actual email if SMTP configuration is provided in env
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        contact_email = os.getenv('CONTACT_EMAIL', 'info@ziglaginstitute.com')

        if smtp_server and smtp_port and smtp_username and smtp_password:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = contact_email
                msg['Subject'] = f"New Contact Submission: {question_type} ({sphere})"
                
                body = f"""
                You have received a new contact submission from Ziglag Institute Math Portal:
                
                Name: {name}
                Email: {email}
                Phone: {phone or 'Not provided'}
                Preferred Contact Method: {preferred_contact or 'Email'}
                Sphere of Interest: {sphere}
                Inquiry Type: {question_type}
                
                Message:
                {message}
                
                Submitted at: {submission.submitted_at}
                """
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(smtp_server, int(smtp_port))
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_username, contact_email, msg.as_string())
                server.quit()
                logging.info("Actual email notification sent successfully via SMTP.")
            except Exception as email_err:
                logging.error(f"Failed to send email notification: {email_err}")

        return jsonify({'success': True, 'message': 'Your inquiry has been successfully submitted! We will reach out shortly.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Server database error: {str(e)}'}), 500

# Startup database initialization
with app.app_context():
    db.create_all()
    # Seed members if empty
    if not Member.query.first():
        default_members = [
            Member(
                name="Isaac Olusola",
                role="Founder & Managing Director",
                bio="Isaac is the visionary behind Ziglag Institute, dedicated to providing premium and accessible STEM education. He guides the institute's strategic curriculum development and partnerships.",
                avatar="🚀",
                email="isaac.olusola@ziglaginstitute.com",
                linkedin="https://www.linkedin.com/in/isaac-olusola-2a2b2218b",
                github="https://github.com/ziglaginstitute-del",
                youtube="https://youtube.com/@ziglaginstitute?si=pb96DBtz9CQRfpbn",
                display_order=1
            ),
            Member(
                name="Dr. Adrian Thorne",
                role="Head of Pure Mathematics",
                bio="Adrian holds a PhD in Pure Mathematics. He specializes in making abstract concepts (like vector spaces and real analysis) intuitive and deeply interesting for undergraduate students.",
                avatar="👨‍🏫",
                email="adrian.thorne@ziglaginstitute.com",
                linkedin="https://linkedin.com",
                github="https://github.com",
                display_order=2
            ),
            Member(
                name="Sarah Jenkins, MSc",
                role="Lead Exam Prep Coach & Coordinator",
                bio="Sarah is a passionate high school educator with 10+ years of tutoring. She focuses on confidence-building and breaking down exam techniques for WASSCE, JAMB, AP, and IGCSE.",
                avatar="👩‍🏫",
                email="sarah.jenkins@ziglaginstitute.com",
                linkedin="https://linkedin.com",
                github="https://github.com",
                display_order=3
            ),
            Member(
                name="Prof. Marcus Vance",
                role="Emeritus Advisor & Content Author",
                bio="Marcus is a retired professor and author of calculus textbooks. His role at Ziglag focuses on verifying core mathematical proof sheets and undergraduate syllabus excellence.",
                avatar="👨‍💻",
                email="marcus.vance@ziglaginstitute.com",
                linkedin="https://linkedin.com",
                github="https://github.com",
                display_order=4
            )
        ]
        db.session.bulk_save_objects(default_members)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
