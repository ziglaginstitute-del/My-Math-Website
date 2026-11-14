import os
import json
import uuid
import logging
import urllib.request
from flask import Flask, send_from_directory, request, jsonify, redirect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Ensure .env is explicitly loaded from project root
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

# Environment detection
IS_VERCEL = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'))

# Ensure upload directories exist safely across standard and serverless environments
if IS_VERCEL:
    COMMUNITY_UPLOADS_DIR = '/tmp/community_uploads'
    VAULT_UPLOADS_DIR = '/tmp/vault_pdfs'
else:
    COMMUNITY_UPLOADS_DIR = os.path.join(BASE_DIR, 'assets', 'community_uploads')
    VAULT_UPLOADS_DIR = os.path.join(BASE_DIR, 'assets', 'vault_pdfs')

try:
    os.makedirs(COMMUNITY_UPLOADS_DIR, exist_ok=True)
    os.makedirs(VAULT_UPLOADS_DIR, exist_ok=True)
except Exception as e:
    logging.warning(f"Could not create upload directories at startup: {e}")

# Set up basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-key-12345')

# CORS handler for cross-origin access (e.g. file:///, localhost dev, or external origins)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

@app.route('/api/<path:dummy>', methods=['OPTIONS'])
def options_preflight(dummy=''):
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response


# ============================================================================
# NEON CLOUD SERVICES CONFIGURATION (Postgres, Auth, Functions, AI, Realtime)
# ============================================================================
NEON_BRANCH = os.getenv('NEON_BRANCH', 'production')
NEON_BRANCH_ID = os.getenv('NEON_BRANCH_ID', '')
NEON_AUTH_BASE_URL = os.getenv('NEON_AUTH_BASE_URL', '')
NEON_AUTH_JWKS_URL = os.getenv('NEON_AUTH_JWKS_URL', '')
NEON_FUNCTION_HOST_SUFFIX = os.getenv('NEON_FUNCTION_HOST_SUFFIX', '')
NEON_AI_GATEWAY_TOKEN = os.getenv('NEON_AI_GATEWAY_TOKEN', '')
NEON_AI_GATEWAY_BASE_URL = os.getenv('NEON_AI_GATEWAY_BASE_URL', '')
NEON_REALTIME_URL = os.getenv('NEON_REALTIME_URL', '')
NEON_REALTIME_SECRET = os.getenv('NEON_REALTIME_SECRET', '')

# Database URI configuration: Works with local SQLite or free Neon Serverless PostgreSQL
db_url = os.getenv('DATABASE_URL')
if not db_url:
    if IS_VERCEL:
        sqlite_path = '/tmp/math_portal.db'
    else:
        instance_dir = os.path.join(BASE_DIR, "instance")
        try:
            os.makedirs(instance_dir, exist_ok=True)
        except Exception:
            pass
        sqlite_path = os.path.join(instance_dir, "math_portal.db")
    db_url = f'sqlite:///{sqlite_path}'

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Ensure SQLAlchemy driver prefix matches the installed psycopg driver
if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    try:
        import psycopg
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        try:
            import psycopg2
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            pass

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300
}

db = SQLAlchemy(app)

# ============================================================================
# 1. DATABASE MODELS
# ============================================================================

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
    avatar = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    github = db.Column(db.String(200), nullable=True)
    youtube = db.Column(db.String(200), nullable=True)
    display_order = db.Column(db.Integer, default=0)

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.String(100), primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False) # Reg / Docket Number
    password = db.Column(db.String(100), default='123456')
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    category = db.Column(db.String(50), default='Science')
    exam_type = db.Column(db.String(50), default='JAMB UTME')
    registered_subjects = db.Column(db.Text, default='["english", "mathematics", "physics", "chemistry"]')
    center = db.Column(db.String(150), default='Ziglag CBT Center Lagos')
    seat_number = db.Column(db.String(50), default='Seat 01')
    status = db.Column(db.String(50), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            subjs = json.loads(self.registered_subjects) if self.registered_subjects else []
        except Exception:
            subjs = ["english", "mathematics", "physics", "chemistry"]
        return {
            'id': self.id,
            'full_name': self.full_name,
            'username': self.username,
            'reg_number': self.username,
            'email': self.email or '',
            'phone': self.phone or '',
            'category': self.category or 'Science',
            'exam_type': self.exam_type or 'JAMB UTME',
            'registered_subjects': subjs,
            'center': self.center or 'Ziglag CBT Center Lagos',
            'seat_number': self.seat_number or 'Seat 01',
            'status': self.status or 'Active',
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(50), nullable=True)
    icon = db.Column(db.String(20), default='📚')
    category = db.Column(db.String(50), default='General')
    question_count = db.Column(db.Integer, default=0)
    default_duration = db.Column(db.Integer, default=40)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # Calculate live question count
        live_count = Question.query.filter_by(subject=self.id).count()
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code or self.id.upper(),
            'icon': self.icon or '📚',
            'category': self.category or 'General',
            'question_count': live_count,
            'default_duration': self.default_duration or 40,
            'is_active': self.is_active
        }

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.String(100), primary_key=True)
    subject = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), default='General')
    difficulty = db.Column(db.String(50), default='Intermediate')
    exam_type = db.Column(db.String(50), default='jamb')
    question_text = db.Column(db.Text, nullable=False)
    passage = db.Column(db.Text, nullable=True)
    options = db.Column(db.Text, default='[]')
    correct_option = db.Column(db.String(10), nullable=False)
    hint = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    year = db.Column(db.Integer, default=2026)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            opts = json.loads(self.options) if self.options else []
        except Exception:
            opts = []
        return {
            'id': self.id,
            'subject': self.subject,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'exam_type': self.exam_type,
            'question_text': self.question_text,
            'question': self.question_text,
            'passage': self.passage,
            'options': opts,
            'correct_option': self.correct_option,
            'correctOption': self.correct_option,
            'correct': self.correct_option,
            'hint': self.hint or '',
            'explanation': self.explanation or '',
            'year': self.year or 2026,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class ScheduledExam(db.Model):
    __tablename__ = 'scheduled_exams'
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    access_code = db.Column(db.String(50), nullable=False)
    exam_type = db.Column(db.String(50), default='jamb')
    duration_minutes = db.Column(db.Integer, default=120)
    subject_ids = db.Column(db.Text, default='["english", "mathematics", "physics", "chemistry"]')
    starts_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            subjs = json.loads(self.subject_ids) if self.subject_ids else []
        except Exception:
            subjs = []
        return {
            'id': self.id,
            'title': self.title,
            'access_code': self.access_code,
            'exam_type': self.exam_type,
            'duration_minutes': self.duration_minutes,
            'subject_ids': subjs,
            'starts_at': self.starts_at.isoformat() if self.starts_at else '',
            'ends_at': self.ends_at.isoformat() if self.ends_at else '',
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class ExamHistory(db.Model):
    __tablename__ = 'exam_history'
    id = db.Column(db.String(100), primary_key=True)
    candidate_id = db.Column(db.String(100), nullable=True)
    candidate_name = db.Column(db.String(150), nullable=True)
    candidate_reg = db.Column(db.String(100), nullable=True)
    scheduled_exam_id = db.Column(db.String(100), nullable=True)
    exam_type = db.Column(db.String(50), default='JAMB UTME')
    score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=400)
    percentage = db.Column(db.Float, default=0.0)
    time_spent_seconds = db.Column(db.Integer, default=0)
    subject_scores = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            sub_scores = json.loads(self.subject_scores) if self.subject_scores else {}
        except Exception:
            sub_scores = {}
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'candidate_name': self.candidate_name,
            'candidate_reg': self.candidate_reg,
            'scheduled_exam_id': self.scheduled_exam_id,
            'exam_type': self.exam_type,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'time_spent_seconds': self.time_spent_seconds,
            'subject_scores': sub_scores,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), default='General')
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(20), default='📐')
    badge = db.Column(db.String(50), default='Comprehensive')
    instructor = db.Column(db.String(100), default='Mr. Isaac Olusola')
    duration_weeks = db.Column(db.Integer, default=6)
    syllabus_json = db.Column(db.Text, default='[]')
    display_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            syl = json.loads(self.syllabus_json) if self.syllabus_json else []
        except Exception:
            syl = []
        weeks = self.duration_weeks or 6
        dur_display = f"{weeks * 5} Hours"
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'category': self.category,
            'subcategory': self.subcategory or 'General',
            'subcat': self.subcategory or 'General',
            'sphere': self.category,
            'description': self.description or '',
            'shortDesc': self.description or '',
            'icon': self.icon or '📐',
            'imageIcon': self.icon or '📐',
            'badge': self.badge or 'Comprehensive',
            'level': self.badge or 'Comprehensive',
            'instructor': self.instructor or 'Mr. Isaac Olusola',
            'duration_weeks': weeks,
            'duration': dur_display,
            'syllabus': syl if (isinstance(syl, list) and len(syl) > 0) else ['Foundational Principles', 'Worked Examples', 'Past Question Walkthrough', 'Exam Mastery Challenge'],
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class Lecture(db.Model):
    __tablename__ = 'lectures'
    id = db.Column(db.String(100), primary_key=True)
    course_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    topic_category = db.Column(db.String(150), default='General')
    description = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.String(50), default='30 mins')
    order_index = db.Column(db.Integer, default=1)
    notes_url = db.Column(db.String(500), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        topic = self.topic_category or 'General'
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'topic_category': topic,
            'group': topic,
            'topic': topic,
            'description': self.description or '',
            'video_url': self.video_url,
            'videoUrl': self.video_url,
            'duration': self.duration or '30 mins',
            'length': self.duration or '30 mins',
            'order_index': self.order_index,
            'notes_url': self.notes_url or '',
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class VaultResource(db.Model):
    __tablename__ = 'vault_resources'
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), default='General')
    file_url = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.String(50), default='1.5 MB')
    badge = db.Column(db.String(50), default='PDF')
    description = db.Column(db.Text, nullable=True)
    downloads_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'subcategory': self.subcategory or 'General',
            'subcat': self.subcategory or 'General',
            'file_url': self.file_url,
            'fileUrl': self.file_url,
            'file_size': self.file_size or '1.5 MB',
            'size': self.file_size or '1.5 MB',
            'badge': self.badge or 'PDF Bundle',
            'type': self.badge or 'PDF Bundle',
            'description': self.description or '',
            'downloads_count': self.downloads_count,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        try:
            val = json.loads(self.value)
        except Exception:
            val = self.value
        return {
            'key': self.key,
            'value': val,
            'updated_at': self.updated_at.isoformat() if self.updated_at else ''
        }


class TutoringBooking(db.Model):
    __tablename__ = 'tutoring_bookings'
    id = db.Column(db.String(100), primary_key=True)
    student_name = db.Column(db.String(150), nullable=False)
    student_email = db.Column(db.String(150), nullable=False)
    student_phone = db.Column(db.String(50), nullable=True)
    instructor_name = db.Column(db.String(100), default="Mr. Isaac Olusola")
    instructor_email = db.Column(db.String(150), default="ziglaginstitute@gmail.com")
    subject = db.Column(db.String(150), nullable=False)
    exam_category = db.Column(db.String(50), default="Local")  # 'Local' or 'International'
    topic = db.Column(db.Text, nullable=False)
    difficulties = db.Column(db.Text, nullable=True)
    booking_date = db.Column(db.String(50), nullable=False)
    booking_time = db.Column(db.String(50), nullable=False)
    duration_hours = db.Column(db.Float, default=1.0)
    hourly_rate = db.Column(db.Float, default=15.0)
    total_price = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(20), default="USD")
    status = db.Column(db.String(50), default="Confirmed")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student_name,
            'student_email': self.student_email,
            'student_phone': self.student_phone or '',
            'instructor_name': self.instructor_name,
            'instructor_email': self.instructor_email,
            'subject': self.subject,
            'exam_category': self.exam_category,
            'topic': self.topic,
            'difficulties': self.difficulties or '',
            'booking_date': self.booking_date,
            'booking_time': self.booking_time,
            'duration_hours': self.duration_hours,
            'hourly_rate': self.hourly_rate,
            'total_price': self.total_price,
            'currency': self.currency,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }


class CommunityQuestion(db.Model):
    __tablename__ = 'community_questions'
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    subject = db.Column(db.String(100), default='Mathematics')  # Mathematics, Physics, Chemistry, Further Mathematics
    difficulty = db.Column(db.String(50), default='Intermediate')  # Beginner, Intermediate, Advanced
    content_latex = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(150), default='Anonymous Scholar')
    author_email = db.Column(db.String(150), nullable=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_name = db.Column(db.String(200), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)  # 'image' or 'pdf'
    views = db.Column(db.Integer, default=0)
    upvotes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='Open')  # 'Open', 'Solved'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    answers = db.relationship('CommunityAnswer', backref='question', cascade='all, delete-orphan', lazy=True)

    @property
    def answers_count(self):
        return len(self.answers) if self.answers is not None else 0

    def to_dict(self, include_answers=False):
        ans_list = self.answers if self.answers is not None else []
        ans_count = len(ans_list)
        has_educator = any(a.is_educator for a in ans_list)
        res = {
            'id': self.id,
            'title': self.title,
            'subject': self.subject or 'Mathematics',
            'difficulty': self.difficulty or 'Intermediate',
            'content_latex': self.content_latex,
            'content': self.content_latex,
            'author_name': self.author_name or 'Anonymous Scholar',
            'author_email': self.author_email or '',
            'attachment_url': self.attachment_url or '',
            'attachment_name': self.attachment_name or '',
            'attachment_type': self.attachment_type or '',
            'views': self.views or 0,
            'upvotes': self.upvotes or 0,
            'status': self.status or 'Open',
            'answers_count': ans_count,
            'has_educator_answer': has_educator,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }
        if include_answers:
            sorted_answers = sorted(ans_list, key=lambda a: (not a.is_educator, -a.upvotes, a.created_at or datetime.min))
            res['answers'] = [a.to_dict() for a in sorted_answers]
        return res


class CommunityAnswer(db.Model):
    __tablename__ = 'community_answers'
    id = db.Column(db.String(100), primary_key=True)
    question_id = db.Column(db.String(100), db.ForeignKey('community_questions.id', ondelete='CASCADE'), nullable=False)
    author_name = db.Column(db.String(150), default='Anonymous Contributor')
    author_email = db.Column(db.String(150), nullable=True)
    is_educator = db.Column(db.Boolean, default=False)
    content_latex = db.Column(db.Text, nullable=False)
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_name = db.Column(db.String(200), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)
    upvotes = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'author_name': self.author_name or 'Anonymous Contributor',
            'author_email': self.author_email or '',
            'is_educator': self.is_educator,
            'content_latex': self.content_latex,
            'content': self.content_latex,
            'attachment_url': self.attachment_url or '',
            'attachment_name': self.attachment_name or '',
            'attachment_type': self.attachment_type or '',
            'upvotes': self.upvotes or 0,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

# ============================================================================
# 2. PAGE ROUTES
# ============================================================================

def _safe_send_html(filename):
    for candidate_dir in [
        BASE_DIR,
        os.path.join(BASE_DIR, '..'),
        os.getcwd(),
        '/var/task',
        '/vercel/path0'
    ]:
        try:
            target = os.path.join(candidate_dir, filename)
            if os.path.isfile(target):
                return send_from_directory(candidate_dir, filename)
        except Exception:
            pass
    try:
        return send_from_directory(BASE_DIR, filename)
    except Exception:
        return jsonify({'error': f'{filename} not found'}), 404

@app.route('/')
def home():
    return _safe_send_html('index.html')

@app.route('/index.html')
def index():
    return _safe_send_html('index.html')

@app.route('/courses.html')
def courses():
    return _safe_send_html('courses.html')

@app.route('/cbt.html')
@app.route('/cbt')
def cbt_redirect():
    target = os.getenv('CBT_APP_URL', 'https://cbt-jamb-website-ziglaginstitute-8370s-projects.vercel.app')
    query = request.query_string.decode('utf-8') if request.query_string else ''
    if query:
        sep = '&' if '?' in target else '?'
        target = f"{target}{sep}{query}"
    return redirect(target, code=302)

@app.route('/tutoring.html')
def tutoring():
    return _safe_send_html('tutoring.html')

@app.route('/vault.html')
def vault():
    return _safe_send_html('vault.html')

@app.route('/course-view.html')
def course_view():
    return _safe_send_html('course-view.html')

@app.route('/contact.html')
def contact_page():
    return _safe_send_html('contact.html')

@app.route('/qa.html')
@app.route('/qa')
def qa_page():
    return _safe_send_html('qa.html')

@app.route('/about.html')
@app.route('/about')
def about_page():
    return _safe_send_html('about.html')

@app.route('/people.html')
@app.route('/people')
def people_page():
    return redirect('/about.html#people', code=302)

@app.route('/admin.html')
def admin_page():
    return _safe_send_html('admin.html')

@app.route('/admin')
def admin_alias():
    return _safe_send_html('admin.html')

# ============================================================================
# 3. DATABASE REST API ENDPOINTS (Zero Vendor Lock-In)
# ============================================================================


# ============================================================================
# NEON CLOUD SERVICES REST APIs (Postgres, Auth, AI Gateway, Functions, Realtime)
# ============================================================================

@app.route('/api/neon/services', methods=['GET'])
def get_neon_services():
    """Comprehensive status and health audit for all 5 deployed Neon services."""
    from sqlalchemy import text
    services = {
        'postgres': {'connected': False, 'details': {}},
        'auth': {'connected': False, 'details': {}},
        'ai_gateway': {'connected': False, 'details': {}},
        'functions': {'connected': False, 'details': {}},
        'realtime': {'connected': False, 'details': {}}
    }
    current_txid = None

    # 1. Lakebase Postgres
    try:
        res = db.session.execute(text("SELECT version(), current_database(), pg_current_xact_id()::text")).fetchone()
        current_txid = res[2] if res else None
        services['postgres'] = {
            'connected': True,
            'version': res[0].split()[0] + ' ' + res[0].split()[1] if res else 'PostgreSQL',
            'database': res[1] if res else 'neondb',
            'branch': NEON_BRANCH,
            'branch_id': NEON_BRANCH_ID,
            'pooled_url_active': True,
            'candidates_count': Candidate.query.count(),
            'questions_count': Question.query.count(),
            'exams_count': ScheduledExam.query.count()
        }
    except Exception as e:
        services['postgres'] = {'connected': False, 'error': str(e)}

    # 2. Neon Auth (Managed Better Auth)
    if NEON_AUTH_BASE_URL:
        try:
            req = urllib.request.Request(f"{NEON_AUTH_BASE_URL}/ok", headers={'User-Agent': 'ZiglagMathPortal/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                services['auth'] = {
                    'connected': resp.status == 200,
                    'base_url': NEON_AUTH_BASE_URL,
                    'jwks_url': NEON_AUTH_JWKS_URL,
                    'status': 'Managed Better Auth Active'
                }
        except Exception as e:
            services['auth'] = {'connected': False, 'error': str(e), 'base_url': NEON_AUTH_BASE_URL}
    else:
        services['auth'] = {'connected': False, 'status': 'Not configured'}

    # 3. Neon AI Gateway (Databricks Multi-Model Engine)
    if NEON_AI_GATEWAY_BASE_URL and NEON_AI_GATEWAY_TOKEN:
        try:
            req = urllib.request.Request(
                f"{NEON_AI_GATEWAY_BASE_URL}/v1/models",
                headers={'Authorization': f'Bearer {NEON_AI_GATEWAY_TOKEN}', 'User-Agent': 'ZiglagMathPortal/1.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models_list = data.get('data', [])
                services['ai_gateway'] = {
                    'connected': resp.status == 200,
                    'models_available': len(models_list),
                    'sample_models': [m.get('id') for m in models_list[:5]],
                    'base_url': NEON_AI_GATEWAY_BASE_URL,
                    'status': 'Databricks AI Gateway Active'
                }
        except Exception as e:
            services['ai_gateway'] = {'connected': False, 'error': str(e), 'base_url': NEON_AI_GATEWAY_BASE_URL}
    else:
        services['ai_gateway'] = {'connected': False, 'status': 'Not configured'}

    # 4. Neon Functions (Serverless HTTP Compute)
    clean_suffix = NEON_FUNCTION_HOST_SUFFIX.lstrip('.')
    fn_url = f"https://{NEON_BRANCH_ID}-hello.{clean_suffix}/" if NEON_FUNCTION_HOST_SUFFIX and NEON_BRANCH_ID else None
    if fn_url:
        try:
            req = urllib.request.Request(fn_url, headers={'User-Agent': 'ZiglagMathPortal/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode()
                services['functions'] = {
                    'connected': resp.status == 200,
                    'url': fn_url,
                    'status': 'Deployed & Ready',
                    'response': body.strip()
                }
        except Exception as e:
            services['functions'] = {'connected': False, 'error': str(e), 'url': fn_url}
    else:
        services['functions'] = {'connected': False, 'status': 'Function host suffix not set'}

    # 5. Neon Realtime (Live Reactive Sync)
    if NEON_REALTIME_URL:
        services['realtime'] = {
            'connected': True,
            'realtime_url': NEON_REALTIME_URL,
            'current_txid': current_txid,
            'secret_configured': bool(NEON_REALTIME_SECRET),
            'status': 'Realtime Live Query Engine Active'
        }
    else:
        services['realtime'] = {'connected': False, 'status': 'Not configured'}

    return jsonify({
        'success': True,
        'organization': 'Ziglag (org-proud-scene-10289145)',
        'project': 'nameless-frost-15881262',
        'branch': NEON_BRANCH,
        'services': services
    })

@app.route('/api/neon/auth/config', methods=['GET'])
def neon_auth_config():
    """Public auth endpoint configuration for frontend client."""
    return jsonify({
        'success': True,
        'base_url': NEON_AUTH_BASE_URL,
        'jwks_url': NEON_AUTH_JWKS_URL,
        'active': bool(NEON_AUTH_BASE_URL)
    })

@app.route('/api/neon/ai/models', methods=['GET'])
def neon_ai_models():
    """Retrieve available AI models from the Neon AI Gateway."""
    if not NEON_AI_GATEWAY_BASE_URL or not NEON_AI_GATEWAY_TOKEN:
        return jsonify({'success': False, 'message': 'AI Gateway credentials not configured'}), 500
    try:
        req = urllib.request.Request(
            f"{NEON_AI_GATEWAY_BASE_URL}/v1/models",
            headers={'Authorization': f'Bearer {NEON_AI_GATEWAY_TOKEN}'}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return jsonify({'success': True, 'models': data.get('data', [])})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/neon/ai/math-assistant', methods=['POST'])
def neon_ai_math_assistant():
    """Real-time STEM / Math AI assistant for JAMB & WASSCE questions."""
    if not NEON_AI_GATEWAY_BASE_URL or not NEON_AI_GATEWAY_TOKEN:
        return jsonify({'success': False, 'message': 'AI Gateway credentials not configured'}), 500
    
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'success': False, 'message': 'Question prompt required.'}), 400
        
    model = data.get('model', 'gemini-2.5-flash')
    system_instruction = (
        "You are Ziglag AI, an expert mathematics, physics, and STEM tutor for Nigerian JAMB UTME "
        "and WASSCE candidates. Give concise, step-by-step explanations, highlighting formula derivations "
        "and final answers clearly."
    )
    
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': question}
        ],
        'temperature': 0.2
    }
    
    try:
        body = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{NEON_AI_GATEWAY_BASE_URL}/v1/chat/completions",
            data=body,
            headers={
                'Authorization': f'Bearer {NEON_AI_GATEWAY_TOKEN}',
                'Content-Type': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode())
            reply = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            return jsonify({'success': True, 'answer': reply, 'model': model})
    except Exception as e:
        # If no prepaid credits on free tier, handle gracefully
        err_str = str(e)
        return jsonify({
            'success': False, 
            'error': err_str,
            'note': 'Neon AI Gateway is connected. Prepaid credits can be activated at https://console.neon.tech/app/org-proud-scene-10289145/billing'
        }), 500

@app.route('/api/neon/functions/invoke', methods=['GET', 'POST'])
def neon_functions_invoke():
    """Invokes a deployed Neon branch function (e.g. hello)."""
    fn_name = request.args.get('name', 'hello')
    clean_suffix = (NEON_FUNCTION_HOST_SUFFIX or '').lstrip('.')
    if not clean_suffix or not NEON_BRANCH_ID:
        return jsonify({'success': False, 'message': 'Neon functions suffix or branch ID not set'}), 500

    fn_url = f"https://{NEON_BRANCH_ID}-{fn_name}.{clean_suffix}/"
    try:
        body = request.get_data() if request.method == 'POST' else None
        req = urllib.request.Request(
            fn_url,
            data=body,
            headers={'User-Agent': 'ZiglagMathPortal/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            output = resp.read().decode()
            return jsonify({'success': True, 'function': fn_name, 'url': fn_url, 'output': output.strip()})
    except Exception as e:
        return jsonify({'success': False, 'function': fn_name, 'url': fn_url, 'error': str(e)}), 500

@app.route('/api/neon/realtime/info', methods=['GET'])
def neon_realtime_info():
    """Returns Neon Realtime WebSocket connection info and current transaction watermark."""
    from sqlalchemy import text
    txid = None
    try:
        res = db.session.execute(text("SELECT pg_current_xact_id()::text")).fetchone()
        txid = res[0] if res else None
    except Exception:
        pass
    return jsonify({
        'success': True,
        'realtime_url': NEON_REALTIME_URL,
        'secret_configured': bool(NEON_REALTIME_SECRET),
        'current_txid': txid,
        'branch': NEON_BRANCH,
        'active': bool(NEON_REALTIME_URL)
    })

@app.route('/api/db-status', methods=['GET'])
def get_db_status():
    provider = "Neon / PostgreSQL" if "postgresql" in app.config['SQLALCHEMY_DATABASE_URI'] else "SQLite (Free Local Database)"
    try:
        cand_count = Candidate.query.count()
        q_count = Question.query.count()
        exam_count = ScheduledExam.query.count()
        return jsonify({
            'success': True,
            'connected': True,
            'provider': provider,
            'candidates_count': cand_count,
            'questions_count': q_count,
            'exams_count': exam_count
        })
    except Exception as e:
        return jsonify({'success': False, 'connected': False, 'error': str(e)}), 500


# ============================================================================
# PREPCBT ADMIN SUITE APIS (Subjects, Candidate Reset/Delete, Bulk, Question Export)
# ============================================================================

# Global Result Release Setting (in-memory with default True)
GLOBAL_RESULTS_RELEASED = True

@app.route('/api/exams/release-status', methods=['GET', 'POST'])
def exams_release_status():
    global GLOBAL_RESULTS_RELEASED
    if request.method == 'POST':
        data = request.get_json() or {}
        GLOBAL_RESULTS_RELEASED = bool(data.get('released', True))
        return jsonify({'success': True, 'released': GLOBAL_RESULTS_RELEASED})
    return jsonify({'success': True, 'released': GLOBAL_RESULTS_RELEASED})

@app.route('/api/subjects', methods=['GET', 'POST'])
def handle_subjects():
    if request.method == 'POST':
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        sub_id = (data.get('id') or name.lower().replace(' ', '_')).strip()
        if not name:
            return jsonify({'success': False, 'message': 'Subject name is required.'}), 400
        
        existing = Subject.query.filter_by(id=sub_id).first()
        if existing:
            return jsonify({'success': True, 'subject': existing.to_dict(), 'message': 'Already exists'})
            
        new_sub = Subject(
            id=sub_id,
            name=name,
            code=data.get('code', sub_id[:4].upper()),
            icon=data.get('icon', '📚'),
            category=data.get('category', 'Science'),
            default_duration=int(data.get('default_duration', 40)),
            is_active=True
        )
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({'success': True, 'subject': new_sub.to_dict()})
        
    subs = Subject.query.order_by(Subject.name.asc()).all()
    return jsonify([s.to_dict() for s in subs])

@app.route('/api/subjects/<sub_id>', methods=['DELETE'])
def delete_subject(sub_id):
    sub = Subject.query.filter_by(id=sub_id).first()
    if not sub:
        return jsonify({'success': False, 'message': 'Subject not found'}), 404
    db.session.delete(sub)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Subject {sub_id} deleted.'})

@app.route('/api/candidates/bulk', methods=['POST'])
def bulk_register_candidates():
    payload = request.get_json() or []
    if isinstance(payload, dict) and 'candidates' in payload:
        data = payload['candidates']
    elif isinstance(payload, list):
        data = payload
    else:
        return jsonify({'success': False, 'message': 'Array of candidates expected'}), 400
        
    saved = []
    for item in data:
        name = (item.get('full_name') or item.get('name') or '').strip()
        if not name:
            continue
        reg = (item.get('username') or item.get('reg_number') or f"ZIG/{int(datetime.utcnow().timestamp())}").strip().upper()
        existing = Candidate.query.filter_by(username=reg).first()
        if existing:
            saved.append(existing.to_dict())
            continue
            
        cand = Candidate(
            id=item.get('id') or f"cand_{int(datetime.utcnow().timestamp())}_{os.urandom(3).hex()}",
            full_name=name,
            username=reg,
            password=item.get('password', '123456'),
            email=item.get('email', ''),
            phone=item.get('phone', ''),
            category=item.get('category', 'Science'),
            exam_type=item.get('exam_type', 'JAMB UTME'),
            registered_subjects=json.dumps(item.get('registered_subjects', ["english", "mathematics", "physics", "chemistry"])),
            center=item.get('center', 'PrepCBT Center 01 (Main Auditorium)'),
            seat_number=item.get('seat_number', f"Seat {int(os.urandom(1)[0] % 60 + 1)}"),
            status='Active'
        )
        db.session.add(cand)
        saved.append(cand.to_dict())
        
    db.session.commit()
    return jsonify({'success': True, 'count': len(saved), 'candidates': saved})

@app.route('/api/candidates/<cand_id>', methods=['DELETE'])
def delete_candidate(cand_id):
    cand = Candidate.query.filter((Candidate.id == cand_id) | (Candidate.username == cand_id)).first()
    if not cand:
        return jsonify({'success': False, 'message': 'Candidate not found'}), 404
    # Also delete exam history for this candidate
    ExamHistory.query.filter((ExamHistory.candidate_id == cand.id) | (ExamHistory.candidate_reg == cand.username)).delete()
    db.session.delete(cand)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Candidate deleted successfully'})

@app.route('/api/candidates/<cand_id>/reset', methods=['POST'])
def reset_candidate(cand_id):
    cand = Candidate.query.filter((Candidate.id == cand_id) | (Candidate.username == cand_id)).first()
    if not cand:
        return jsonify({'success': False, 'message': 'Candidate not found'}), 404
    cand.status = 'Active'
    # Delete previous exam history
    ExamHistory.query.filter((ExamHistory.candidate_id == cand.id) | (ExamHistory.candidate_reg == cand.username)).delete()
    db.session.commit()
    return jsonify({'success': True, 'message': f'Exam authorization reset for {cand.full_name}. Candidate can re-sit.'})

@app.route('/api/questions/<q_id>', methods=['DELETE', 'PUT'])
def handle_single_question(q_id):
    q = Question.query.filter_by(id=q_id).first()
    if not q:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
        
    if request.method == 'DELETE':
        db.session.delete(q)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Question deleted'})
        
    data = request.get_json() or {}
    q.subject = (data.get('subject') or q.subject).lower()
    q.topic = data.get('topic', q.topic)
    q.difficulty = data.get('difficulty', q.difficulty)
    q.exam_type = data.get('exam_type', q.exam_type)
    q.question_text = data.get('question_text') or data.get('question') or q.question_text
    q.passage = data.get('passage', q.passage)
    if 'options' in data:
        q.options = json.dumps(data.get('options', []))
    q.correct_option = data.get('correct_option') or data.get('correctOption') or q.correct_option
    q.hint = data.get('hint', q.hint)
    q.explanation = data.get('explanation', q.explanation)
    q.year = int(data.get('year', q.year or 2026))
    db.session.commit()
    return jsonify({'success': True, 'question': q.to_dict()})

@app.route('/api/questions/export', methods=['GET'])
def export_questions():
    questions = Question.query.all()
    return jsonify({
        'app': 'PrepCBT',
        'export_date': datetime.utcnow().isoformat(),
        'total_questions': len(questions),
        'questions': [q.to_dict() for q in questions]
    })

@app.route('/api/questions/import', methods=['POST'])
def import_questions():
    data = request.get_json() or {}
    q_list = data.get('questions', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    
    count = 0
    for q_data in q_list:
        q_id = q_data.get('id') or f"q_{int(datetime.utcnow().timestamp())}_{os.urandom(3).hex()}"
        existing = Question.query.filter_by(id=q_id).first()
        opts = q_data.get('options') or []
        opts_json = json.dumps(opts) if isinstance(opts, list) else opts
        
        if existing:
            existing.question_text = q_data.get('question_text') or q_data.get('question', existing.question_text)
            existing.options = opts_json
            existing.correct_option = q_data.get('correct_option') or q_data.get('correctOption', existing.correct_option)
            existing.explanation = q_data.get('explanation', existing.explanation)
            existing.passage = q_data.get('passage', existing.passage)
        else:
            new_q = Question(
                id=q_id,
                subject=(q_data.get('subject') or 'mathematics').lower(),
                topic=q_data.get('topic', 'General'),
                difficulty=q_data.get('difficulty', 'Intermediate'),
                exam_type=q_data.get('exam_type', 'jamb'),
                question_text=q_data.get('question_text') or q_data.get('question', ''),
                passage=q_data.get('passage'),
                options=opts_json,
                correct_option=q_data.get('correct_option') or q_data.get('correctOption', 'A'),
                hint=q_data.get('hint', ''),
                explanation=q_data.get('explanation', ''),
                year=int(q_data.get('year', 2026))
            )
            db.session.add(new_q)
        count += 1
        
    db.session.commit()
    return jsonify({'success': True, 'count': count})

@app.route('/api/exams/<exam_id>', methods=['DELETE', 'PUT'])
def handle_single_exam(exam_id):
    exam = ScheduledExam.query.filter_by(id=exam_id).first()
    if not exam:
        return jsonify({'success': False, 'message': 'Mock exam not found'}), 404
        
    if request.method == 'DELETE':
        db.session.delete(exam)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Mock exam deleted'})
        
    data = request.get_json() or {}
    if 'is_active' in data:
        exam.is_active = bool(data.get('is_active'))
    if 'title' in data:
        exam.title = data.get('title')
    if 'access_code' in data:
        exam.access_code = data.get('access_code')
    if 'duration_minutes' in data:
        exam.duration_minutes = int(data.get('duration_minutes', 120))
    db.session.commit()
    return jsonify({'success': True, 'exam': exam.to_dict()})

# CANDIDATES API
@app.route('/api/candidates', methods=['GET'])
def list_candidates():
    candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
    return jsonify([c.to_dict() for c in candidates])

@app.route('/api/candidates/verify', methods=['POST'])
def verify_candidate():
    data = request.get_json() or {}
    reg = (data.get('reg_number') or data.get('username') or '').strip()
    if not reg:
        return jsonify({'success': False, 'message': 'Registration number required.'}), 400

    cand = Candidate.query.filter(
        (Candidate.username.ilike(reg)) | (Candidate.id.ilike(reg))
    ).first()

    if cand:
        return jsonify({'success': True, 'candidate': cand.to_dict()})
    return jsonify({'success': False, 'message': 'Candidate docket not found.'}), 404

@app.route('/api/candidates/register', methods=['POST'])
def register_candidate():
    data = request.get_json() or {}
    name = (data.get('full_name') or data.get('name') or '').strip()
    reg = (data.get('username') or data.get('reg_number') or f"ZIG/{int(datetime.utcnow().timestamp())}").strip().upper()

    if not name:
        return jsonify({'success': False, 'message': 'Full name is required.'}), 400

    existing = Candidate.query.filter_by(username=reg).first()
    if existing:
        return jsonify({'success': True, 'candidate': existing.to_dict(), 'message': 'Already registered'})

    cand_id = data.get('id') or f"cand_{int(datetime.utcnow().timestamp())}_{os.urandom(3).hex()}"
    new_cand = Candidate(
        id=cand_id,
        full_name=name,
        username=reg,
        password=data.get('password', '123456'),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        category=data.get('category', 'Science'),
        exam_type=data.get('exam_type', 'JAMB UTME'),
        registered_subjects=json.dumps(data.get('registered_subjects', ["english", "mathematics", "physics", "chemistry"])),
        center=data.get('center', 'Ziglag CBT Center Lagos'),
        seat_number=data.get('seat_number', f"Seat {int(os.urandom(1)[0] % 60 + 1)}"),
        status='Active'
    )
    db.session.add(new_cand)
    db.session.commit()
    return jsonify({'success': True, 'candidate': new_cand.to_dict()})

# QUESTIONS API
@app.route('/api/questions', methods=['GET', 'POST'])
def handle_questions():
    if request.method == 'POST':
        data = request.get_json() or {}
        q_id = data.get('id') or f"q_{int(datetime.utcnow().timestamp())}_{os.urandom(3).hex()}"
        options = data.get('options', [])
        if isinstance(options, list):
            options_str = json.dumps(options)
        else:
            options_str = str(options)

        q = Question(
            id=q_id,
            subject=(data.get('subject') or 'mathematics').lower(),
            topic=data.get('topic', 'General'),
            difficulty=data.get('difficulty', 'Intermediate'),
            exam_type=data.get('exam_type', 'jamb'),
            question_text=data.get('question_text') or data.get('question', ''),
            passage=data.get('passage'),
            options=options_str,
            correct_option=(data.get('correct_option') or data.get('correctOption') or 'A').upper(),
            hint=data.get('hint', ''),
            explanation=data.get('explanation', ''),
            year=int(data.get('year') or 2026)
        )
        db.session.add(q)
        db.session.commit()
        return jsonify({'success': True, 'question': q.to_dict()})

    # GET
    subject = request.args.get('subject')
    limit = int(request.args.get('limit') or 100)
    query = Question.query
    if subject:
        query = query.filter(Question.subject == subject.lower())
    questions = query.order_by(Question.created_at.desc()).limit(limit).all()
    return jsonify([q.to_dict() for q in questions])

@app.route('/api/questions/bulk', methods=['POST'])
def bulk_insert_questions():
    data = request.get_json() or []
    if not isinstance(data, list):
        return jsonify({'success': False, 'message': 'Expected array of questions.'}), 400

    added = []
    for item in data:
        q_id = item.get('id') or f"q_{int(datetime.utcnow().timestamp())}_{os.urandom(3).hex()}"
        options = item.get('options', [])
        options_str = json.dumps(options) if isinstance(options, list) else str(options)

        q = Question(
            id=q_id,
            subject=(item.get('subject') or 'mathematics').lower(),
            topic=item.get('topic', 'General'),
            difficulty=item.get('difficulty', 'Intermediate'),
            exam_type=item.get('exam_type', 'jamb'),
            question_text=item.get('question_text') or item.get('question', ''),
            passage=item.get('passage'),
            options=options_str,
            correct_option=(item.get('correct_option') or item.get('correctOption') or 'A').upper(),
            hint=item.get('hint', ''),
            explanation=item.get('explanation', ''),
            year=int(item.get('year') or 2026)
        )
        db.session.add(q)
        added.append(q)

    db.session.commit()
    return jsonify({'success': True, 'count': len(added)})

# SCHEDULED EXAMS API
@app.route('/api/exams', methods=['GET', 'POST'])
def handle_exams():
    if request.method == 'POST':
        data = request.get_json() or {}
        exam_id = data.get('id') or f"mock_{int(datetime.utcnow().timestamp())}"
        subjs = data.get('subject_ids', ["english", "mathematics", "physics", "chemistry"])
        subjs_str = json.dumps(subjs) if isinstance(subjs, list) else str(subjs)

        exam = ScheduledExam(
            id=exam_id,
            title=data.get('title', 'National Mock Examination'),
            access_code=(data.get('access_code') or 'MOCK-2026').upper(),
            exam_type=data.get('exam_type', 'jamb'),
            duration_minutes=int(data.get('duration_minutes') or 120),
            subject_ids=subjs_str,
            starts_at=datetime.fromisoformat(data['starts_at']) if 'starts_at' in data else datetime.utcnow(),
            ends_at=datetime.fromisoformat(data['ends_at']) if 'ends_at' in data else datetime.utcnow(),
            is_active=data.get('is_active', True)
        )
        db.session.add(exam)
        db.session.commit()
        return jsonify({'success': True, 'exam': exam.to_dict()})

    exams = ScheduledExam.query.order_by(ScheduledExam.created_at.desc()).all()
    return jsonify([e.to_dict() for e in exams])

@app.route('/api/exams/submit', methods=['POST'])
def submit_exam_result():
    data = request.get_json() or {}
    hist_id = data.get('id') or f"sub_{int(datetime.utcnow().timestamp())}_{os.urandom(3).hex()}"
    sub_scores = data.get('subject_scores', {})
    sub_scores_str = json.dumps(sub_scores) if isinstance(sub_scores, dict) else str(sub_scores)

    history = ExamHistory(
        id=hist_id,
        candidate_id=data.get('candidate_id'),
        candidate_name=data.get('candidate_name', 'Anonymous'),
        candidate_reg=data.get('candidate_reg', 'PRACTICE'),
        scheduled_exam_id=data.get('scheduled_exam_id'),
        exam_type=data.get('exam_type', 'JAMB UTME'),
        score=int(data.get('score') or 0),
        max_score=int(data.get('max_score') or 400),
        percentage=float(data.get('percentage') or 0.0),
        time_spent_seconds=int(data.get('time_spent_seconds') or 0),
        subject_scores=sub_scores_str
    )
    db.session.add(history)
    db.session.commit()
    return jsonify({'success': True, 'submission': history.to_dict()})

@app.route('/api/exams/history', methods=['GET'])
def get_exam_history():
    history = ExamHistory.query.order_by(ExamHistory.created_at.desc()).limit(100).all()
    return jsonify([h.to_dict() for h in history])

# COURSES & LECTURES API
@app.route('/api/courses', methods=['GET', 'POST'])
def handle_courses():
    if request.method == 'POST':
        data = request.get_json() or {}
        cid = data.get('id') or f"course_{int(datetime.utcnow().timestamp())}"
        slug = data.get('slug') or data.get('title', '').lower().replace(' ', '-')
        syl_data = data.get('syllabus') or []
        syl_str = json.dumps(syl_data) if isinstance(syl_data, list) else str(syl_data)
        course = Course(
            id=cid,
            title=data.get('title'),
            slug=slug,
            category=data.get('category', 'exams'),
            subcategory=data.get('subcategory') or data.get('subcat', 'General'),
            description=data.get('description', ''),
            icon=data.get('icon', '📐'),
            badge=data.get('badge', 'Comprehensive'),
            instructor=data.get('instructor', 'Mr. Isaac Olusola'),
            duration_weeks=int(data.get('duration_weeks') or 6),
            syllabus_json=syl_str,
            display_order=int(data.get('display_order') or 0)
        )
        db.session.add(course)
        db.session.commit()
        return jsonify({'success': True, 'course': course.to_dict()})

    courses = Course.query.order_by(Course.display_order.asc()).all()
    return jsonify([c.to_dict() for c in courses])

@app.route('/api/lectures', methods=['GET', 'POST'])
def handle_lectures():
    if request.method == 'POST':
        data = request.get_json() or {}
        lid = data.get('id') or f"lec_{int(datetime.utcnow().timestamp())}"
        topic_cat = data.get('topic_category') or data.get('group') or data.get('topic') or 'General'
        lec = Lecture(
            id=lid,
            course_id=data.get('course_id') or data.get('courseId'),
            title=data.get('title'),
            topic_category=topic_cat,
            description=data.get('description', ''),
            video_url=data.get('video_url') or data.get('videoUrl'),
            duration=data.get('duration', '30 mins'),
            order_index=int(data.get('order_index') or 1),
            notes_url=data.get('notes_url', '')
        )
        db.session.add(lec)
        db.session.commit()
        return jsonify({'success': True, 'lecture': lec.to_dict()})

    course_id = request.args.get('course_id')
    query = Lecture.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    lectures = query.order_by(Lecture.order_index.asc()).all()
    return jsonify([l.to_dict() for l in lectures])

# VAULT RESOURCES API
@app.route('/api/vault', methods=['GET', 'POST'])
def handle_vault():
    if request.method == 'POST':
        data = request.get_json() or {}
        rid = data.get('id') or f"res_{int(datetime.utcnow().timestamp())}"
        res = VaultResource(
            id=rid,
            title=data.get('title'),
            category=data.get('category', 'exams'),
            subcategory=data.get('subcategory') or data.get('subcat', 'General'),
            file_url=data.get('file_url') or data.get('fileUrl', '#'),
            file_size=data.get('file_size', '1.5 MB'),
            badge=data.get('badge', 'PDF Bundle'),
            description=data.get('description', '')
        )
        db.session.add(res)
        db.session.commit()
        return jsonify({'success': True, 'resource': res.to_dict()})

    resources = VaultResource.query.order_by(VaultResource.created_at.desc()).all()
    return jsonify([r.to_dict() for r in resources])


# ============================================================================
# CMS MANAGEMENT ROUTES (Courses, Lectures, Vault PDFs, Site Content, Inquiries)
# ============================================================================

@app.route('/api/courses/<cid>', methods=['DELETE', 'PUT'])
def course_detail(cid):
    course = Course.query.get(cid)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if request.method == 'DELETE':
        Lecture.query.filter_by(course_id=cid).delete()
        db.session.delete(course)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Course {cid} and its lectures deleted'})
    
    data = request.get_json() or {}
    if 'title' in data: course.title = data['title']
    if 'category' in data: course.category = data['category']
    if 'description' in data: course.description = data['description']
    if 'icon' in data: course.icon = data['icon']
    if 'badge' in data: course.badge = data['badge']
    if 'instructor' in data: course.instructor = data['instructor']
    if 'subcategory' in data: course.subcategory = data['subcategory']
    if 'subcat' in data: course.subcategory = data['subcat']
    if 'syllabus' in data:
        syl = data['syllabus']
        course.syllabus_json = json.dumps(syl) if isinstance(syl, list) else str(syl)
    if 'duration_weeks' in data: course.duration_weeks = int(data['duration_weeks'] or 6)
    if 'display_order' in data: course.display_order = int(data['display_order'] or 0)
    db.session.commit()
    return jsonify({'success': True, 'course': course.to_dict()})

@app.route('/api/lectures/<lid>', methods=['DELETE', 'PUT'])
def lecture_detail(lid):
    lec = Lecture.query.get(lid)
    if not lec:
        return jsonify({'success': False, 'message': 'Lecture not found'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(lec)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Lecture {lid} deleted'})
    
    data = request.get_json() or {}
    if 'title' in data: lec.title = data['title']
    if 'description' in data: lec.description = data['description']
    if 'video_url' in data: lec.video_url = data['video_url']
    if 'duration' in data: lec.duration = data['duration']
    if 'topic_category' in data: lec.topic_category = data['topic_category']
    elif 'group' in data: lec.topic_category = data['group']
    elif 'topic' in data: lec.topic_category = data['topic']
    if 'order_index' in data: lec.order_index = int(data['order_index'] or 1)
    if 'notes_url' in data: lec.notes_url = data['notes_url']
    db.session.commit()
    return jsonify({'success': True, 'lecture': lec.to_dict()})

@app.route('/api/vault/<rid>', methods=['DELETE', 'PUT'])
def vault_detail(rid):
    res = VaultResource.query.get(rid)
    if not res:
        return jsonify({'success': False, 'message': 'Resource not found'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(res)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Vault resource {rid} deleted'})
    
    data = request.get_json() or {}
    if 'title' in data: res.title = data['title']
    if 'category' in data: res.category = data['category']
    if 'subcategory' in data: res.subcategory = data['subcategory']
    if 'subcat' in data: res.subcategory = data['subcat']
    if 'file_url' in data: res.file_url = data['file_url']
    if 'file_size' in data: res.file_size = data['file_size']
    if 'badge' in data: res.badge = data['badge']
    if 'description' in data: res.description = data['description']
    db.session.commit()
    return jsonify({'success': True, 'resource': res.to_dict()})

@app.route('/api/upload/pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request'}), 400
    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    filename = secure_filename(f.filename)
    if not filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'message': 'Only PDF (.pdf) files are supported'}), 400
    
    upload_dir = VAULT_UPLOADS_DIR
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except Exception:
        pass
    
    safe_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
    filepath = os.path.join(upload_dir, safe_name)
    f.save(filepath)
    
    size_bytes = os.path.getsize(filepath)
    size_str = f"{size_bytes / (1024*1024):.1f} MB" if size_bytes >= 1024*1024 else f"{size_bytes / 1024:.0f} KB"
    clean_title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
    
    return jsonify({
        'success': True,
        'filename': safe_name,
        'file_url': f"/assets/vault_pdfs/{safe_name}",
        'file_size': size_str,
        'title': clean_title
    })

@app.route('/assets/vault_pdfs/<path:filename>')
def serve_vault_pdf(filename):
    if os.path.exists(os.path.join(VAULT_UPLOADS_DIR, filename)):
        return send_from_directory(VAULT_UPLOADS_DIR, filename)
    fallback_dir = os.path.join(BASE_DIR, 'assets', 'vault_pdfs')
    if os.path.exists(os.path.join(fallback_dir, filename)):
        return send_from_directory(fallback_dir, filename)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/people/update', methods=['POST'])
def update_founder_profile():
    data = request.get_json() or {}
    isaac = Member.query.filter(Member.name.like('%Isaac%')).first()
    if not isaac:
        isaac = Member(
            name="Isaac Olusola",
            role=data.get('role', 'Founder & Lead Applied Mathematician'),
            bio=data.get('bio', ''),
            avatar=data.get('avatar', 'IMG_1399.JPG'),
            email=data.get('email', 'ziglaginstitute@gmail.com'),
            linkedin=data.get('linkedin', ''),
            github=data.get('github', ''),
            youtube=data.get('youtube', ''),
            display_order=1
        )
        db.session.add(isaac)
    else:
        if 'name' in data: isaac.name = data['name']
        if 'role' in data: isaac.role = data['role']
        if 'bio' in data: isaac.bio = data['bio']
        if 'avatar' in data: isaac.avatar = data['avatar']
        if 'email' in data: isaac.email = data['email']
        if 'linkedin' in data: isaac.linkedin = data['linkedin']
        if 'github' in data: isaac.github = data['github']
        if 'youtube' in data: isaac.youtube = data['youtube']
    
    db.session.commit()
    return jsonify({
        'success': True,
        'member': {
            'name': isaac.name,
            'role': isaac.role,
            'bio': isaac.bio,
            'avatar': isaac.avatar,
            'email': isaac.email,
            'linkedin': isaac.linkedin,
            'github': isaac.github,
            'youtube': isaac.youtube
        }
    })

@app.route('/api/contact/submissions', methods=['GET'])
def get_contact_submissions():
    submissions = ContactSubmission.query.order_by(ContactSubmission.submitted_at.desc()).all()
    out = []
    for s in submissions:
        out.append({
            'id': s.id,
            'name': s.name,
            'email': s.email,
            'phone': s.phone or '',
            'sphere': s.sphere,
            'question_type': s.question_type,
            'message': s.message,
            'preferred_contact': s.preferred_contact or 'email',
            'submitted_at': s.submitted_at.strftime('%Y-%m-%d %H:%M') if s.submitted_at else ''
        })
    return jsonify(out)

@app.route('/api/contact/submissions/<int:sub_id>', methods=['DELETE'])
def delete_contact_submission(sub_id):
    sub = ContactSubmission.query.get(sub_id)
    if not sub:
        return jsonify({'success': False, 'message': 'Submission not found'}), 404
    db.session.delete(sub)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Submission {sub_id} deleted'})

@app.route('/api/site-content', methods=['GET', 'POST'])
def handle_site_content():
    if request.method == 'POST':
        data = request.get_json() or {}
        for key, val in data.items():
            str_val = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
            setting = SiteSetting.query.get(key)
            if not setting:
                setting = SiteSetting(key=key, value=str_val)
                db.session.add(setting)
            else:
                setting.value = str_val
        db.session.commit()
        return jsonify({'success': True, 'message': 'Site content saved successfully'})

    settings = SiteSetting.query.all()
    settings_dict = {}
    for s in settings:
        try:
            settings_dict[s.key] = json.loads(s.value)
        except Exception:
            settings_dict[s.key] = s.value

    # Default fallback values
    defaults = {
        'impact_stats': {
            'pass_rate': '98.4%',
            'video_count': '1,200+',
            'question_count': '15,000+',
            'coaching_stat': '1-on-1'
        },
        'vision': {
            'title': "To be Africa's Standard-Bearer in Mathematical Mastery & Analytical Innovation",
            'statement': "We envision a continent where every young mind is equipped with the fearless quantitative competence to engineer high-impact solutions in software, artificial intelligence, aerospace, energy, macroeconomic policy, and medicine."
        },
        'mission': {
            'title': "Demystifying Quantitative STEM Through First-Principles Pedagogy",
            'statement': "Our mission is to obliterate the dread and anxiety that historically surrounds mathematics and physics. We do this by breaking complex theorems into their fundamental building blocks, providing continuous practice under realistic digital exam conditions, and providing personalized guidance."
        }
    }
    for k, v in defaults.items():
        if k not in settings_dict:
            settings_dict[k] = v

    return jsonify(settings_dict)

# WORD & PDF QUESTION PARSER ENDPOINT
@app.route('/api/admin/parse-questions', methods=['POST'])
def parse_questions_endpoint():
    try:
        from question_parser import extract_text_from_file, parse_questions_from_text
    except ImportError as ie:
        return jsonify({'success': False, 'message': f'Parser dependency error: {str(ie)}'}), 500

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'Empty filename.'}), 400

    subject = request.form.get('subject', 'mathematics')
    topic = request.form.get('topic', 'General')
    difficulty = request.form.get('difficulty', 'Intermediate')
    year = request.form.get('year', 2026)

    try:
        file_bytes = file.read()
        raw_text = extract_text_from_file(file_bytes, file.filename)
        questions = parse_questions_from_text(
            raw_text,
            default_subject=subject,
            default_topic=topic,
            default_difficulty=difficulty,
            default_year=year
        )
        return jsonify({
            'success': True,
            'filename': file.filename,
            'count': len(questions),
            'questions': questions,
            'preview_text': raw_text[:500]
        })
    except Exception as e:
        logging.error(f"Error parsing question document {file.filename}: {e}")
        return jsonify({'success': False, 'message': f'Document parsing failed: {str(e)}'}), 500

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
                'avatar': m.avatar or 'IMG_1399.JPG',
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

        # Dispatch email to Isaac Olusola (ziglaginstitute@gmail.com) and auto-acknowledgment to sender
        email_sent = send_contact_inquiry_emails(submission)

        return jsonify({
            'success': True,
            'message': 'Your inquiry has been delivered directly to Mr. Isaac Olusola (ziglaginstitute@gmail.com). We will reach out shortly!',
            'email_sent': email_sent
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Server database error: {str(e)}'}), 500



def send_system_email(to_email, subject, body_text, reply_to=None):
    """
    Robust universal email sender:
    1. Supports Resend API (HTTPS port 443) if RESEND_API_KEY is present
       (bypasses cloud host free-tier SMTP port blocks completely).
    2. Fallback to Gmail / Standard SMTP with support for both:
       - SMTP_USERNAME / SMTP_PASSWORD
       - MAIL_USERNAME / MAIL_PASSWORD
       - Port 587 (STARTTLS) and Port 465 (SSL)
    """
    if not to_email:
        return False

    resend_key = (os.getenv('RESEND_API_KEY') or '').strip()
    if resend_key:
        try:
            import json
            import urllib.request
            sender = (
                os.getenv('MAIL_DEFAULT_SENDER')
                or os.getenv('SMTP_USERNAME')
                or os.getenv('MAIL_USERNAME')
                or 'onboarding@resend.dev'
            ).strip()
            if '@gmail.com' in sender and not os.getenv('RESEND_CUSTOM_DOMAIN'):
                from_header = "Ziglag Institute <onboarding@resend.dev>"
            else:
                from_header = f"Ziglag Institute <{sender}>"

            payload = {
                "from": from_header,
                "to": [to_email],
                "subject": subject,
                "text": body_text
            }
            if reply_to:
                payload["reply_to"] = reply_to

            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "ZiglagMathPortal/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 201):
                    print(f"[Email Resend API] Sent email to {to_email}")
                    return True
        except Exception as re_err:
            print(f"[Email Resend Warning] Failed via Resend API: {re_err}")

    # Standard SMTP
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    try:
        smtp_port = int(os.getenv('SMTP_PORT', 587))
    except (ValueError, TypeError):
        smtp_port = 587

    smtp_user = (
        os.getenv('SMTP_USERNAME')
        or os.getenv('MAIL_USERNAME')
        or os.getenv('MAIL_DEFAULT_SENDER')
        or ''
    ).strip()
    smtp_pass = (
        os.getenv('SMTP_PASSWORD')
        or os.getenv('MAIL_PASSWORD')
        or ''
    ).replace(' ', '').strip()

    if not smtp_user or not smtp_pass:
        print(f"[Email Notice] Credentials not configured for sending to {to_email} (Checked SMTP_USERNAME/SMTP_PASSWORD and MAIL_USERNAME/MAIL_PASSWORD)")
        return False

    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email
        if reply_to:
            msg['Reply-To'] = reply_to
        msg.set_content(body_text)

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=12) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        print(f"[Email SMTP] Sent email to {to_email}")
        return True
    except Exception as err:
        print(f"[Email SMTP Warning] Transmission notice to {to_email}: {err}")
        return False

def send_contact_inquiry_emails(submission):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = (os.getenv('SMTP_USERNAME') or '').strip()
    smtp_pass = (os.getenv('SMTP_PASSWORD') or '').replace(' ', '').strip()
    lead_email = "ziglaginstitute@gmail.com"

    lead_subject = f"📬 Website Contact Inquiry: {submission.name} [{submission.question_type.title()}]"
    lead_body = f"""Dear Mr. Isaac Olusola,

A new contact inquiry has been submitted through the Ziglag Institute website:

--- SENDER DETAILS ---
• Name: {submission.name}
• Email: {submission.email}
• Phone: {submission.phone or 'Not provided'}
• Preferred Contact Method: {submission.preferred_contact or 'Email'}
• Academic Sphere: {submission.sphere}
• Inquiry Type: {submission.question_type}
• Submitted At: {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if submission.submitted_at else 'Just now'}

--- MESSAGE / QUERY ---
{submission.message}

---
You can reply directly to {submission.name} at {submission.email}.
Ziglag Institute Administration System
"""

    student_subject = "✅ Inquiry Received — Ziglag Institute"
    student_body = f"""Dear {submission.name},

Thank you for reaching out to Ziglag Institute.

Your message has been delivered directly to Mr. Isaac Olusola (Founder & Lead Instructor) at ziglaginstitute@gmail.com. We are reviewing your submission and will get back to you shortly.

--- YOUR INQUIRY SUMMARY ---
• Focus Track: {submission.sphere}
• Type: {submission.question_type}
• Message:
{submission.message}

--- MATH & PHYSICS PROBLEMS ---
If your message is a specific Mathematics or Physics question requiring step-by-step mathematical proofs, LaTeX equations, or diagram uploads, check out our interactive Community Q&A Hub:
https://cbt-jamb-website-ziglaginstitute-8370s-projects.vercel.app / Q&A Hub (qa.html)

Warm regards,
Mr. Isaac Olusola (MSc in Applied Mathematics)
Ziglag Institute — Minds in Motion, Futures in Focus
Email: ziglaginstitute@gmail.com
"""

    sent_lead = send_system_email(lead_email, lead_subject, lead_body, reply_to=submission.email)
    sent_student = send_system_email(submission.email, student_subject, student_body, reply_to=lead_email)
    return sent_lead or sent_student


def send_tutoring_booking_emails(booking):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = (os.getenv('SMTP_USERNAME') or '').strip()
    smtp_pass = (os.getenv('SMTP_PASSWORD') or '').replace(' ', '').strip()
    coach_email = "ziglaginstitute@gmail.com"

    # Coach notification email
    coach_subject = f"🎓 New 1-on-1 Tutoring Booking: {booking.student_name} ({booking.subject})"
    coach_body = f"""Dear Mr. Isaac Olusola,

A new 1-on-1 private tutoring session has been booked on the Ziglag Institute Math Portal!

--- STUDENT & SESSION DETAILS ---
• Student Name: {booking.student_name}
• Student Email: {booking.student_email}
• Student Phone / WhatsApp: {booking.student_phone or 'Not provided'}
• Examination Track: {booking.subject} ({booking.exam_category} Exam)
• Scheduled Date: {booking.booking_date}
• Scheduled Time: {booking.booking_time} (West Africa Time, WAT / GMT+1)
• Duration: {booking.duration_hours} hour(s)
• Rate: ${booking.hourly_rate:.2f}/hr
• Total Amount: {booking.total_price}

--- LEARNING PRIORITIES ---
• Priority Focus Topic:
{booking.topic}

• Specific Difficulties & Questions:
{booking.difficulties or 'None specified'}

• Booking Reference ID: {booking.id}
• Booked At: {booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking.created_at else 'Just now'}

---
You can reply directly to the student at {booking.student_email} to share virtual whiteboard access or session notes.
Ziglag Institute Administration System
"""

    # Student confirmation email
    student_subject = f"✅ Booking Confirmed: 1-on-1 Tutoring with Mr. Isaac Olusola ({booking.subject})"
    payment_note = ""
    if booking.exam_category == "Local":
        payment_note = f"""• Payment Information:
  This local curriculum session is billed at ${booking.hourly_rate:.2f}/hr (Total: {booking.total_price}).
  Payment is payable in Naira (₦) via direct bank transfer. If you have not yet completed payment, details will be communicated via email prior to the session.
"""

    student_body = f"""Dear {booking.student_name},

Congratulations! Your private 1-on-1 tutoring session with Mr. Isaac Olusola (MSc in Applied Mathematics) has been confirmed on Ziglag Institute.

--- YOUR APPOINTMENT DOCKET ---
• Instructor: Mr. Isaac Olusola (Founder & Lead Instructor)
• Subject Track: {booking.subject}
• Focus Topic: {booking.topic}
• Difficulties to Cover: {booking.difficulties or 'Comprehensive syllabus revision'}
• Date: {booking.booking_date}
• Time: {booking.booking_time} (West Africa Time, WAT / GMT+1)
• Duration: {booking.duration_hours} hour(s)
• Total Fee: {booking.total_price}
• Booking Reference: {booking.id}

{payment_note}
--- HOW TO PREPARE ---
1. Prepare any past questions, textbook exercises, or notes on your selected topic ({booking.topic}).
2. Ensure you have a notebook, writing pens, and calculator accessible.
3. A live interactive whiteboard link (Zoom or Google Meet) will be provided for your session.

--- CONTACTING YOUR INSTRUCTOR ---
If you need to make inquiries, send question snapshots beforehand, or communicate changes, you can contact Mr. Isaac Olusola directly via email only:
✉️ Email: ziglaginstitute@gmail.com

Thank you for choosing Ziglag Institute.
Minds in Motion, Futures in Focus.
"""

    sent_coach = send_system_email(coach_email, coach_subject, coach_body, reply_to=booking.student_email)
    sent_student = send_system_email(booking.student_email, student_subject, student_body, reply_to=coach_email)
    return sent_coach or sent_student


@app.route('/api/tutoring/book', methods=['POST'])
def book_tutoring_session():
    data = request.get_json() or {}
    student_name = data.get('student_name') or data.get('name')
    student_email = data.get('student_email') or data.get('email')
    student_phone = data.get('student_phone') or data.get('phone') or ''
    subject = data.get('subject') or data.get('level') or 'Secondary Mathematics'
    topic = data.get('topic') or data.get('priority_topic') or ''
    difficulties = data.get('difficulties') or data.get('notes') or ''
    booking_date = data.get('booking_date') or data.get('date') or ''
    booking_time = data.get('booking_time') or data.get('slot') or '09:00 AM'
    try:
        duration_hours = float(data.get('duration_hours') or data.get('hours') or 1.0)
    except Exception:
        duration_hours = 1.0

    if not student_name or not student_email or not topic or not booking_date:
        return jsonify({
            'success': False,
            'message': 'Student Name, Email, Priority Topic, and Booking Date are required.'
        }), 400

    # Rule 3: Enforce No Sunday Bookings
    is_sunday = False
    for fmt in ('%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'):
        try:
            dt = datetime.strptime(booking_date.strip(), fmt)
            if dt.weekday() == 6:  # Sunday is index 6
                is_sunday = True
            break
        except ValueError:
            pass

    if 'sunday' in booking_date.lower() or is_sunday:
        return jsonify({
            'success': False,
            'message': 'Sundays are unavailable for tutoring sessions. Mr. Isaac Olusola is available Monday through Saturday. Please select a Monday–Saturday date.'
        }), 400

    # Rules 1 & 2: Pricing determination
    # GCSE and A-Level = $25/hr
    # JAMB, WASSCE, Secondary Mathematics = $15/hr (payable in Naira)
    international_subjects = [
        'GCSE Mathematics', 'GCSE Physics', 'GCSE Chemistry',
        'A-Level Mathematics', 'A-Level Physics'
    ]
    is_intl = any(is_s.lower() in subject.lower() for is_s in ['gcse', 'a-level', 'alevel', 'international'])

    if is_intl:
        exam_category = "International"
        hourly_rate = 25.0
        total_price = f"${(duration_hours * 25.0):.2f}"
        currency = "USD"
    else:
        exam_category = "Local"
        hourly_rate = 15.0
        naira_amt = int(duration_hours * 15.0 * 1600)  # Standard ~$15 = ₦24,000/hr
        total_price = f"${(duration_hours * 15.0):.2f} (~₦{naira_amt:,})"
        currency = "NGN / USD"

    bid = f"book_{int(datetime.utcnow().timestamp())}_{int(duration_hours*10)}"
    booking = TutoringBooking(
        id=bid,
        student_name=student_name.strip(),
        student_email=student_email.strip(),
        student_phone=student_phone.strip(),
        instructor_name="Mr. Isaac Olusola",
        instructor_email="ziglaginstitute@gmail.com",
        subject=subject.strip(),
        exam_category=exam_category,
        topic=topic.strip(),
        difficulties=difficulties.strip(),
        booking_date=booking_date.strip(),
        booking_time=booking_time.strip(),
        duration_hours=duration_hours,
        hourly_rate=hourly_rate,
        total_price=total_price,
        currency=currency,
        status="Confirmed"
    )

    try:
        db.session.add(booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error saving booking: {str(e)}'}), 500

    # Dispatch notification emails
    email_dispatched = send_tutoring_booking_emails(booking)

    return jsonify({
        'success': True,
        'message': 'Your tutoring session has been successfully booked and confirmed!',
        'booking': booking.to_dict(),
        'email_sent': email_dispatched
    })


@app.route('/api/tutoring/bookings', methods=['GET'])
def get_tutoring_bookings():
    try:
        bookings = TutoringBooking.query.order_by(TutoringBooking.created_at.desc()).all()
        return jsonify([b.to_dict() for b in bookings])
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/api/tutoring/bookings/<bid>', methods=['DELETE'])
def delete_tutoring_booking(bid):
    booking = TutoringBooking.query.get(bid)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'}), 404
    try:
        db.session.delete(booking)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Booking {bid} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


# ============================================================================
# COMMUNITY MATH & PHYSICS Q&A HUB ENDPOINTS
# ============================================================================

def send_community_question_email(question):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = (os.getenv('SMTP_USERNAME') or '').strip()
    smtp_pass = (os.getenv('SMTP_PASSWORD') or '').replace(' ', '').strip()
    coach_email = "ziglaginstitute@gmail.com"

    subject = f"❓ New Community Question: [{question.difficulty} | {question.subject}] {question.title}"
    body = f"""Dear Mr. Isaac Olusola,

A new question has been posted to the Community Math & Physics Hub on Ziglag Institute!

--- QUESTION OVERVIEW ---
• Title: {question.title}
• Subject: {question.subject}
• Difficulty Level: {question.difficulty}
• Posted By: {question.author_name} ({question.author_email or 'No email provided'})
• Question ID: {question.id}
• Attachment: {question.attachment_name or 'None'} {f'({question.attachment_url})' if question.attachment_url else ''}
• Posted At: {question.created_at.strftime('%Y-%m-%d %H:%M:%S') if question.created_at else 'Just now'}

--- QUESTION BODY / LATEX ---
{question.content_latex}

---
You can view, review, and post your verified educator solution on the portal at:
https://cbt-jamb-website-ziglaginstitute-8370s-projects.vercel.app/qa.html or via Admin CMS.

Ziglag Institute Administration System
"""
    return send_system_email(coach_email, subject, body, reply_to=question.author_email)


def send_community_answer_email(question, answer):
    if not question.author_email:
        return False
    # Don't email author if they answered their own question
    if answer.author_email and answer.author_email.lower() == question.author_email.lower():
        return False

    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = (os.getenv('SMTP_USERNAME') or '').strip()
    smtp_pass = (os.getenv('SMTP_PASSWORD') or '').replace(' ', '').strip()

    subject = f"💡 Solution Posted to Your Question: {question.title} — Ziglag Institute"
    role_tag = " (🌟 Lead Instructor & Verified Educator)" if answer.is_educator else ""
    body = f"""Dear {question.author_name},

A new response/solution has been submitted to your question "{question.title}" by {answer.author_name}{role_tag}!

--- SOLUTION PREVIEW ---
{answer.content_latex[:400]}{'...' if len(answer.content_latex) > 400 else ''}

---
To view the full step-by-step LaTeX derivation, mathematical formulas, and community discussion, visit:
https://cbt-jamb-website-ziglaginstitute-8370s-projects.vercel.app/qa.html?qid={question.id}

Keep learning and exploring!
Ziglag Institute — Minds in Motion, Futures in Focus
Email: ziglaginstitute@gmail.com
"""
    return send_system_email(question.author_email, subject, body, reply_to="ziglaginstitute@gmail.com")


@app.route('/api/community/upload', methods=['POST'])
def upload_community_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request.'}), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'Empty file submitted.'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'svg'}
    if ext not in allowed_exts:
        return jsonify({
            'success': False,
            'message': f'Unsupported file type .{ext}. Allowed types: PNG, JPG, JPEG, WEBP, PDF, SVG.'
        }), 400

    unique_name = f"qa_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}_{filename}"
    try:
        os.makedirs(COMMUNITY_UPLOADS_DIR, exist_ok=True)
    except Exception:
        pass
    save_path = os.path.join(COMMUNITY_UPLOADS_DIR, unique_name)
    file.save(save_path)

    file_size_bytes = os.path.getsize(save_path)
    file_size_display = f"{file_size_bytes / (1024*1024):.1f} MB" if file_size_bytes >= 1024*1024 else f"{max(1, file_size_bytes // 1024)} KB"
    file_type = 'pdf' if ext == 'pdf' else 'image'

    return jsonify({
        'success': True,
        'file_url': f'/assets/community_uploads/{unique_name}',
        'file_name': filename,
        'file_type': file_type,
        'file_size': file_size_display
    })


@app.route('/assets/community_uploads/<path:filename>')
def serve_community_upload(filename):
    if os.path.exists(os.path.join(COMMUNITY_UPLOADS_DIR, filename)):
        return send_from_directory(COMMUNITY_UPLOADS_DIR, filename)
    fallback_dir = os.path.join(BASE_DIR, 'assets', 'community_uploads')
    if os.path.exists(os.path.join(fallback_dir, filename)):
        return send_from_directory(fallback_dir, filename)
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/community/questions', methods=['GET'])
def get_community_questions():
    difficulty = request.args.get('difficulty')
    subject = request.args.get('subject')
    status = request.args.get('status')
    search = request.args.get('search', '').strip().lower()

    query = CommunityQuestion.query

    if difficulty and difficulty.lower() != 'all':
        query = query.filter(CommunityQuestion.difficulty.ilike(difficulty))
    if subject and subject.lower() != 'all':
        query = query.filter(CommunityQuestion.subject.ilike(subject))
    if status and status.lower() != 'all':
        query = query.filter(CommunityQuestion.status.ilike(status))

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                CommunityQuestion.title.ilike(search_filter),
                CommunityQuestion.content_latex.ilike(search_filter),
                CommunityQuestion.subject.ilike(search_filter),
                CommunityQuestion.author_name.ilike(search_filter)
            )
        )

    questions = query.order_by(CommunityQuestion.created_at.desc()).all()
    return jsonify([q.to_dict() for q in questions])


@app.route('/api/community/questions/<qid>', methods=['GET'])
def get_community_question_detail(qid):
    question = CommunityQuestion.query.get(qid)
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'}), 404

    # Increment view count
    try:
        question.views = (question.views or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({
        'success': True,
        'question': question.to_dict(include_answers=True)
    })


@app.route('/api/community/questions', methods=['POST'])
def create_community_question():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    subject = (data.get('subject') or 'Mathematics').strip()
    difficulty = (data.get('difficulty') or 'Intermediate').strip()
    content_latex = (data.get('content_latex') or data.get('content') or '').strip()
    author_name = (data.get('author_name') or 'Anonymous Scholar').strip()
    author_email = (data.get('author_email') or '').strip()
    attachment_url = (data.get('attachment_url') or '').strip()
    attachment_name = (data.get('attachment_name') or '').strip()
    attachment_type = (data.get('attachment_type') or ('pdf' if attachment_url.endswith('.pdf') else 'image' if attachment_url else '')).strip()

    if not title or not content_latex:
        return jsonify({'success': False, 'message': 'Title and Question Body are required.'}), 400

    valid_diffs = {'Beginner', 'Intermediate', 'Advanced'}
    if difficulty.title() in valid_diffs:
        difficulty = difficulty.title()
    else:
        difficulty = 'Intermediate'

    qid = f"cq_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}"
    question = CommunityQuestion(
        id=qid,
        title=title,
        subject=subject,
        difficulty=difficulty,
        content_latex=content_latex,
        author_name=author_name,
        author_email=author_email,
        attachment_url=attachment_url if attachment_url else None,
        attachment_name=attachment_name if attachment_name else None,
        attachment_type=attachment_type if attachment_type else None,
        views=0,
        upvotes=0,
        status='Open',
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(question)
        db.session.commit()
        # Notify lead instructor
        send_community_question_email(question)
        return jsonify({'success': True, 'question': question.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/api/community/questions/<qid>/answers', methods=['POST'])
def add_community_answer(qid):
    question = CommunityQuestion.query.get(qid)
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'}), 404

    data = request.get_json() or {}
    content_latex = (data.get('content_latex') or data.get('content') or '').strip()
    author_name = (data.get('author_name') or 'Anonymous Contributor').strip()
    author_email = (data.get('author_email') or '').strip()
    attachment_url = (data.get('attachment_url') or '').strip()
    attachment_name = (data.get('attachment_name') or '').strip()
    attachment_type = (data.get('attachment_type') or ('pdf' if attachment_url.endswith('.pdf') else 'image' if attachment_url else '')).strip()

    if not content_latex:
        return jsonify({'success': False, 'message': 'Solution body is required.'}), 400

    # Determine educator / lead status
    is_educator = False
    is_verified = False
    if (author_email and author_email.lower() == 'ziglaginstitute@gmail.com') or ('isaac olusola' in author_name.lower()):
        is_educator = True
        is_verified = True
        author_name = "Mr. Isaac Olusola"
        author_email = "ziglaginstitute@gmail.com"
        question.status = 'Solved'

    aid = f"ans_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:6]}"
    answer = CommunityAnswer(
        id=aid,
        question_id=qid,
        author_name=author_name,
        author_email=author_email,
        is_educator=is_educator,
        content_latex=content_latex,
        attachment_url=attachment_url if attachment_url else None,
        attachment_name=attachment_name if attachment_name else None,
        attachment_type=attachment_type if attachment_type else None,
        upvotes=0,
        is_verified=is_verified,
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(answer)
        db.session.commit()
        # Notify asker
        send_community_answer_email(question, answer)
        return jsonify({'success': True, 'answer': answer.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/api/community/questions/<qid>/upvote', methods=['POST'])
def upvote_community_question(qid):
    question = CommunityQuestion.query.get(qid)
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    try:
        question.upvotes = (question.upvotes or 0) + 1
        db.session.commit()
        return jsonify({'success': True, 'upvotes': question.upvotes})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/api/community/answers/<aid>/upvote', methods=['POST'])
def upvote_community_answer(aid):
    answer = CommunityAnswer.query.get(aid)
    if not answer:
        return jsonify({'success': False, 'message': 'Answer not found'}), 404
    try:
        answer.upvotes = (answer.upvotes or 0) + 1
        db.session.commit()
        return jsonify({'success': True, 'upvotes': answer.upvotes})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/api/community/questions/<qid>', methods=['DELETE'])
def delete_community_question(qid):
    question = CommunityQuestion.query.get(qid)
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'}), 404
    try:
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Question {qid} and all associated answers deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500


@app.route('/api/community/answers/<aid>', methods=['DELETE'])
def delete_community_answer(aid):
    answer = CommunityAnswer.query.get(aid)
    if not answer:
        return jsonify({'success': False, 'message': 'Answer not found'}), 404
    try:
        db.session.delete(answer)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Answer {aid} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

# ============================================================================
# 4. STARTUP DATABASE INITIALIZATION & DEFAULT SEEDING
# ============================================================================
if not IS_VERCEL:
    _app_ctx = app.app_context()
    _app_ctx.push()
    try:
        db.create_all()

        # Seed Founder
        if not Member.query.first():
            default_members = [
                Member(
                    name="Isaac Olusola",
                    role="Founder & CEO",
                    bio="Isaac is the visionary behind Ziglag Institute, dedicated to providing premium and accessible STEM education.",
                    avatar="🚀",
                    email="ziglaginstitute@gmail.com",
                    linkedin="https://www.linkedin.com/in/isaac-olusola-2a2b2218b",
                    github="https://github.com/ziglaginstitute-del",
                    youtube="https://youtube.com/@ziglaginstitute?si=pb96DBtz9CQRfpbn",
                    display_order=1
                )
            ]
            db.session.bulk_save_objects(default_members)
            db.session.commit()

        # Seed Demo Candidate (Ifeoma Adaeze Jude)
        if not Candidate.query.first():
            demo_candidate = Candidate(
                id="cand_demo_01",
                full_name="Ifeoma Adaeze Jude",
                username="JAMB/2026/170",
                category="Biological & Medical",
                exam_type="JAMB UTME",
                registered_subjects='["english", "mathematics", "physics", "chemistry"]',
                center="PrepCBT Center 01 (Main Auditorium)",
                seat_number="Seat 54",
                status="Active"
            )
            demo_candidate2 = Candidate(
                id="cand_demo_02",
                full_name="Babatunde Johnson",
                username="2026/JAMB/94821",
                category="Science",
                exam_type="JAMB UTME",
                registered_subjects='["english", "mathematics", "physics", "chemistry"]',
                center="Ziglag CBT Center Lagos",
                seat_number="Seat 12",
                status="Active"
            )
            db.session.add(demo_candidate)
            db.session.add(demo_candidate2)
            db.session.commit()

    
        # Seed Default Nigerian Subjects if empty
        if not Subject.query.first():
            default_subs = [
                Subject(id="mathematics", name="Mathematics", code="MTH", icon="📐", category="Core STEM", default_duration=40),
                Subject(id="english", name="English Language", code="ENG", icon="📖", category="General", default_duration=60),
                Subject(id="physics", name="Physics", code="PHY", icon="⚡", category="Core STEM", default_duration=40),
                Subject(id="chemistry", name="Chemistry", code="CHM", icon="🧪", category="Core STEM", default_duration=40),
                Subject(id="biology", name="Biology", code="BIO", icon="🧬", category="Medical / Science", default_duration=40),
                Subject(id="further_mathematics", name="Further Mathematics", code="FMTH", icon="🔢", category="Advanced STEM", default_duration=40),
                Subject(id="economics", name="Economics", code="ECN", icon="📊", category="Social Science", default_duration=40),
                Subject(id="government", name="Government", code="GOV", icon="🏛️", category="Arts / Humanities", default_duration=40),
                Subject(id="literature", name="Literature in English", code="LIT", icon="🎭", category="Arts / Humanities", default_duration=40),
                Subject(id="commerce", name="Commerce", code="COM", icon="💼", category="Commercial", default_duration=40),
                Subject(id="agricultural_science", name="Agricultural Science", code="AGR", icon="🌾", category="Science", default_duration=40),
                Subject(id="civic_education", name="Civic Education", code="CIV", icon="🛡️", category="General", default_duration=40),
                Subject(id="geography", name="Geography", code="GEO", icon="🌍", category="Social Science", default_duration=40)
            ]
            db.session.bulk_save_objects(default_subs)
            db.session.commit()

        # Seed Default Mock Exam
        if not ScheduledExam.query.first():
            demo_mock = ScheduledExam(
                id="mock_2026_national",
                title="National All-Nigeria JAMB UTME Mega Mock 2026",
                access_code="ZIGLAG-MOCK-2026",
                exam_type="jamb",
                duration_minutes=120,
                subject_ids='["english", "mathematics", "physics", "chemistry"]',
                is_active=True
            )
            db.session.add(demo_mock)
            db.session.commit()

        # Seed Default Courses
        if not Course.query.first():
            default_courses = [
                Course(
                    id="jamb-prep",
                    title="JAMB / Post-JAMB Comprehensive Prep",
                    slug="jamb-prep",
                    category="JAMB / Post-JAMB",
                    description="High-yield masterclass on Calculus, Coordinate Geometry, Projectile Motion, Stoichiometry, and Mechanics.",
                    icon="🎯",
                    badge="Bestseller",
                    instructor="Mr. Isaac Olusola",
                    duration_weeks=6,
                    display_order=1
                ),
                Course(
                    id="calculus-essentials",
                    title="Calculus Essentials & Advanced Methods",
                    slug="calculus-essentials",
                    category="Senior Secondary WASSCE",
                    description="From limits and first-principles differentiation to definite integrals and kinematic applications.",
                    icon="∫",
                    badge="Advanced",
                    instructor="Mr. Isaac Olusola",
                    duration_weeks=6,
                    display_order=2
                ),
                Course(
                    id="physics-mechanics",
                    title="Classical Mechanics & Wave Optics",
                    slug="physics-mechanics",
                    category="Senior Secondary WASSCE",
                    description="Vectors, Newton laws of motion, rotational dynamics, SHM, and geometric optics with exam past papers.",
                    icon="⚡",
                    badge="Core STEM",
                    instructor="Mr. Isaac Olusola",
                    duration_weeks=6,
                    display_order=3
                )
            ]
            db.session.bulk_save_objects(default_courses)
            db.session.commit()

        # Seed Default Vault Resources
        if not VaultResource.query.first():
            default_vault = [
                VaultResource(
                    id="res-jamb-math-formulas",
                    title="Complete JAMB Mathematics Formula Sheet & Shortcuts",
                    category="JAMB UTME",
                    file_url="#",
                    file_size="2.4 MB",
                    badge="PDF",
                    description="Comprehensive compilation of all formulas in Algebra, Calculus, Matrices, and Trigonometry."
                ),
                VaultResource(
                    id="res-waec-physics-mechanics",
                    title="WASSCE Physics Mechanics & Motion Mastery Guide",
                    category="WASSCE / NECO",
                    file_url="#",
                    file_size="3.1 MB",
                    badge="PDF",
                    description="Detailed breakdown of projectile motion, friction, momentum conservation, and solved WAEC past questions."
                )
            ]
            db.session.bulk_save_objects(default_vault)
            db.session.commit()

        # Seed Representative Community Q&A across Beginner, Intermediate, and Advanced tiers
        if not CommunityQuestion.query.first():
            try:
                # Beginner 1 (Math)
                q1 = CommunityQuestion(
                    id="cq_seed_01",
                    title="How do I convert a fractional decimal like 13.625 into binary base 2?",
                    subject="Mathematics",
                    difficulty="Beginner",
                    content_latex="Can someone break down the exact procedure for converting decimal fractions into binary base 2? For example:\n$$13.625_{10} = (?)_{2}$$\nI understand how to convert the integer part $13_{10}$, but the fractional part $.625$ always confuses me.",
                    author_name="Chukwudi Eze",
                    author_email="chukwudi.eze@example.com",
                    views=42,
                    upvotes=7,
                    status="Solved"
                )
                a1 = CommunityAnswer(
                    id="ans_seed_01",
                    question_id="cq_seed_01",
                    author_name="Mr. Isaac Olusola",
                    author_email="ziglaginstitute@gmail.com",
                    is_educator=True,
                    is_verified=True,
                    upvotes=12,
                    content_latex="Hello Chukwudi! Here is the rigorous first-principles breakdown. We decompose the number into its integer part and fractional part:\n$$13.625_{10} = 13 + 0.625$$\n\n**Step 1: Integer Part ($13$) via repeated division by $2$:**\n- $13 \\div 2 = 6 \\text{ remainder } 1$\n- $6 \\div 2 = 3 \\text{ remainder } 0$\n- $3 \\div 2 = 1 \\text{ remainder } 1$\n- $1 \\div 2 = 0 \\text{ remainder } 1$\nReading remainders from bottom to top: $13_{10} = 1101_2$.\n\n**Step 2: Fractional Part ($0.625$) via repeated multiplication by $2$:**\n- $0.625 \\times 2 = 1.25 \\implies \\text{record integer } \\mathbf{1}$, remainder $= 0.25$\n- $0.25 \\times 2 = 0.50 \\implies \\text{record integer } \\mathbf{0}$, remainder $= 0.50$\n- $0.50 \\times 2 = 1.00 \\implies \\text{record integer } \\mathbf{1}$, remainder $= 0.00$ (Terminates!)\nReading recorded integers from top to bottom: $0.625_{10} = 0.101_2$.\n\n**Step 3: Combine both parts:**\n$$13.625_{10} = 1101.101_2$$"
                )

                # Beginner 2 (Physics)
                q2 = CommunityQuestion(
                    id="cq_seed_02",
                    title="A car accelerates uniformly from rest to 25 m/s in 10 seconds. Calculate the total distance covered.",
                    subject="Physics",
                    difficulty="Beginner",
                    content_latex="A vehicle starts from rest ($u = 0$) and accelerates uniformly to a final velocity of $v = 25\\text{ m/s}$ in $t = 10\\text{ s}$. How do we compute the total displacement $s$ using kinematic equations?",
                    author_name="Blessing Okon",
                    author_email="blessing.okon@example.com",
                    views=35,
                    upvotes=5,
                    status="Solved"
                )
                a2 = CommunityAnswer(
                    id="ans_seed_02",
                    question_id="cq_seed_02",
                    author_name="Mr. Isaac Olusola",
                    author_email="ziglaginstitute@gmail.com",
                    is_educator=True,
                    is_verified=True,
                    upvotes=9,
                    content_latex="Great foundational kinematics problem!\nWe are given:\n- Initial velocity: $u = 0\\text{ m/s}$\n- Final velocity: $v = 25\\text{ m/s}$\n- Time interval: $t = 10\\text{ s}$\n\n**Method 1: Average velocity formulation**\nSince acceleration is uniform:\n$$s = \\left(\\frac{u + v}{2}\\right) \\times t = \\left(\\frac{0 + 25}{2}\\right) \\times 10 = 12.5 \\times 10 = 125\\text{ metres}$$\n\n**Method 2: Finding acceleration $a$ first**\n$$a = \\frac{v - u}{t} = \\frac{25 - 0}{10} = 2.5\\text{ m/s}^2$$\nUsing $s = ut + \\frac{1}{2}at^2$:\n$$s = (0)(10) + \\frac{1}{2}(2.5)(10)^2 = 0 + 1.25 \\times 100 = 125\\text{ metres}$$"
                )

                # Intermediate 1 (Math)
                q3 = CommunityQuestion(
                    id="cq_seed_03",
                    title="Proof of Alternate Segment Theorem in Circle Geometry (WASSCE / IGCSE)",
                    subject="Mathematics",
                    difficulty="Intermediate",
                    content_latex="In circle geometry, prove that the angle between a tangent to a circle and a chord drawn through the point of contact is equal to the angle subtended by the chord in the alternate segment:\n$$\\angle TAB = \\angle ACB$$\nHow do we prove this formally for WAEC / Cambridge exam marks?",
                    author_name="Faruk Danjuma",
                    author_email="faruk.danjuma@example.com",
                    views=68,
                    upvotes=14,
                    status="Solved"
                )
                a3 = CommunityAnswer(
                    id="ans_seed_03",
                    question_id="cq_seed_03",
                    author_name="Mr. Isaac Olusola",
                    author_email="ziglaginstitute@gmail.com",
                    is_educator=True,
                    is_verified=True,
                    upvotes=21,
                    content_latex="A classic theorem frequently examined in WASSCE and IGCSE Additional Mathematics!\n\n**Construction:**\nDraw diameter $AD$ through point of contact $A$ to point $D$ on the circumference. Join $D$ to $B$.\n\n**Formal Proof:**\n1. Since $AD$ is a diameter and $AT$ is a tangent at $A$:\n$$\\angle DAT = 90^\\circ \\quad (\\text{radius } \\perp \\text{ tangent})$$\n2. Therefore:\n$$\\angle TAB = 90^\\circ - \\angle DAB \\quad \\text{--- (Equation 1)}$$\n3. Angle in a semicircle is a right angle ($\\triangle ABD$ is right-angled at $B$):\n$$\\angle ABD = 90^\\circ$$\n$$\\implies \\angle ADB + \\angle DAB = 90^\\circ \\implies \\angle ADB = 90^\\circ - \\angle DAB \\quad \\text{--- (Equation 2)}$$\n4. Comparing (1) and (2):\n$$\\angle TAB = \\angle ADB$$\n5. But angles subtended by the same chord $AB$ in the same segment are equal:\n$$\\angle ADB = \\angle ACB$$\n6. Therefore, by transitive equality:\n$$\\angle TAB = \\angle ACB \\quad \\text{Q.E.D.}$$"
                )

                # Intermediate 2 (Physics)
                q4 = CommunityQuestion(
                    id="cq_seed_04",
                    title="Derivation of Maximum Horizontal Range in Projectile Motion",
                    subject="Physics",
                    difficulty="Intermediate",
                    content_latex="For a projectile launched at speed $u$ and angle $\\theta$ to the horizontal over level ground, prove that the horizontal range is:\n$$R = \\frac{u^2 \\sin(2\\theta)}{g}$$\nand show that the maximum range occurs at $\\theta = 45^\\circ$.",
                    author_name="Amara Nwachukwu",
                    author_email="amara.n@example.com",
                    views=53,
                    upvotes=11,
                    status="Solved"
                )
                a4 = CommunityAnswer(
                    id="ans_seed_04",
                    question_id="cq_seed_04",
                    author_name="Mr. Isaac Olusola",
                    author_email="ziglaginstitute@gmail.com",
                    is_educator=True,
                    is_verified=True,
                    upvotes=16,
                    content_latex="Let's derive this from first principles:\n\n**1. Velocity components:**\n$$u_x = u \\cos\\theta, \\quad u_y = u \\sin\\theta$$\n\n**2. Total Time of Flight ($T$):**\nUsing vertical displacement $y = u_y t - \\frac{1}{2}gt^2 = 0$:\n$$t \\left(u \\sin\\theta - \\frac{1}{2}gt\\right) = 0 \\implies T = \\frac{2u \\sin\\theta}{g}$$\n\n**3. Horizontal Range ($R$):**\nSince horizontal acceleration $a_x = 0$:\n$$R = u_x \\times T = (u \\cos\\theta) \\left(\\frac{2u \\sin\\theta}{g}\\right) = \\frac{u^2 (2\\sin\\theta\\cos\\theta)}{g}$$\nUsing double-angle identity $2\\sin\\theta\\cos\\theta = \\sin(2\\theta)$:\n$$R = \\frac{u^2 \\sin(2\\theta)}{g}$$\n\n**4. Condition for Maximum Range:**\nSince the sine function attains its maximum value of $1$:\n$$\\sin(2\\theta) = 1 \\implies 2\\theta = 90^\\circ \\implies \\theta = 45^\\circ$$\n$$R_{\\max} = \\frac{u^2}{g}$$"
                )

                # Advanced 1 (Math)
                q5 = CommunityQuestion(
                    id="cq_seed_05",
                    title="Eigenvalues and Orthonormal Eigenspaces of a 3x3 Symmetric Tridiagonal Matrix",
                    subject="Mathematics",
                    difficulty="Advanced",
                    content_latex="Let $A$ be the symmetric matrix:\n$$A = \\begin{pmatrix} 2 & 1 & 0 \\\\ 1 & 2 & 1 \\\\ 0 & 1 & 2 \\end{pmatrix}$$\nFind all eigenvalues $\\lambda_1, \\lambda_2, \\lambda_3$ and determine an orthonormal basis of eigenvectors for $\\mathbb{R}^3$.",
                    author_name="Kelechi Adeleke",
                    author_email="kelechi.adeleke@example.com",
                    views=89,
                    upvotes=19,
                    status="Solved"
                )
                a5 = CommunityAnswer(
                    id="ans_seed_05",
                    question_id="cq_seed_05",
                    author_name="Mr. Isaac Olusola",
                    author_email="ziglaginstitute@gmail.com",
                    is_educator=True,
                    is_verified=True,
                    upvotes=25,
                    content_latex="A wonderful problem demonstrating the Spectral Theorem for symmetric real matrices!\n\n**1. Characteristic Polynomial $\\det(A - \\lambda I) = 0$:**\n$$\\det \\begin{pmatrix} 2 - \\lambda & 1 & 0 \\\\ 1 & 2 - \\lambda & 1 \\\\ 0 & 1 & 2 - \\lambda \\end{pmatrix} = 0$$\nExpanding along the first row:\n$$(2 - \\lambda)[(2 - \\lambda)^2 - 1] - 1[(2 - \\lambda) - 0] = 0$$\n$$(2 - \\lambda) \\left[ (2 - \\lambda)^2 - 2 \\right] = 0$$\nHence the three distinct eigenvalues are:\n$$\\lambda_1 = 2, \\quad \\lambda_2 = 2 + \\sqrt{2}, \\quad \\lambda_3 = 2 - \\sqrt{2}$$\n\n**2. Eigenvectors:**\nFor $\\lambda_1 = 2$:\n$$\\begin{pmatrix} 0 & 1 & 0 \\\\ 1 & 0 & 1 \\\\ 0 & 1 & 0 \\end{pmatrix} \\begin{pmatrix} x \\\\ y \\\\ z \\end{pmatrix} = \\mathbf{0} \\implies y = 0, \\ x + z = 0 \\implies \\vec{v}_1 = \\frac{1}{\\sqrt{2}} \\begin{pmatrix} 1 \\\\ 0 \\\\ -1 \\end{pmatrix}$$\n\nFor $\\lambda_2 = 2 + \\sqrt{2}$:\n$$\\begin{pmatrix} -\\sqrt{2} & 1 & 0 \\\\ 1 & -\\sqrt{2} & 1 \\\\ 0 & 1 & -\\sqrt{2} \\end{pmatrix} \\begin{pmatrix} x \\\\ y \\\\ z \\end{pmatrix} = \\mathbf{0} \\implies y = \\sqrt{2}x, \\ z = x \\implies \\vec{v}_2 = \\frac{1}{2} \\begin{pmatrix} 1 \\\\ \\sqrt{2} \\\\ 1 \\end{pmatrix}$$\n\nFor $\\lambda_3 = 2 - \\sqrt{2}$:\n$$\\vec{v}_3 = \\frac{1}{2} \\begin{pmatrix} 1 \\\\ -\\sqrt{2} \\\\ 1 \\end{pmatrix}$$\nNotice that $\\{\\vec{v}_1, \\vec{v}_2, \\vec{v}_3\\}$ forms an orthonormal basis: $\\vec{v}_i \\cdot \\vec{v}_j = \\delta_{ij}$."
                )

                # Advanced 2 (Physics)
                q6 = CommunityQuestion(
                    id="cq_seed_06",
                    title="Infinite Square Well: Solving the Time-Independent Schrödinger Equation",
                    subject="Physics",
                    difficulty="Advanced",
                    content_latex="Consider a particle of mass $m$ confined to a 1D box with potential:\n$$V(x) = \\begin{cases} 0 & \\text{for } 0 \\le x \\le L \\\\ \\infty & \\text{otherwise} \\end{cases}$$\nDerive the normalized stationary wavefunctions $\\psi_n(x)$ and energy levels $E_n$ from the Schrödinger equation.",
                    author_name="Toluwani Alao",
                    author_email="toluwani.alao@example.com",
                    views=74,
                    upvotes=15,
                    status="Solved"
                )
                a6 = CommunityAnswer(
                    id="ans_seed_06",
                    question_id="cq_seed_06",
                    author_name="Mr. Isaac Olusola",
                    author_email="ziglaginstitute@gmail.com",
                    is_educator=True,
                    is_verified=True,
                    upvotes=18,
                    content_latex="Let's solve the 1D Time-Independent Schrödinger Equation (TISE):\n$$-\\frac{\\hbar^2}{2m} \\frac{d^2\\psi}{dx^2} = E\\psi \\implies \\frac{d^2\\psi}{dx^2} + k^2\\psi = 0, \\quad \\text{where } k = \\frac{\\sqrt{2mE}}{\\hbar}$$\n\n**1. General Solution inside the well ($0 \\le x \\le L$):**\n$$\\psi(x) = A \\sin(kx) + B \\cos(kx)$$\n\n**2. Boundary Conditions:**\n- At $x = 0$: $\\psi(0) = B = 0$.\n- At $x = L$: $\\psi(L) = A \\sin(kL) = 0$.\nFor non-trivial solutions ($A \\neq 0$):\n$$kL = n\\pi \\implies k_n = \\frac{n\\pi}{L}, \\quad n \\in \\{1, 2, 3, \\dots\\}$$\n\n**3. Energy Eigenvalues:**\n$$E_n = \\frac{\\hbar^2 k_n^2}{2m} = \\frac{n^2 \\pi^2 \\hbar^2}{2mL^2}$$\n\n**4. Normalization condition $\\int_0^L |\\psi(x)|^2 dx = 1$:**\n$$A^2 \\int_0^L \\sin^2\\left(\\frac{n\\pi x}{L}\\right) dx = A^2 \\left(\\frac{L}{2}\\right) = 1 \\implies A = \\sqrt{\\frac{2}{L}}$$\n$$\\psi_n(x) = \\sqrt{\\frac{2}{L}} \\sin\\left(\\frac{n\\pi x}{L}\\right)$$\nThe ground state energy is $E_1 = \\frac{\\pi^2 \\hbar^2}{2mL^2}$."
                )

                db.session.add_all([q1, q2, q3, q4, q5, q6])
                db.session.add_all([a1, a2, a3, a4, a5, a6])
                db.session.commit()
                print("[Q&A Seeding] Successfully seeded 6 representative Community questions & verified educator solutions.")
            except Exception as se:
                db.session.rollback()
                print(f"[Q&A Seeding Notice] Could not seed community questions: {se}")
    except Exception as e:
        logging.warning(f"[Database Startup Notice] Startup database operation notice: {e}")
    finally:
        try:
            _app_ctx.pop()
        except Exception:
            pass


handler = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
