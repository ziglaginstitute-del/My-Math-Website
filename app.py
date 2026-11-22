import os
import json
import uuid
import logging
import urllib.request
import secrets
import hashlib
import re
from functools import wraps
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, send_from_directory, request, jsonify, redirect, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import func, text
from decimal import Decimal, ROUND_HALF_UP
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

# Apply Werkzeug ProxyFix middleware for Render reverse proxy (trusting 1 proxy hop)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Secure Session Cookie Configuration (Render-Centric)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = bool(os.getenv('RENDER') or os.getenv('FLASK_ENV') == 'production')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)

if os.getenv('RENDER') and app.config['SECRET_KEY'] == 'default-dev-secret-key-12345':
    logging.warning("[SECURITY NOTICE] Running on Render with fallback dev SECRET_KEY. Please pin a strong SECRET_KEY in Render environment variables.")

# CORS handler for cross-origin access (e.g. file:///, localhost dev, or external origins)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRF-Token'
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


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    intended_exam = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    session_version = db.Column(db.Integer, default=1, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    tokens = db.relationship('PasswordResetToken', backref='student', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': str(self.id),
            'full_name': self.full_name,
            'email': self.email,
            'education_level': self.education_level,
            'intended_exam': self.intended_exam,
            'phone': self.phone or '',
            'avatar_url': self.avatar_url or '',
            'is_active': self.is_active,
            'session_version': self.session_version,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'token_hash': self.token_hash,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuthRateLimit(db.Model):
    __tablename__ = 'auth_rate_limits'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    rate_key = db.Column(db.String(128), unique=True, nullable=False)
    endpoint = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    identifier_hash = db.Column(db.String(64), nullable=True)
    attempt_count = db.Column(db.Integer, default=1, nullable=False)
    first_attempt_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_attempt_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)


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


# ============================================================================
# PHASE 6.2 / 6.3 STUDENT LEARNING MODELS
# ============================================================================

class StudentEnrollment(db.Model):
    __tablename__ = 'student_enrollments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.String(100), db.ForeignKey('courses.id', ondelete='RESTRICT'), nullable=False)
    enrolled_at = db.Column(db.DateTime(timezone=True), server_default=db.text('CURRENT_TIMESTAMP'), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_pinned = db.Column(db.Boolean, server_default=db.text('true'), default=True, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_accessed_at = db.Column(db.DateTime(timezone=True), server_default=db.text('CURRENT_TIMESTAMP'), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_enrollments_student_course'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'course_id': self.course_id,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'is_pinned': self.is_pinned,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }


class StudentLessonProgress(db.Model):
    __tablename__ = 'student_lesson_progress'

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.String(100), db.ForeignKey('courses.id', ondelete='RESTRICT'), nullable=False)
    lecture_id = db.Column(db.String(100), db.ForeignKey('lectures.id', ondelete='RESTRICT'), nullable=False)
    is_completed = db.Column(db.Boolean, server_default=db.text('false'), default=False, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    first_completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    xp_awarded = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    last_position_seconds = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    total_duration_seconds = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    view_count = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    seconds_spent = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    last_accessed_at = db.Column(db.DateTime(timezone=True), server_default=db.text('CURRENT_TIMESTAMP'), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'lecture_id', name='uq_student_lesson_progress_student_lecture'),
        db.CheckConstraint('last_position_seconds >= 0 AND (total_duration_seconds = 0 OR last_position_seconds <= total_duration_seconds)', name='chk_lesson_progress_position_bounds'),
        db.CheckConstraint('total_duration_seconds >= 0', name='chk_lesson_progress_duration_nonneg'),
        db.CheckConstraint('view_count >= 0', name='chk_lesson_progress_view_count_nonneg'),
        db.CheckConstraint('(xp_awarded = 0 AND first_completed_at IS NULL) OR (xp_awarded = 50 AND first_completed_at IS NOT NULL)', name='chk_lesson_progress_xp_consistency'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'course_id': self.course_id,
            'lecture_id': self.lecture_id,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'first_completed_at': self.first_completed_at.isoformat() if self.first_completed_at else None,
            'xp_awarded': self.xp_awarded,
            'last_position_seconds': self.last_position_seconds,
            'total_duration_seconds': self.total_duration_seconds,
            'view_count': self.view_count,
            'seconds_spent': self.seconds_spent,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }


class StudentDailyActivity(db.Model):
    __tablename__ = 'student_daily_activity'

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    activity_date = db.Column(db.Date, nullable=False, server_default=db.text("(CURRENT_TIMESTAMP AT TIME ZONE 'Africa/Lagos')::date"), default=lambda: datetime.now(timezone(timedelta(hours=1))).date())
    minutes_spent = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    seconds_spent = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    lessons_completed = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    questions_practiced = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    xp_earned = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    last_active_at = db.Column(db.DateTime(timezone=True), server_default=db.text('CURRENT_TIMESTAMP'), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'activity_date', name='uq_student_daily_activity_student_date'),
        db.CheckConstraint('minutes_spent >= 0', name='chk_daily_activity_minutes_nonneg'),
        db.CheckConstraint('seconds_spent >= 0', name='ck_student_daily_seconds_non_negative'),
        db.CheckConstraint('lessons_completed >= 0', name='chk_daily_activity_lessons_nonneg'),
        db.CheckConstraint('questions_practiced >= 0', name='chk_daily_activity_questions_nonneg'),
        db.CheckConstraint('xp_earned >= 0', name='chk_daily_activity_xp_nonneg'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'activity_date': self.activity_date.isoformat() if self.activity_date else None,
            'minutes_spent': self.minutes_spent,
            'seconds_spent': self.seconds_spent,
            'lessons_completed': self.lessons_completed,
            'questions_practiced': self.questions_practiced,
            'xp_earned': self.xp_earned,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None
        }


class StudentDiagnosticHistory(db.Model):
    __tablename__ = 'student_diagnostic_history'

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text('gen_random_uuid()'), default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(50), server_default=db.text("'Mathematics'"), default='Mathematics', nullable=False)
    attempt_number = db.Column(db.Integer, server_default=db.text('1'), default=1, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Integer, nullable=False)
    topic_breakdown = db.Column(JSONB, server_default=db.text("'{}'::jsonb"), default=dict, nullable=False)
    recommendations = db.Column(JSONB, server_default=db.text("'[]'::jsonb"), default=list, nullable=False)
    time_spent_seconds = db.Column(db.Integer, server_default=db.text('0'), default=0, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), server_default=db.text('CURRENT_TIMESTAMP'), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject', 'attempt_number', name='uq_student_diagnostic_attempt'),
        db.CheckConstraint('score >= 0', name='chk_diagnostic_history_score_nonneg'),
        db.CheckConstraint('max_score > 0', name='chk_diagnostic_history_max_score_pos'),
        db.CheckConstraint('score <= max_score', name='chk_diagnostic_history_score_max'),
        db.CheckConstraint('attempt_number > 0', name='chk_diagnostic_history_attempt_pos'),
        db.CheckConstraint("percentage = ROUND((score::numeric / max_score::numeric) * 100)::integer", name='chk_diagnostic_history_percentage_calc'),
        db.CheckConstraint("jsonb_typeof(topic_breakdown) = 'object'", name='chk_diagnostic_topic_breakdown_object'),
        db.CheckConstraint("jsonb_typeof(recommendations) = 'array'", name='chk_diagnostic_recommendations_array'),
        db.CheckConstraint('time_spent_seconds >= 0', name='chk_diagnostic_history_time_nonneg'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'subject': self.subject,
            'attempt_number': self.attempt_number,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'topic_breakdown': self.topic_breakdown if isinstance(self.topic_breakdown, dict) else {},
            'recommendations': self.recommendations if isinstance(self.recommendations, list) else [],
            'time_spent_seconds': self.time_spent_seconds,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


# ============================================================================
# PHASE 6.3 STUDENT LEARNING CONSTANTS & CONFIGURATION
# ============================================================================

DIAGNOSTIC_QUESTION_BANK = {
    'diag_math_01': {
        'topic': 'Linear Algebra',
        'prompt': 'Solve for x in the linear algebraic equation: 3(x - 2) + 4 = 2(x + 5)',
        'options': ['x = 8', 'x = 12', 'x = 14', 'x = 10'],
        'correct_option': 1,  # 0-indexed: "x = 12"
        'num_options': 4,
        'recommendation_if_incorrect': 'Review linear algebraic equations, bracket expansion, and isolating unknown terms.'
    },
    'diag_math_02': {
        'topic': 'Logarithms & Indices',
        'prompt': 'If log₁₀(2) = 0.3010 and log₁₀(3) = 0.4771, calculate the exact value of log₁₀(18):',
        'options': ['1.2552', '0.9542', '1.1761', '1.0791'],
        'correct_option': 0,  # 0-indexed: "1.2552"
        'num_options': 4,
        'recommendation_if_incorrect': 'Practice logarithmic expansion laws, power rules, and prime-factor decomposition.'
    },
    'diag_math_03': {
        'topic': 'Circle Geometry Theorems',
        'prompt': 'In a circle with center O, the angle subtended by an arc at the center is 110°. Find the angle subtended by the same arc at any point on the circumference:',
        'options': ['220°', '110°', '55°', '90°'],
        'correct_option': 2,  # 0-indexed: "55°"
        'num_options': 4,
        'recommendation_if_incorrect': 'Revise Circle Theorems: angle subtended by an arc at the center versus circumference.'
    }
}

EXAM_COURSE_MAP = {
    'WASSCE': 'wassce-gce-neco-prep',
    'WAEC': 'wassce-gce-neco-prep',
    'NECO': 'wassce-gce-neco-prep',
    'GCE': 'wassce-gce-neco-prep',
    'JAMB': 'utme-postutme-prep',
    'UTME': 'utme-postutme-prep',
    'JAMB/UTME': 'utme-postutme-prep',
    'Post-UTME': 'utme-postutme-prep',
    'POST-UTME': 'utme-postutme-prep',
    'Senior Secondary': 'wassce-gce-neco-prep',
    'School Examination': 'wassce-gce-neco-prep',
    'Not yet decided': 'wassce-gce-neco-prep'
}


def resolve_exam_course(intended_exam):
    """
    Resolves a student's intended_exam to a published course_id based on approved mapping.
    Defaults to 'wassce-gce-neco-prep' if unknown, unspecified, or empty.
    """
    if not intended_exam or not isinstance(intended_exam, str):
        return 'wassce-gce-neco-prep'

    clean_exam = intended_exam.strip()
    if clean_exam in EXAM_COURSE_MAP:
        return EXAM_COURSE_MAP[clean_exam]

    clean_upper = clean_exam.upper()
    for k, v in EXAM_COURSE_MAP.items():
        if k.upper() == clean_upper:
            return v

    return 'wassce-gce-neco-prep'


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

@app.route('/dashboard.html')
@app.route('/dashboard')
def dashboard_page():
    student_id = session.get('student_id')
    if not student_id:
        return redirect('/login.html?next=/dashboard.html')
    try:
        student = Student.query.filter_by(id=uuid.UUID(str(student_id))).first()
    except Exception:
        student = None
    if not student or not student.is_active:
        session.clear()
        return redirect('/login.html?next=/dashboard.html')
    if session.get('session_version') is not None and student.session_version != session.get('session_version'):
        session.clear()
        return redirect('/login.html?next=/dashboard.html')
    return _safe_send_html('dashboard.html')

@app.route('/register.html')
@app.route('/register')
def register_page():
    return _safe_send_html('register.html')

@app.route('/login.html')
@app.route('/login')
def login_page():
    return _safe_send_html('login.html')

@app.route('/forgot-password.html')
@app.route('/forgot-password')
def forgot_password_page():
    return _safe_send_html('forgot-password.html')

@app.route('/reset-password.html')
@app.route('/reset-password')
def reset_password_page():
    return _safe_send_html('reset-password.html')

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
# STUDENT AUTHENTICATION SYSTEM (Phase 5.3: Register, Login, Session, Security)
# ============================================================================

def validate_password_strength(password):
    """Enforces the 4-point password strength policy matching the registration UI."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter (A-Z)."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least 1 lowercase letter (a-z)."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number (0-9)."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least 1 special character."
    return True, ""

def validate_email_format(email):
    """Validates standard email address syntax."""
    if not email or len(email) > 150:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email))

def student_login_required(f):
    """
    Decorator protecting student-only routes.
    Validates session existence, checks student live status against Neon PostgreSQL,
    and invalidates sessions when session_version changes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        student_id = session.get('student_id')
        session_ver = session.get('session_version')
        if not student_id:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required. Please sign in.', 'code': 'UNAUTHORIZED'}), 401
            return redirect(f'/login.html?next={request.path}')
        
        try:
            student = Student.query.filter_by(id=uuid.UUID(str(student_id))).first()
        except Exception as e:
            logging.error(f"[Auth Error] Failed to resolve student session: {e}")
            student = None

        if not student:
            session.clear()
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Account not found or session expired.', 'code': 'UNAUTHORIZED'}), 401
            return redirect('/login.html')

        if not student.is_active:
            session.clear()
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Your account has been deactivated. Please contact administration.', 'code': 'FORBIDDEN'}), 403
            return redirect('/login.html?error=deactivated')

        if session_ver is not None and student.session_version != session_ver:
            session.clear()
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Your session has been invalidated. Please sign in again.', 'code': 'UNAUTHORIZED'}), 401
            return redirect('/login.html?error=session_invalidated')

        return f(student, *args, **kwargs)
    return decorated_function


# ============================================================================
# AUTHENTICATION RATE LIMITING & BRUTE-FORCE DEFENSE
# ============================================================================
import threading

_IN_MEMORY_RATE_LIMITS = {}
_RATE_LIMIT_LOCK = threading.Lock()

def get_client_ip():
    """
    Safely extract the real client IP address.
    With Werkzeug ProxyFix(x_for=1) active, request.remote_addr is securely
    populated from the trusted reverse proxy (Render) hop.
    Falls back to CF-Connecting-IP if Cloudflare CDN is active.
    """
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip.strip()
    return request.remote_addr or '127.0.0.1'

def check_auth_rate_limit(endpoint, ip_address, identifier=None, max_attempts=5, window_seconds=900, lockout_seconds=300):
    """
    Dual-layer rate limit checker:
    1. Checks if locked_until > now in persistent storage (or in-memory fallback).
    2. Checks if attempt_count >= max_attempts within window_seconds.
    Returns: (is_allowed: bool, retry_after_seconds: int, error_message: str)
    """
    now = datetime.now(timezone.utc)
    ident_hash = hashlib.sha256(identifier.lower().strip().encode('utf-8')).hexdigest() if identifier else None

    # Track both IP key (protects against brute-force) and Account key (throttles specific user)
    ip_key = f"ip:{ip_address}:{endpoint}"
    keys_to_check = [(ip_key, max_attempts, lockout_seconds)]
    if ident_hash:
        acct_key = f"acct:{ident_hash}:{endpoint}"
        keys_to_check.append((acct_key, max_attempts, lockout_seconds))

    # Try persistent DB check first
    try:
        from sqlalchemy import inspect
        engine = db.engine
        inspector = inspect(engine)
        if 'auth_rate_limits' in inspector.get_table_names():
            for key, limit, lockout in keys_to_check:
                record = AuthRateLimit.query.filter_by(rate_key=key).first()
                if record:
                    if record.locked_until and record.locked_until > now:
                        retry_after = int((record.locked_until - now).total_seconds())
                        return False, max(retry_after, 1), f"Too many attempts. Please try again in {max(1, (retry_after + 59) // 60)} minute(s)."
                    window_start = now - timedelta(seconds=window_seconds)
                    if record.first_attempt_at < window_start:
                        record.attempt_count = 0
                        record.first_attempt_at = now
                        record.locked_until = None
                        db.session.commit()
                    elif record.attempt_count >= limit:
                        record.locked_until = now + timedelta(seconds=lockout)
                        db.session.commit()
                        return False, lockout, f"Too many attempts. Please try again in {max(1, (lockout + 59) // 60)} minute(s)."
            return True, 0, ""
    except Exception:
        pass

    # In-memory sliding window fallback
    with _RATE_LIMIT_LOCK:
        for key, limit, lockout in keys_to_check:
            entry = _IN_MEMORY_RATE_LIMITS.get(key)
            if entry:
                locked_until = entry.get('locked_until')
                if locked_until and locked_until > now:
                    retry_after = int((locked_until - now).total_seconds())
                    return False, max(retry_after, 1), f"Too many attempts. Please try again in {max(1, (retry_after + 59) // 60)} minute(s)."
                first_attempt = entry.get('first_attempt_at', now)
                if first_attempt < now - timedelta(seconds=window_seconds):
                    _IN_MEMORY_RATE_LIMITS[key] = {'count': 0, 'first_attempt_at': now, 'locked_until': None}
                elif entry.get('count', 0) >= limit:
                    locked = now + timedelta(seconds=lockout)
                    entry['locked_until'] = locked
                    return False, lockout, f"Too many attempts. Please try again in {max(1, (lockout + 59) // 60)} minute(s)."
    return True, 0, ""

def record_auth_failure(endpoint, ip_address, identifier=None, lockout_seconds=300):
    """Increment failed attempt counters in persistent DB and in-memory cache with atomic PostgreSQL upserts."""
    now = datetime.now(timezone.utc)
    ident_hash = hashlib.sha256(identifier.lower().strip().encode('utf-8')).hexdigest() if identifier else None
    keys = [f"ip:{ip_address}:{endpoint}"]
    if ident_hash:
        keys.append(f"acct:{ident_hash}:{endpoint}")

    try:
        from sqlalchemy import inspect, text
        engine = db.engine
        inspector = inspect(engine)
        if 'auth_rate_limits' in inspector.get_table_names():
            for key in keys:
                db.session.execute(text("""
                    INSERT INTO public.auth_rate_limits (
                        id, rate_key, endpoint, ip_address, identifier_hash, attempt_count, first_attempt_at, last_attempt_at
                    ) VALUES (
                        :id, :rate_key, :endpoint, :ip_address, :identifier_hash, 1, :now, :now
                    )
                    ON CONFLICT (rate_key) DO UPDATE SET
                        attempt_count = auth_rate_limits.attempt_count + 1,
                        last_attempt_at = EXCLUDED.last_attempt_at;
                """), {
                    'id': str(uuid.uuid4()),
                    'rate_key': key,
                    'endpoint': endpoint,
                    'ip_address': ip_address,
                    'identifier_hash': ident_hash,
                    'now': now
                })
            # Opportunistic retention pruning: delete records older than 24 hours that are not actively locked
            retention_cutoff = now - timedelta(hours=24)
            db.session.execute(text("""
                DELETE FROM public.auth_rate_limits
                WHERE last_attempt_at < :cutoff
                  AND (locked_until IS NULL OR locked_until < :now);
            """), {
                'cutoff': retention_cutoff,
                'now': now
            })
            db.session.commit()
    except Exception:
        db.session.rollback()

    with _RATE_LIMIT_LOCK:
        for key in keys:
            if key not in _IN_MEMORY_RATE_LIMITS:
                _IN_MEMORY_RATE_LIMITS[key] = {'count': 1, 'first_attempt_at': now, 'locked_until': None}
            else:
                _IN_MEMORY_RATE_LIMITS[key]['count'] = _IN_MEMORY_RATE_LIMITS[key].get('count', 0) + 1

def clear_auth_limits(endpoint, ip_address, identifier=None):
    """Reset failed counters upon successful authentication."""
    ident_hash = hashlib.sha256(identifier.lower().strip().encode('utf-8')).hexdigest() if identifier else None
    keys = [f"ip:{ip_address}:{endpoint}"]
    if ident_hash:
        keys.append(f"acct:{ident_hash}:{endpoint}")

    try:
        from sqlalchemy import inspect
        engine = db.engine
        inspector = inspect(engine)
        if 'auth_rate_limits' in inspector.get_table_names():
            for key in keys:
                AuthRateLimit.query.filter_by(rate_key=key).delete()
            db.session.commit()
    except Exception:
        db.session.rollback()

    with _RATE_LIMIT_LOCK:
        for key in keys:
            _IN_MEMORY_RATE_LIMITS.pop(key, None)


@app.route('/api/auth/csrf-token', methods=['GET'])
def get_auth_csrf_token():
    """Generates or returns a session-anchored CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return jsonify({'success': True, 'csrf_token': session['csrf_token']})


@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """
    Student Registration Endpoint.
    Normalizes email, validates required fields, enforces password policy,
    hashes password using Werkzeug scrypt, and inserts record into public.students.
    """
    data = request.get_json(silent=True) or {}
    
    fullname = (data.get('fullname') or data.get('full_name') or '').strip()
    raw_email = (data.get('email') or '').strip()
    norm_email = raw_email.lower()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or data.get('confirmPassword') or ''
    education_level = (data.get('education_level') or '').strip()
    intended_exam = (data.get('intended_exam') or '').strip()
    terms = data.get('terms')
    phone = (data.get('phone') or '').strip() or None

    # Server-side validation
    if not fullname or len(fullname) < 2:
        return jsonify({'success': False, 'message': 'Please provide your full name (at least 2 characters).', 'field': 'fullname'}), 400

    if not norm_email or not validate_email_format(norm_email):
        return jsonify({'success': False, 'message': 'Please provide a valid email address.', 'field': 'email'}), 400

    valid_levels = {'JSS 1', 'JSS 2', 'JSS 3', 'SS1', 'SS2', 'SS3', 'JAMB/UTME', 'Other supported programmes'}
    if education_level not in valid_levels:
        return jsonify({'success': False, 'message': 'Please select a valid education level.', 'field': 'education_level'}), 400

    valid_exams = {'WASSCE', 'NECO', 'JAMB/UTME', 'School Examination', 'Not yet decided'}
    if intended_exam not in valid_exams:
        return jsonify({'success': False, 'message': 'Please select a valid target examination.', 'field': 'intended_exam'}), 400

    if not terms:
        return jsonify({'success': False, 'message': 'You must accept the Terms of Service and Privacy Policy.', 'field': 'terms'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.', 'field': 'confirm_password'}), 400

    is_strong, pwd_err = validate_password_strength(password)
    if not is_strong:
        return jsonify({'success': False, 'message': pwd_err, 'field': 'password'}), 400

    # Duplicate email check
    try:
        existing = Student.query.filter_by(email=norm_email).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'An account with this email address already exists. Please sign in or use password recovery.',
                'field': 'email'
            }), 409

        p_hash = generate_password_hash(password, method='scrypt')
        now = datetime.now(timezone.utc)
        new_student = Student(
            id=uuid.uuid4(),
            full_name=fullname,
            email=norm_email,
            password_hash=p_hash,
            education_level=education_level,
            intended_exam=intended_exam,
            phone=phone,
            is_active=True,
            session_version=1,
            created_at=now,
            updated_at=now
        )
        db.session.add(new_student)
        db.session.commit()

        logging.info(f"[Auth Audit] Student account successfully created for {norm_email}")
        return jsonify({
            'success': True,
            'message': 'Account created successfully! Please sign in with your credentials.',
            'redirect': '/login.html'
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Auth Error] Registration failure for {norm_email}: {e}")
        return jsonify({'success': False, 'message': 'An unexpected database error occurred. Please try again later.'}), 500


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """
    Student Login Endpoint.
    Validates credentials against public.students, protects against session fixation,
    checks account active status, issues signed session cookie, and updates last_login.
    Applies proxy-aware IP and account rate limiting with progressive lockout.
    """
    data = request.get_json(silent=True) or {}
    raw_email = (data.get('email') or '').strip()
    norm_email = raw_email.lower()
    password = data.get('password') or ''
    remember_me = bool(data.get('remember_me') or data.get('rememberMe'))

    client_ip = get_client_ip()

    # Rate Limit Check: max 5 failed attempts per 15 min, 5-minute lockout
    allowed, retry_sec, limit_msg = check_auth_rate_limit(
        'login', client_ip, identifier=norm_email if norm_email else None,
        max_attempts=5, window_seconds=900, lockout_seconds=300
    )
    if not allowed:
        resp = jsonify({
            'success': False,
            'error': 'TOO_MANY_REQUESTS',
            'message': limit_msg,
            'retry_after': retry_sec
        })
        resp.headers['Retry-After'] = str(retry_sec)
        return resp, 429

    if not norm_email or not password:
        return jsonify({'success': False, 'message': 'Please provide both email address and password.'}), 400

    try:
        student = Student.query.filter_by(email=norm_email).first()
        
        # Constant-time comparison & generic rejection to prevent user enumeration
        if not student or not check_password_hash(student.password_hash, password):
            record_auth_failure('login', client_ip, identifier=norm_email, lockout_seconds=300)
            return jsonify({'success': False, 'message': 'Invalid email address or password.'}), 401

        if not student.is_active:
            return jsonify({'success': False, 'message': 'Your account has been deactivated. Please contact administration.'}), 403

        # Clear failed login attempts upon success
        clear_auth_limits('login', client_ip, identifier=norm_email)

        # Protect against session fixation
        session.clear()

        # Minimal secure session payload
        session['student_id'] = str(student.id)
        session['session_version'] = student.session_version
        session['csrf_token'] = secrets.token_hex(32)
        session.permanent = remember_me

        # Update last_login audit timestamp
        student.last_login = datetime.now(timezone.utc)
        db.session.commit()

        logging.info(f"[Auth Audit] Student login successful for {norm_email} (ID: {student.id})")
        return jsonify({
            'success': True,
            'message': f'Welcome back, {student.full_name.split()[0]}!',
            'student': student.to_dict(),
            'csrf_token': session['csrf_token'],
            'redirect': '/dashboard.html'
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Auth Error] Login failure for {norm_email}: {e}")
        return jsonify({'success': False, 'message': 'An unexpected authentication error occurred.'}), 500


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """
    Student Logout Endpoint.
    Clears the Flask server-side session and invalidates the session cookie.
    """
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Signed out successfully.',
        'redirect': '/login.html'
    }), 200


@app.route('/api/auth/me', methods=['GET'])
@student_login_required
def auth_me(student):
    """
    Current Authenticated Student Profile.
    Returns the live student profile for the session owner.
    """
    return jsonify({
        'success': True,
        'student': student.to_dict(),
        'csrf_token': session.get('csrf_token')
    }), 200


@app.route('/api/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    """
    Password Recovery Endpoint.
    Accepts student email, generates a 256-bit cryptographically secure reset token,
    hashes the token with SHA-256 for storage, enforces a 60-minute single-use TTL,
    applies proxy-aware rate limiting (5 req / 15 min), and returns a generic message to prevent user enumeration.
    """
    data = request.get_json(silent=True) or {}
    raw_email = (data.get('email') or '').strip()
    norm_email = raw_email.lower()

    client_ip = get_client_ip()

    # Rate limiting: max 5 requests per 15 minutes per IP/account
    allowed, retry_sec, limit_msg = check_auth_rate_limit(
        'forgot_password', client_ip, identifier=norm_email if norm_email else None,
        max_attempts=5, window_seconds=900, lockout_seconds=900
    )
    if not allowed:
        resp = jsonify({
            'success': False,
            'error': 'TOO_MANY_REQUESTS',
            'message': limit_msg,
            'retry_after': retry_sec
        })
        resp.headers['Retry-After'] = str(retry_sec)
        return resp, 429

    generic_response = {
        'success': True,
        'message': 'If an account with that email address exists, password reset instructions have been sent.'
    }

    if not norm_email or not validate_email_format(norm_email):
        return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400

    # Record rate limit attempt
    record_auth_failure('forgot_password', client_ip, identifier=norm_email, lockout_seconds=900)

    try:
        student = Student.query.filter_by(email=norm_email, is_active=True).first()
        now = datetime.now(timezone.utc)

        if student:
            # Invalidate any existing unused reset tokens for this student
            PasswordResetToken.query.filter_by(student_id=student.id, used_at=None).update({'used_at': now})

            raw_token = secrets.token_urlsafe(32) # 256 bits of entropy
            token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
            expires_at = now + timedelta(hours=1)

            reset_record = PasswordResetToken(
                id=uuid.uuid4(),
                student_id=student.id,
                token_hash=token_hash,
                expires_at=expires_at,
                created_at=now
            )
            db.session.add(reset_record)
            db.session.commit()

            # Attempt SMTP delivery
            base_url = request.host_url.rstrip('/')
            reset_link = f"{base_url}/reset-password.html?token={raw_token}"
            subject = "🔐 Reset Your Ziglag Institute Password"
            body_text = f"""Dear {student.full_name},

We received a request to reset the password for your Ziglag Institute student account.

Click the link below (or paste it into your browser) to choose a new password:
{reset_link}

This link is valid for 60 minutes and can only be used once.

If you did not request a password reset, please ignore this email. Your account remains completely secure.

Warm regards,
Mr. Isaac Olusola & The Ziglag Institute Team
https://my-math-website.onrender.com
"""
            send_system_email(student.email, subject, body_text, reply_to="ziglaginstitute@gmail.com")
            logging.info(f"[Auth Audit] Password reset token issued for {norm_email}")
        else:
            # Perform dummy scrypt hash to equalize response timing against enumeration
            generate_password_hash("dummy_timing_padding", method='scrypt')

        return jsonify(generic_response), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Auth Error] Forgot password failure for {norm_email}: {e}")
        return jsonify(generic_response), 200


@app.route('/api/auth/reset-password', methods=['POST'])
def auth_reset_password():
    """
    Password Reset Confirmation Endpoint.
    Validates token hash, checks single-use and expiration status,
    updates password_hash using Werkzeug scrypt, increments session_version,
    applies proxy-aware rate limiting, and invalidates any prior active student sessions.
    """
    data = request.get_json(silent=True) or {}
    raw_token = (data.get('token') or '').strip()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or data.get('confirmPassword') or ''

    client_ip = get_client_ip()
    token_ident = raw_token[:10] if raw_token else 'no_token'

    # Rate limiting: max 5 requests per 15 minutes per IP/token
    allowed, retry_sec, limit_msg = check_auth_rate_limit(
        'reset_password', client_ip, identifier=token_ident,
        max_attempts=5, window_seconds=900, lockout_seconds=900
    )
    if not allowed:
        resp = jsonify({
            'success': False,
            'error': 'TOO_MANY_REQUESTS',
            'message': limit_msg,
            'retry_after': retry_sec
        })
        resp.headers['Retry-After'] = str(retry_sec)
        return resp, 429

    if not raw_token:
        return jsonify({'success': False, 'message': 'Password reset token is required.'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.', 'field': 'confirm_password'}), 400

    is_strong, pwd_err = validate_password_strength(password)
    if not is_strong:
        return jsonify({'success': False, 'message': pwd_err, 'field': 'password'}), 400

    try:
        token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        now = datetime.now(timezone.utc)

        token_record = PasswordResetToken.query.filter_by(token_hash=token_hash).first()

        if not token_record or token_record.used_at is not None or token_record.expires_at < now:
            record_auth_failure('reset_password', client_ip, identifier=token_ident, lockout_seconds=900)
            return jsonify({
                'success': False,
                'message': 'This password reset link is invalid or has expired. Please request a new link.'
            }), 400

        student = db.session.get(Student, token_record.student_id)
        if not student or not student.is_active:
            return jsonify({'success': False, 'message': 'Student account not found or deactivated.'}), 400

        # Clear rate limit counters for this token/IP
        clear_auth_limits('reset_password', client_ip, identifier=token_ident)

        # Update password hash, increment session_version (invalidating active sessions), mark token used
        student.password_hash = generate_password_hash(password, method='scrypt')
        student.session_version += 1
        student.updated_at = now
        token_record.used_at = now
        db.session.commit()

        # Clear any current session
        session.clear()

        logging.info(f"[Auth Audit] Password successfully reset for student ID {student.id}")
        return jsonify({
            'success': True,
            'message': 'Your password has been successfully reset. Please sign in with your new password.',
            'redirect': '/login.html'
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Auth Error] Reset password execution error: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred during password reset.'}), 500

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
    1. Primary: Resend HTTPS API (port 443) when RESEND_API_KEY is present.
       - Validates response JSON and confirms message ID.
       - Reads sender address from EMAIL_FROM (with fallbacks to RESEND_FROM, MAIL_DEFAULT_SENDER).
       - Never hardcodes credentials or exposes internal error details to students.
       - Safe error logging without leaking secrets.
       - Handles Resend testing domain (onboarding@resend.dev) restrictions vs verified custom domain.
    2. Fallback: SMTP over TLS/SSL when SMTP_USERNAME and SMTP_PASSWORD / MAIL_PASSWORD are present.
    """
    if not to_email:
        return False

    norm_to_email = to_email.strip().lower()
    resend_key = (os.getenv('RESEND_API_KEY') or '').strip()

    if resend_key:
        try:
            import json
            import urllib.request
            import urllib.error

            # Resolve sender address from environment
            configured_sender = (
                os.getenv('EMAIL_FROM')
                or os.getenv('RESEND_FROM')
                or os.getenv('MAIL_DEFAULT_SENDER')
                or os.getenv('SMTP_USERNAME')
                or os.getenv('MAIL_USERNAME')
                or 'onboarding@resend.dev'
            ).strip()

            # Format From header cleanly:
            # Preserves full "Name <email@domain>" if provided
            # Falls back to onboarding@resend.dev if using unverified gmail without custom domain
            if '<' in configured_sender and '>' in configured_sender:
                from_header = configured_sender
            elif '@gmail.com' in configured_sender and not os.getenv('RESEND_CUSTOM_DOMAIN'):
                from_header = "Ziglag Institute <onboarding@resend.dev>"
            elif configured_sender == 'onboarding@resend.dev':
                from_header = "Ziglag Institute <onboarding@resend.dev>"
            else:
                from_header = f"Ziglag Institute <{configured_sender}>"

            payload = {
                "from": from_header,
                "to": [norm_to_email],
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
                    "User-Agent": "ZiglagMathPortal-Auth/1.0"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_bytes = resp.read()
                resp_data = json.loads(resp_bytes.decode('utf-8'))
                message_id = resp_data.get('id')
                if resp.status in (200, 201) and message_id:
                    logging.info(f"[Email Resend API] Successfully dispatched email to {norm_to_email} (Resend Message ID: {message_id})")
                    return True
                else:
                    logging.warning(f"[Email Resend API] Unexpected Resend response status {resp.status}: {resp_data}")
        except urllib.error.HTTPError as http_err:
            try:
                err_body = http_err.read().decode('utf-8', errors='replace')
                err_json = json.loads(err_body)
                err_name = err_json.get('name') or 'HTTPError'
                err_msg = err_json.get('message') or err_body
            except Exception:
                err_name = 'HTTPError'
                err_msg = str(http_err)
            logging.error(f"[Email Resend API Error] Status {http_err.code} ({err_name}): {err_msg}")
        except Exception as re_err:
            logging.error(f"[Email Resend API Exception] Failed to send email to {norm_to_email}: {type(re_err).__name__}")

    # Standard SMTP Fallback
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
        logging.info(f"[Email Notice] SMTP credentials not configured for {norm_to_email} and Resend key not active.")
        return False

    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = norm_to_email
        if reply_to:
            msg['Reply-To'] = reply_to
        msg.set_content(body_text)

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

        logging.info(f"[Email SMTP] Sent email to {norm_to_email}")
        return True
    except Exception as err:
        logging.warning(f"[Email SMTP Notice] Transmission notice to {norm_to_email}: {type(err).__name__}")
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
# PHASE 6.3 STUDENT LEARNING & DASHBOARD REST APIs
# ============================================================================

@app.route('/api/student/diagnostic/submit', methods=['POST'])
@student_login_required
def submit_diagnostic_assessment(student):
    """
    Submits and server-evaluates a diagnostic assessment.

    Security & Validation:
    - Derives student identity exclusively from authenticated session (via @student_login_required).
    - Rejects any client-supplied 'student_id' in body (HTTP 400).
    - Enforces CSRF token check (X-CSRF-Token, X-CSRFToken, or csrf_token).
    - Validates answers contain exactly the expected question IDs from DIAGNOSTIC_QUESTION_BANK.
    - Rejects missing, duplicate, unknown question IDs, non-integer, boolean, or out-of-range choices.
    - Rejects negative or non-integer time_spent_seconds.

    Evaluation:
    - Calculates score, max_score, and Decimal ROUND_HALF_UP percentage.
    - Generates topic_breakdown (JSON object) and recommendations (JSON array).
    - Allocates attempt_number concurrency-safely via row lock on Student.id.
    - Records 0 XP awarded (diagnostic assessments never grant XP).
    - Updates student_daily_activity.questions_practiced += max_score in the same transaction.
    - Never exposes correct answers in the response.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    # 1. Reject student_id in request body
    if 'student_id' in data:
        return jsonify({
            'success': False,
            'message': 'Student identity cannot be supplied in request body; it is derived from session.',
            'code': 'FORBIDDEN_FIELD'
        }), 400

    # 2. CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    # 3. Subject Validation
    raw_subject = data.get('subject', 'Mathematics')
    if not isinstance(raw_subject, str) or not raw_subject.strip() or len(raw_subject.strip()) > 50:
        return jsonify({
            'success': False,
            'message': 'Subject must be a non-empty string of at most 50 characters.',
            'code': 'INVALID_SUBJECT'
        }), 400
    subject = raw_subject.strip()

    # 4. time_spent_seconds Validation
    raw_time = data.get('time_spent_seconds', 0)
    if isinstance(raw_time, bool) or not isinstance(raw_time, int) or raw_time < 0:
        return jsonify({
            'success': False,
            'message': 'time_spent_seconds must be a non-negative integer.',
            'code': 'INVALID_TIME'
        }), 400
    time_spent_seconds = raw_time

    # 5. Answers Structure & Completeness Validation
    answers = data.get('answers')
    if not isinstance(answers, list) or len(answers) == 0:
        return jsonify({
            'success': False,
            'message': 'answers must be a non-empty list of question responses.',
            'code': 'INVALID_ANSWERS'
        }), 400

    expected_qids = set(DIAGNOSTIC_QUESTION_BANK.keys())
    submitted_qids = []
    answer_map = {}

    for idx, ans in enumerate(answers):
        if not isinstance(ans, dict):
            return jsonify({
                'success': False,
                'message': f'Answer item at index {idx} must be a JSON object.',
                'code': 'INVALID_ANSWER_ITEM'
            }), 400

        qid = ans.get('question_id')
        if not isinstance(qid, str) or not qid.strip():
            return jsonify({
                'success': False,
                'message': f'question_id at index {idx} must be a non-empty string.',
                'code': 'INVALID_QUESTION_ID'
            }), 400
        qid = qid.strip()

        # Reject unknown question IDs
        if qid not in expected_qids:
            return jsonify({
                'success': False,
                'message': f'Unknown question ID: {qid}. Expected one of {sorted(list(expected_qids))}.',
                'code': 'UNKNOWN_QUESTION_ID'
            }), 400

        submitted_qids.append(qid)

        # Validate selected_option: must be genuine int, non-boolean, and within valid range
        opt = ans.get('selected_option')
        if isinstance(opt, bool) or not isinstance(opt, int):
            return jsonify({
                'success': False,
                'message': f'selected_option for question {qid} must be an integer, not boolean or other type.',
                'code': 'INVALID_OPTION_TYPE'
            }), 400

        q_spec = DIAGNOSTIC_QUESTION_BANK[qid]
        if opt < 0 or opt >= q_spec['num_options']:
            return jsonify({
                'success': False,
                'message': f'selected_option {opt} for question {qid} is out of valid range (0 to {q_spec["num_options"] - 1}).',
                'code': 'OPTION_OUT_OF_RANGE'
            }), 400

        answer_map[qid] = opt

    # Check for duplicate question IDs
    if len(submitted_qids) != len(set(submitted_qids)):
        return jsonify({
            'success': False,
            'message': 'Duplicate question IDs detected in submission.',
            'code': 'DUPLICATE_QUESTION_ID'
        }), 400

    # Check for missing questions (must contain exactly the expected question IDs)
    missing_ids = expected_qids - set(submitted_qids)
    if missing_ids:
        return jsonify({
            'success': False,
            'message': f'Missing expected diagnostic question(s): {sorted(list(missing_ids))}.',
            'code': 'MISSING_QUESTIONS'
        }), 400

    # 6. Authoritative Server-Side Evaluation
    max_score = len(DIAGNOSTIC_QUESTION_BANK)
    score = 0
    topic_breakdown = {}
    recommendations = []

    for qid, q_spec in DIAGNOSTIC_QUESTION_BANK.items():
        topic = q_spec['topic']
        student_choice = answer_map[qid]
        is_correct = (student_choice == q_spec['correct_option'])

        if is_correct:
            score += 1
        else:
            rec = q_spec.get('recommendation_if_incorrect')
            if rec and rec not in recommendations:
                recommendations.append(rec)

        topic_breakdown[topic] = {
            'score': 1 if is_correct else 0,
            'max_score': 1,
            'percentage': 100 if is_correct else 0,
            'is_correct': is_correct,
            'needs_remediation': not is_correct
        }

    # Decimal ROUND_HALF_UP matching PostgreSQL ROUND((score::numeric / max_score::numeric) * 100)::integer
    pct_decimal = (Decimal(score) * Decimal(100) / Decimal(max_score)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    percentage = int(pct_decimal)

    # 7. Database Persistence & Daily Activity Update in One Atomic Transaction
    try:
        # Acquire row lock on Student to serialize concurrent attempt allocations for this student
        db.session.query(Student.id).filter_by(id=student.id).with_for_update().one()

        # Allocate concurrency-safe attempt_number
        max_attempt = db.session.query(
            func.coalesce(func.max(StudentDiagnosticHistory.attempt_number), 0)
        ).filter_by(student_id=student.id, subject=subject).scalar()
        attempt_number = int(max_attempt) + 1

        # Create diagnostic history record
        diag_record = StudentDiagnosticHistory(
            id=uuid.uuid4(),
            student_id=student.id,
            subject=subject,
            attempt_number=attempt_number,
            score=score,
            max_score=max_score,
            percentage=percentage,
            topic_breakdown=topic_breakdown,
            recommendations=recommendations,
            time_spent_seconds=time_spent_seconds,
            completed_at=datetime.now(timezone.utc)
        )
        db.session.add(diag_record)

        # Concurrency-safe atomic UPSERT on student_daily_activity
        # Diagnostic awards 0 XP; increments questions_practiced by max_score (3)
        daily_upsert_sql = text("""
            INSERT INTO public.student_daily_activity (
                id, student_id, activity_date, minutes_spent, lessons_completed, questions_practiced, xp_earned, last_active_at
            )
            VALUES (
                gen_random_uuid(), :student_id, (CURRENT_TIMESTAMP AT TIME ZONE 'Africa/Lagos')::date,
                0, 0, :questions_count, 0, CURRENT_TIMESTAMP
            )
            ON CONFLICT (student_id, activity_date)
            DO UPDATE SET
                questions_practiced = public.student_daily_activity.questions_practiced + EXCLUDED.questions_practiced,
                last_active_at = CURRENT_TIMESTAMP;
        """)
        db.session.execute(daily_upsert_sql, {
            'student_id': str(student.id),
            'questions_count': max_score
        })

        # Commit both operations atomically
        db.session.commit()

        # Build clean response (zero correct answer options exposed)
        evaluation_data = diag_record.to_dict()
        evaluation_data['xp_awarded'] = 0

        return jsonify({
            'success': True,
            'message': 'Diagnostic assessment evaluated and recorded successfully.',
            'evaluation': evaluation_data
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Diagnostic Error] Failed to persist assessment for student {student.id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to record diagnostic assessment due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


@app.route('/api/student/progress/toggle-lesson', methods=['POST'])
@student_login_required
def toggle_lesson_progress(student):
    """
    Toggles lesson completion status, updates watch duration and playback position,
    and grants exactly 50 XP on verified first-time completion within an atomic transaction.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    # 1. Reject client-supplied forbidden fields
    if 'student_id' in data:
        return jsonify({
            'success': False,
            'message': 'student_id cannot be supplied in request body; it is derived from session.',
            'code': 'FORBIDDEN_FIELD'
        }), 400

    if 'xp_awarded' in data:
        return jsonify({
            'success': False,
            'message': 'xp_awarded cannot be supplied by the client; XP is managed exclusively by the server.',
            'code': 'FORBIDDEN_FIELD'
        }), 400

    # 2. CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    # 3. Validate course_id and lecture_id
    raw_course_id = data.get('course_id')
    raw_lecture_id = data.get('lecture_id')
    if not isinstance(raw_course_id, str) or not raw_course_id.strip():
        return jsonify({
            'success': False,
            'message': 'course_id must be a non-empty string.',
            'code': 'INVALID_COURSE_ID'
        }), 400
    if not isinstance(raw_lecture_id, str) or not raw_lecture_id.strip():
        return jsonify({
            'success': False,
            'message': 'lecture_id must be a non-empty string.',
            'code': 'INVALID_LECTURE_ID'
        }), 400

    course_id = raw_course_id.strip()
    lecture_id = raw_lecture_id.strip()

    # 4. Validate is_completed: must be genuine JSON boolean
    is_completed = data.get('is_completed')
    if not isinstance(is_completed, bool):
        return jsonify({
            'success': False,
            'message': 'is_completed must be a genuine boolean value (true or false).',
            'code': 'INVALID_COMPLETED_STATUS'
        }), 400

    # 5. Validate last_position_seconds and total_duration_seconds
    raw_pos = data.get('last_position_seconds', 0)
    raw_dur = data.get('total_duration_seconds', 0)

    if isinstance(raw_pos, bool) or not isinstance(raw_pos, int) or raw_pos < 0:
        return jsonify({
            'success': False,
            'message': 'last_position_seconds must be a non-negative integer, not boolean.',
            'code': 'INVALID_POSITION'
        }), 400

    if isinstance(raw_dur, bool) or not isinstance(raw_dur, int) or raw_dur < 0:
        return jsonify({
            'success': False,
            'message': 'total_duration_seconds must be a non-negative integer, not boolean.',
            'code': 'INVALID_DURATION'
        }), 400

    if raw_dur > 0 and raw_pos > raw_dur:
        return jsonify({
            'success': False,
            'message': 'last_position_seconds cannot exceed total_duration_seconds.',
            'code': 'POSITION_EXCEEDS_DURATION'
        }), 400

    last_position_seconds = raw_pos
    total_duration_seconds = raw_dur

    # 6. Verify course and lecture existence & publication status
    course = Course.query.filter_by(id=course_id).first()
    if not course or not course.is_published:
        return jsonify({
            'success': False,
            'message': f'Course with ID "{course_id}" not found or is currently unpublished.',
            'code': 'COURSE_NOT_FOUND'
        }), 404

    lecture = Lecture.query.filter_by(id=lecture_id).first()
    if not lecture or not lecture.is_published:
        return jsonify({
            'success': False,
            'message': f'Lecture with ID "{lecture_id}" not found or is currently unpublished.',
            'code': 'LECTURE_NOT_FOUND'
        }), 404

    if lecture.course_id != course_id:
        return jsonify({
            'success': False,
            'message': f'Lecture "{lecture_id}" belongs to course "{lecture.course_id}", not "{course_id}".',
            'code': 'RELATIONAL_MISMATCH'
        }), 400

    # 7. Concurrency-Safe Insert-or-Lock Transaction Sequence
    try:
        # Step A: Safe seed insert if no record exists yet (view_count defaults to 0: completion is NOT an opening)
        seed_sql = text("""
            INSERT INTO public.student_lesson_progress (
                id, student_id, course_id, lecture_id, is_completed, xp_awarded,
                last_position_seconds, total_duration_seconds, view_count, last_accessed_at
            )
            VALUES (
                gen_random_uuid(), :student_id, :course_id, :lecture_id, FALSE, 0,
                :pos, :dur, 0, CURRENT_TIMESTAMP
            )
            ON CONFLICT (student_id, lecture_id) DO NOTHING;
        """)
        db.session.execute(seed_sql, {
            'student_id': str(student.id),
            'course_id': course_id,
            'lecture_id': lecture_id,
            'pos': last_position_seconds,
            'dur': total_duration_seconds
        })

        # Step B: Select row with exclusive lock
        progress = db.session.query(StudentLessonProgress).filter_by(
            student_id=student.id, lecture_id=lecture_id
        ).with_for_update().one()

        xp_to_award = 0
        lessons_inc = 0
        now = datetime.now(timezone.utc)

        if is_completed:
            progress.is_completed = True
            if progress.first_completed_at is None:
                # FIRST-TIME COMPLETION: Award exactly 50 XP
                progress.first_completed_at = now
                progress.completed_at = now
                progress.xp_awarded = 50
                xp_to_award = 50
                lessons_inc = 1
            else:
                # REPEATED COMPLETION: Zero additional XP
                if progress.completed_at is None:
                    progress.completed_at = now
                xp_to_award = 0
                lessons_inc = 0
        else:
            # UNCHECKING: Mark incomplete, clear completed_at, but PRESERVE first_completed_at and xp_awarded
            progress.is_completed = False
            progress.completed_at = None
            xp_to_award = 0
            lessons_inc = 0

        # Update playback metrics and access timestamp without modifying view_count
        progress.last_position_seconds = last_position_seconds
        if total_duration_seconds > 0:
            progress.total_duration_seconds = max(progress.total_duration_seconds or 0, total_duration_seconds)
        progress.last_accessed_at = now

        # Step C: Atomically update student_daily_activity in the same transaction
        daily_upsert_sql = text("""
            INSERT INTO public.student_daily_activity (
                id, student_id, activity_date, minutes_spent, lessons_completed, questions_practiced, xp_earned, last_active_at
            )
            VALUES (
                gen_random_uuid(), :student_id, (CURRENT_TIMESTAMP AT TIME ZONE 'Africa/Lagos')::date,
                0, :lessons_inc, 0, :xp_inc, CURRENT_TIMESTAMP
            )
            ON CONFLICT (student_id, activity_date)
            DO UPDATE SET
                xp_earned = public.student_daily_activity.xp_earned + EXCLUDED.xp_earned,
                lessons_completed = public.student_daily_activity.lessons_completed + EXCLUDED.lessons_completed,
                last_active_at = CURRENT_TIMESTAMP;
        """)
        db.session.execute(daily_upsert_sql, {
            'student_id': str(student.id),
            'lessons_inc': lessons_inc,
            'xp_inc': xp_to_award
        })

        # Step D: Commit both operations atomically
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Lesson progress updated successfully.',
            'progress': progress.to_dict(),
            'xp_awarded_this_request': xp_to_award
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Progress Error] Failed to update lesson progress for student {student.id}, lecture {lecture_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to record lesson progress due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


@app.route('/api/student/progress/open-lecture', methods=['POST'])
@student_login_required
def open_lecture(student):
    """
    Records genuine lecture-opening event.
    Creates progress record if absent (view_count = 1), or increments view_count (+1).
    Does NOT award XP, increment lessons_completed, or alter playback positions / completion status.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    # 1. Reject client-supplied student_id
    if 'student_id' in data:
        return jsonify({
            'success': False,
            'message': 'student_id cannot be supplied in request body; it is derived from session.',
            'code': 'FORBIDDEN_FIELD'
        }), 400

    # 2. CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    # 3. Validate course_id and lecture_id
    raw_course_id = data.get('course_id')
    raw_lecture_id = data.get('lecture_id')
    if not isinstance(raw_course_id, str) or not raw_course_id.strip():
        return jsonify({
            'success': False,
            'message': 'course_id must be a non-empty string.',
            'code': 'INVALID_COURSE_ID'
        }), 400
    if not isinstance(raw_lecture_id, str) or not raw_lecture_id.strip():
        return jsonify({
            'success': False,
            'message': 'lecture_id must be a non-empty string.',
            'code': 'INVALID_LECTURE_ID'
        }), 400

    course_id = raw_course_id.strip()
    lecture_id = raw_lecture_id.strip()

    # 4. Verify course and lecture existence & publication status
    course = Course.query.filter_by(id=course_id).first()
    if not course or not course.is_published:
        return jsonify({
            'success': False,
            'message': f'Course with ID "{course_id}" not found or is currently unpublished.',
            'code': 'COURSE_NOT_FOUND'
        }), 404

    lecture = Lecture.query.filter_by(id=lecture_id).first()
    if not lecture or not lecture.is_published:
        return jsonify({
            'success': False,
            'message': f'Lecture with ID "{lecture_id}" not found or is currently unpublished.',
            'code': 'LECTURE_NOT_FOUND'
        }), 404

    if lecture.course_id != course_id:
        return jsonify({
            'success': False,
            'message': f'Lecture "{lecture_id}" belongs to course "{lecture.course_id}", not "{course_id}".',
            'code': 'RELATIONAL_MISMATCH'
        }), 400

    # 5. Concurrency-Safe View Count Increment & Progress Retrieval
    try:
        # Atomic UPSERT: view_count = 1 on insert, or view_count = view_count + 1 on conflict
        # Does NOT reset completion status or position
        upsert_view_sql = text("""
            INSERT INTO public.student_lesson_progress (
                id, student_id, course_id, lecture_id, is_completed, xp_awarded,
                last_position_seconds, total_duration_seconds, view_count, last_accessed_at
            )
            VALUES (
                gen_random_uuid(), :student_id, :course_id, :lecture_id, FALSE, 0,
                0, 0, 1, CURRENT_TIMESTAMP
            )
            ON CONFLICT (student_id, lecture_id)
            DO UPDATE SET
                view_count = public.student_lesson_progress.view_count + 1,
                last_accessed_at = CURRENT_TIMESTAMP
            RETURNING id, student_id, course_id, lecture_id, is_completed, completed_at,
                      first_completed_at, xp_awarded, last_position_seconds,
                      total_duration_seconds, view_count, last_accessed_at;
        """)
        res = db.session.execute(upsert_view_sql, {
            'student_id': str(student.id),
            'course_id': course_id,
            'lecture_id': lecture_id
        }).fetchone()

        # Update student_daily_activity touch (0 XP, 0 lessons, 0 minutes)
        daily_touch_sql = text("""
            INSERT INTO public.student_daily_activity (
                id, student_id, activity_date, minutes_spent, lessons_completed, questions_practiced, xp_earned, last_active_at
            )
            VALUES (
                gen_random_uuid(), :student_id, (CURRENT_TIMESTAMP AT TIME ZONE 'Africa/Lagos')::date,
                0, 0, 0, 0, CURRENT_TIMESTAMP
            )
            ON CONFLICT (student_id, activity_date)
            DO UPDATE SET
                last_active_at = CURRENT_TIMESTAMP;
        """)
        db.session.execute(daily_touch_sql, {
            'student_id': str(student.id)
        })

        db.session.commit()

        # Build clean progress dict from returning row
        progress_data = {
            'id': str(res[0]),
            'student_id': str(res[1]),
            'course_id': res[2],
            'lecture_id': res[3],
            'is_completed': res[4],
            'completed_at': res[5].isoformat() if res[5] else None,
            'first_completed_at': res[6].isoformat() if res[6] else None,
            'xp_awarded': res[7],
            'last_position_seconds': res[8],
            'total_duration_seconds': res[9],
            'view_count': res[10],
            'last_accessed_at': res[11].isoformat() if res[11] else None
        }

        return jsonify({
            'success': True,
            'message': 'Lecture opened successfully.',
            'progress': progress_data,
            'xp_awarded_this_request': 0
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Open Lecture Error] Failed to record lecture opening for student {student.id}, lecture {lecture_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to record lecture opening due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


# ============================================================================
# PHASE 6.4.3: REAL-TIME STUDY TIME TRACKING ENDPOINTS
# ============================================================================

@app.route('/api/student/study-session/start', methods=['POST'])
@student_login_required
def start_study_session(student):
    """
    Initializes a new study session for an authenticated student opening a lecture.
    Enforces the primary clock mutex, generates a cryptographically secure session token,
    and sets initial lease ownership if available.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    # 1. Reject client-supplied forbidden fields
    if 'student_id' in data:
        return jsonify({
            'success': False,
            'message': 'student_id cannot be supplied in request body; it is derived from session.',
            'code': 'FORBIDDEN_FIELD'
        }), 400

    # 2. CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    # 3. Validate course_id and lecture_id
    raw_course_id = data.get('course_id')
    raw_lecture_id = data.get('lecture_id')
    if not isinstance(raw_course_id, str) or not raw_course_id.strip():
        return jsonify({
            'success': False,
            'message': 'course_id must be a non-empty string.',
            'code': 'INVALID_COURSE_ID'
        }), 400
    if not isinstance(raw_lecture_id, str) or not raw_lecture_id.strip():
        return jsonify({
            'success': False,
            'message': 'lecture_id must be a non-empty string.',
            'code': 'INVALID_LECTURE_ID'
        }), 400

    course_id = raw_course_id.strip()
    lecture_id = raw_lecture_id.strip()

    # 4. Verify course and lecture existence & publication status
    course = Course.query.filter_by(id=course_id).first()
    if not course or not course.is_published:
        return jsonify({
            'success': False,
            'message': f'Course with ID "{course_id}" not found or is currently unpublished.',
            'code': 'COURSE_NOT_FOUND'
        }), 404

    lecture = Lecture.query.filter_by(id=lecture_id).first()
    if not lecture or not lecture.is_published:
        return jsonify({
            'success': False,
            'message': f'Lecture with ID "{lecture_id}" not found or is currently unpublished.',
            'code': 'LECTURE_NOT_FOUND'
        }), 404

    if lecture.course_id != course_id:
        return jsonify({
            'success': False,
            'message': f'Lecture "{lecture_id}" belongs to course "{lecture.course_id}", not "{course_id}".',
            'code': 'RELATIONAL_MISMATCH'
        }), 400

    session_token = f"tok_sess_{secrets.token_hex(24)}"
    sess_id = uuid.uuid4()
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')

    try:
        sess = db.session() if callable(db.session) else db.session
        tx = sess.begin_nested() if sess.in_transaction() else sess.begin()
        with tx:
            # Mutex 1: Lock student study clock first (global deterministic ordering)
            clock = db.session.execute(text("""
                SELECT student_id, active_session_id, active_lecture_id, lease_expires_at, last_credited_at
                FROM public.student_study_clocks
                WHERE student_id = :sid
                FOR UPDATE;
            """), {'sid': str(student.id)}).fetchone()

            now = db.session.execute(text("SELECT clock_timestamp();")).scalar()

            is_lease_free = False
            if not clock:
                db.session.execute(text("""
                    INSERT INTO public.student_study_clocks (
                        student_id, lease_expires_at, last_credited_at, updated_at
                    ) VALUES (
                        :sid, :now - interval '1 hour', :now - interval '1 hour', :now
                    ) ON CONFLICT (student_id) DO NOTHING;
                """), {'sid': str(student.id), 'now': now})
                is_lease_free = True
            else:
                _, active_session_id, _, lease_expires_at, _ = clock
                if active_session_id is None or lease_expires_at is None or lease_expires_at <= now:
                    is_lease_free = True

            # Mutex 2: Insert new active session record
            db.session.execute(text("""
                INSERT INTO public.student_study_sessions (
                    id, student_id, course_id, lecture_id, session_token,
                    started_at, last_heartbeat_at, expires_at, status,
                    duration_seconds, active_seconds, total_seconds,
                    last_sequence_number, last_credited_seconds, client_ip, user_agent
                ) VALUES (
                    :id, :sid, :cid, :lid, :token,
                    :now, :now, :now + interval '35 seconds', 'ACTIVE',
                    0, 0, 0, 0, 0, :ip, :ua
                );
            """), {
                'id': str(sess_id),
                'sid': str(student.id),
                'cid': course_id,
                'lid': lecture_id,
                'token': session_token,
                'now': now,
                'ip': client_ip[:100] if client_ip else None,
                'ua': user_agent[:500] if user_agent else None
            })

            # Mutex 3: If clock lease was unheld or expired, bind this session immediately
            if is_lease_free:
                db.session.execute(text("""
                    UPDATE public.student_study_clocks
                    SET active_session_id = :id,
                        active_lecture_id = :lid,
                        lease_expires_at = :now + interval '35 seconds',
                        last_credited_at = :now,
                        updated_at = :now
                    WHERE student_id = :sid;
                """), {
                    'id': str(sess_id),
                    'lid': lecture_id,
                    'now': now,
                    'sid': str(student.id)
                })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Study session started successfully.',
            'session_token': session_token,
            'session_id': str(sess_id),
            'course_id': course_id,
            'lecture_id': lecture_id,
            'is_owner': is_lease_free
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Study Session Start Error] Student {student.id}, course {course_id}, lecture {lecture_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to initialize study session due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


@app.route('/api/student/study-session/heartbeat', methods=['POST'])
@student_login_required
def heartbeat_study_session(student):
    """
    Receives periodic study heartbeats from the course player.
    Validates CSRF, monotonicity, and schema, delegating atomic state transitions
    and time crediting to study_tracker.handle_heartbeat_transaction.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    # 1. Reject client-supplied forbidden fields
    if 'student_id' in data:
        return jsonify({
            'success': False,
            'message': 'student_id cannot be supplied in request body; it is derived from session.',
            'code': 'FORBIDDEN_FIELD'
        }), 400

    # 2. CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    # 3. Field validation
    session_token = data.get('session_token')
    course_id = data.get('course_id')
    lecture_id = data.get('lecture_id')
    seq = data.get('seq')
    payload_hash = data.get('payload_hash')
    is_active = data.get('is_active', True)
    event_type = data.get('event_type', 'heartbeat')
    user_notice = data.get('user_notice')

    if not isinstance(session_token, str) or not session_token.strip():
        return jsonify({
            'success': False,
            'message': 'session_token must be a non-empty string.',
            'code': 'INVALID_TOKEN'
        }), 400
    if not isinstance(course_id, str) or not course_id.strip():
        return jsonify({
            'success': False,
            'message': 'course_id must be a non-empty string.',
            'code': 'INVALID_COURSE_ID'
        }), 400
    if not isinstance(lecture_id, str) or not lecture_id.strip():
        return jsonify({
            'success': False,
            'message': 'lecture_id must be a non-empty string.',
            'code': 'INVALID_LECTURE_ID'
        }), 400
    if not isinstance(seq, int) or seq <= 0:
        return jsonify({
            'success': False,
            'message': 'seq must be a positive integer.',
            'code': 'INVALID_SEQUENCE'
        }), 400
    if not isinstance(payload_hash, str) or not payload_hash.strip():
        return jsonify({
            'success': False,
            'message': 'payload_hash must be a non-empty string.',
            'code': 'INVALID_HASH'
        }), 400
    if not isinstance(is_active, bool):
        return jsonify({
            'success': False,
            'message': 'is_active must be a genuine boolean value.',
            'code': 'INVALID_ACTIVE_STATE'
        }), 400
    if not isinstance(event_type, str) or event_type not in ('heartbeat', 'takeover'):
        return jsonify({
            'success': False,
            'message': 'event_type must be either "heartbeat" or "takeover".',
            'code': 'INVALID_EVENT_TYPE'
        }), 400

    try:
        from study_tracker import handle_heartbeat_transaction
        resp = handle_heartbeat_transaction(
            student_id=student.id,
            session_token=session_token.strip(),
            course_id=course_id.strip(),
            lecture_id=lecture_id.strip(),
            seq=seq,
            payload_hash=payload_hash.strip(),
            is_active=is_active,
            event_type=event_type,
            user_notice=str(user_notice)[:200] if user_notice else None
        )
        db.session.commit()
        return resp
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Heartbeat Route Error] Student {student.id}, token {session_token}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to process heartbeat due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


@app.route('/api/student/study-session/close', methods=['POST'])
@student_login_required
def close_study_session(student):
    """
    Terminates an active or displaced study session.
    Releases the clock lease if this session currently held it.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    session_token = data.get('session_token')
    if not isinstance(session_token, str) or not session_token.strip():
        return jsonify({
            'success': False,
            'message': 'session_token must be a non-empty string.',
            'code': 'INVALID_TOKEN'
        }), 400

    # CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    close_reason = data.get('close_reason') or 'USER_NAVIGATION'

    try:
        sess = db.session() if callable(db.session) else db.session
        tx = sess.begin_nested() if sess.in_transaction() else sess.begin()
        with tx:
            # 1. Primary Mutex: Lock clock first
            db.session.execute(text("""
                SELECT student_id FROM public.student_study_clocks
                WHERE student_id = :sid FOR UPDATE;
            """), {'sid': str(student.id)})

            now = db.session.execute(text("SELECT clock_timestamp();")).scalar()

            # 2. Update session to CLOSED
            res = db.session.execute(text("""
                UPDATE public.student_study_sessions
                SET status = 'CLOSED',
                    ended_at = :now,
                    close_reason = :reason
                WHERE session_token = :token AND student_id = :sid AND status != 'CLOSED'
                RETURNING id;
            """), {
                'token': session_token.strip(),
                'sid': str(student.id),
                'now': now,
                'reason': str(close_reason)[:50]
            }).fetchone()

            if res:
                sess_id = res[0]
                # 3. If session held the clock lease, release it
                db.session.execute(text("""
                    UPDATE public.student_study_clocks
                    SET active_session_id = NULL,
                        active_lecture_id = NULL,
                        lease_expires_at = :now - interval '1 second',
                        updated_at = :now
                    WHERE student_id = :sid AND active_session_id = :sess_id;
                """), {
                    'sid': str(student.id),
                    'sess_id': str(sess_id),
                    'now': now
                })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Study session closed successfully.'
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Close Session Error] Student {student.id}, token {session_token}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to close study session due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


@app.route('/api/student/dashboard-summary', methods=['GET'])
@student_login_required
def get_student_dashboard_summary(student):
    """
    Returns authenticated student's learning dashboard summary and automatically
    enrolls the student into their target exam preparation course if not already enrolled.
    """
    try:
        lagos_tz = ZoneInfo('Africa/Lagos')
        lagos_today = datetime.now(lagos_tz).date()

        # 1. Automatic Examination-Course Enrollment (idempotent, concurrency-safe)
        target_course_id = resolve_exam_course(student.intended_exam)
        target_course = Course.query.filter_by(id=target_course_id, is_published=True).first()

        if target_course:
            enroll_sql = text("""
                INSERT INTO public.student_enrollments (
                    id, student_id, course_id, enrolled_at, is_pinned, completed_at, last_accessed_at
                )
                VALUES (
                    gen_random_uuid(), :student_id, :course_id, CURRENT_TIMESTAMP, TRUE, NULL, CURRENT_TIMESTAMP
                )
                ON CONFLICT (student_id, course_id) DO NOTHING;
            """)
            db.session.execute(enroll_sql, {
                'student_id': str(student.id),
                'course_id': target_course.id
            })
            db.session.commit()

        # 2. Student Profile Section
        student_profile = {
            'full_name': student.full_name,
            'email': student.email,
            'education_level': student.education_level,
            'intended_exam': student.intended_exam
        }

        # 3. Learning Statistics Section
        # IMPORTANT XP RULE: total_xp = SUM(student_daily_activity.xp_earned) ONLY.
        total_xp = db.session.query(
            func.coalesce(func.sum(StudentDailyActivity.xp_earned), 0)
        ).filter(
            StudentDailyActivity.student_id == student.id
        ).scalar() or 0

        total_questions_practiced = db.session.query(
            func.coalesce(func.sum(StudentDailyActivity.questions_practiced), 0)
        ).filter(
            StudentDailyActivity.student_id == student.id
        ).scalar() or 0

        total_lessons_completed = db.session.query(
            func.count(StudentLessonProgress.id)
        ).join(
            Lecture, StudentLessonProgress.lecture_id == Lecture.id
        ).filter(
            StudentLessonProgress.student_id == student.id,
            StudentLessonProgress.is_completed == True,
            Lecture.is_published == True
        ).scalar() or 0

        # 4. Learning Streak Section (Africa/Lagos calendar date)
        active_rows = db.session.query(
            StudentDailyActivity.activity_date
        ).filter(
            StudentDailyActivity.student_id == student.id,
            (StudentDailyActivity.xp_earned > 0) |
            (StudentDailyActivity.lessons_completed > 0) |
            (StudentDailyActivity.questions_practiced > 0) |
            (StudentDailyActivity.seconds_spent > 0)
        ).all()

        active_dates = {r[0] for r in active_rows}
        lagos_yesterday = lagos_today - timedelta(days=1)

        current_streak = 0
        if lagos_today in active_dates:
            current_streak = 1
            chk = lagos_today - timedelta(days=1)
            while chk in active_dates:
                current_streak += 1
                chk = chk - timedelta(days=1)
        elif lagos_yesterday in active_dates:
            current_streak = 1
            chk = lagos_yesterday - timedelta(days=1)
            while chk in active_dates:
                current_streak += 1
                chk = chk - timedelta(days=1)
        else:
            current_streak = 0

        sorted_dates = sorted(active_dates)
        longest_streak = 0
        if sorted_dates:
            running_streak = 1
            max_streak = 1
            for i in range(1, len(sorted_dates)):
                if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                    running_streak += 1
                    if running_streak > max_streak:
                        max_streak = running_streak
                elif sorted_dates[i] > sorted_dates[i - 1] + timedelta(days=1):
                    running_streak = 1
            longest_streak = max(max_streak, current_streak)

        # 5. Weekly Activity Section (Current Lagos calendar week: Monday to Sunday)
        monday = lagos_today - timedelta(days=lagos_today.weekday())
        sunday = monday + timedelta(days=6)

        weekly_rows = db.session.query(
            StudentDailyActivity
        ).filter(
            StudentDailyActivity.student_id == student.id,
            StudentDailyActivity.activity_date >= monday,
            StudentDailyActivity.activity_date <= sunday
        ).all()

        weekly_map = {row.activity_date: row for row in weekly_rows}

        weekly_activity = []
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(7):
            day_date = monday + timedelta(days=i)
            activity = weekly_map.get(day_date)
            if activity:
                xp = activity.xp_earned or 0
                lessons = activity.lessons_completed or 0
                questions = activity.questions_practiced or 0
                sec = activity.seconds_spent or 0
                mins = activity.minutes_spent or (sec // 60)
                is_active = (xp > 0 or lessons > 0 or questions > 0 or sec > 0)
            else:
                xp = 0
                lessons = 0
                questions = 0
                sec = 0
                mins = 0
                is_active = False

            weekly_activity.append({
                'date': day_date.isoformat(),
                'day_name': day_names[i],
                'xp_earned': xp,
                'lessons_completed': lessons,
                'questions_practiced': questions,
                'seconds_spent': sec,
                'minutes_spent': mins,
                'is_active': is_active
            })

        # 6. Course Progress Section (Enrolled published courses)
        enrollment_rows = db.session.query(
            StudentEnrollment, Course
        ).join(
            Course, StudentEnrollment.course_id == Course.id
        ).filter(
            StudentEnrollment.student_id == student.id,
            Course.is_published == True
        ).order_by(
            StudentEnrollment.enrolled_at.asc()
        ).all()

        enrolled_courses = []
        for enrollment, course in enrollment_rows:
            total_published_lectures = db.session.query(func.count(Lecture.id)).filter(
                Lecture.course_id == course.id,
                Lecture.is_published == True
            ).scalar() or 0

            completed_lectures = db.session.query(func.count(StudentLessonProgress.id)).join(
                Lecture, StudentLessonProgress.lecture_id == Lecture.id
            ).filter(
                StudentLessonProgress.student_id == student.id,
                StudentLessonProgress.course_id == course.id,
                StudentLessonProgress.is_completed == True,
                Lecture.is_published == True
            ).scalar() or 0

            if total_published_lectures > 0:
                progress_percentage = int(round((completed_lectures / total_published_lectures) * 100))
            else:
                progress_percentage = 0

            enrolled_courses.append({
                'course_id': course.id,
                'title': course.title,
                'description': course.description or '',
                'total_published_lectures': total_published_lectures,
                'completed_lectures': completed_lectures,
                'progress_percentage': progress_percentage,
                'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
                'is_pinned': enrollment.is_pinned
            })

        # 7. Recently Accessed Lessons (Max 5, Published Lectures Only, Genuine Openings view_count > 0)
        recent_progress = db.session.query(
            StudentLessonProgress, Lecture, Course
        ).join(
            Lecture, StudentLessonProgress.lecture_id == Lecture.id
        ).join(
            Course, StudentLessonProgress.course_id == Course.id
        ).filter(
            StudentLessonProgress.student_id == student.id,
            StudentLessonProgress.view_count > 0,
            Lecture.is_published == True,
            Course.is_published == True
        ).order_by(
            StudentLessonProgress.last_accessed_at.desc()
        ).limit(5).all()

        recent_lessons = [
            {
                'course_id': course.id,
                'course_title': course.title,
                'lecture_id': lecture.id,
                'lecture_title': lecture.title,
                'last_accessed_at': prog.last_accessed_at.isoformat() if prog.last_accessed_at else None,
                'is_completed': prog.is_completed,
                'last_position_seconds': prog.last_position_seconds,
                'total_duration_seconds': prog.total_duration_seconds,
                'view_count': prog.view_count
            }
            for prog, lecture, course in recent_progress
        ]

        # 8. Latest Diagnostic Assessment
        latest_diag = StudentDiagnosticHistory.query.filter_by(
            student_id=student.id
        ).order_by(
            StudentDiagnosticHistory.attempt_number.desc()
        ).first()

        if latest_diag:
            diagnostic_data = {
                'subject': latest_diag.subject,
                'score': latest_diag.score,
                'max_score': latest_diag.max_score,
                'percentage': latest_diag.percentage,
                'topic_breakdown': latest_diag.topic_breakdown if isinstance(latest_diag.topic_breakdown, dict) else {},
                'recommendations': latest_diag.recommendations if isinstance(latest_diag.recommendations, list) else [],
                'attempt_number': latest_diag.attempt_number,
                'submitted_at': latest_diag.completed_at.isoformat() if latest_diag.completed_at else None
            }
        else:
            diagnostic_data = None

        # 9. Real Study Time Accounting (Phase 6.4.3)
        today_activity = weekly_map.get(lagos_today)
        today_seconds = (today_activity.seconds_spent or 0) if today_activity else 0
        today_minutes = (today_activity.minutes_spent or (today_seconds // 60)) if today_activity else 0

        weekly_seconds = sum((row.seconds_spent or 0) for row in weekly_rows)
        weekly_minutes = sum((row.minutes_spent or ((row.seconds_spent or 0) // 60)) for row in weekly_rows)

        def _format_study_duration(seconds):
            if not seconds or seconds <= 0:
                return "0m"
            h = seconds // 3600
            m = (seconds % 3600) // 60
            if h > 0:
                return f"{h}h {m}m"
            return f"{m}m"

        study_time = {
            'today_seconds': today_seconds,
            'today_minutes': today_minutes,
            'today_formatted': _format_study_duration(today_seconds),
            'weekly_seconds': weekly_seconds,
            'weekly_minutes': weekly_minutes,
            'weekly_formatted': _format_study_duration(weekly_seconds),
            'weekly_target_hours': 10,
            'tracking_status': 'active'
        }

        # 10. Milestones & Achievements (Phase 6.5.4)
        from achievement_service import get_student_achievements
        achievements_data = get_student_achievements(db.session, student.id)

        # Backward-compatible milestones list
        milestones = []
        for a in achievements_data['achievements']:
            if a['is_earned']:
                m_id = 'first_lesson_completed' if a['id'] == 'first_lesson' else a['id']
                milestones.append({
                    'id': m_id,
                    'title': a['title'],
                    'description': a['description'],
                    'achieved_at': a['earned_at']
                })

        # Phase 6.5.2: Learning Analytics & Personalized Recommendations
        from analytics_engine import (
            get_student_topic_mastery,
            get_student_study_habits,
            get_student_diagnostic_analytics,
            get_student_recommendations
        )

        topic_mastery = get_student_topic_mastery(db.session, student.id)
        study_habits = get_student_study_habits(db.session, student.id)
        diag_analytics = get_student_diagnostic_analytics(db.session, student.id)
        recommendations = get_student_recommendations(db.session, student.id, student.intended_exam)

        analytics_payload = {
            'topic_mastery': topic_mastery,
            'study_habits': study_habits
        }

        return jsonify({
            'success': True,
            'student': student_profile,
            'stats': {
                'total_xp': total_xp,
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'total_lessons_completed': total_lessons_completed,
                'total_questions_practiced': total_questions_practiced,
                'weekly_activity': weekly_activity,
                'weekly_activity_start': monday.isoformat(),
                'weekly_activity_end': sunday.isoformat()
            },
            'enrolled_courses': enrolled_courses,
            'recent_lessons': recent_lessons,
            'latest_diagnostic': diagnostic_data,
            'study_time': study_time,
            'milestones': milestones,
            'achievements': achievements_data,
            'analytics': analytics_payload,
            'recommendations': recommendations,
            'diagnostic_progress': diag_analytics
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Dashboard Summary Error] Failed to generate dashboard summary for student {student.id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve student dashboard summary due to a server error.',
            'code': 'DASHBOARD_RETRIEVAL_ERROR'
        }), 500


@app.route('/api/student/analytics/activity-history', methods=['GET'])
@student_login_required
def get_student_activity_history(student):
    """
    Phase 6.5.2: Returns dense chronological daily activity history over requested number of days (default 30, max 90).
    Enforces @student_login_required and derives student identity exclusively from authenticated session.
    """
    try:
        raw_days = request.args.get('days', default='30')
        try:
            days = int(raw_days)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Parameter "days" must be an integer between 1 and 90.',
                'code': 'INVALID_DAYS_PARAM'
            }), 400

        if days < 1 or days > 90:
            return jsonify({
                'success': False,
                'message': 'Parameter "days" must be between 1 and 90.',
                'code': 'DAYS_OUT_OF_RANGE'
            }), 400

        from analytics_engine import get_student_activity_history_data
        data = get_student_activity_history_data(db.session, student.id, days=days)
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"[Activity History Error] Failed for student {student.id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve student activity history due to a server error.',
            'code': 'ACTIVITY_HISTORY_ERROR'
        }), 500


# ============================================================================
# PHASE 6.5.4: STUDENT ENGAGEMENT AND ACHIEVEMENT API
# ============================================================================

@app.route('/api/student/achievements', methods=['GET'])
@student_login_required
def get_student_achievements_route(student):
    """
    Phase 6.5.4: Returns authenticated student's engagement milestones and achievements
    across Learning Progress, Study Consistency, Study Commitment, and Diagnostic Improvement.
    Derives student identity strictly from authenticated session.
    """
    try:
        from achievement_service import get_student_achievements
        data = get_student_achievements(db.session, student.id)
        return jsonify({
            'success': True,
            'summary': data['summary'],
            'categories': data['categories'],
            'achievements': data['achievements'],
            'recent_unlocked': data['recent_unlocked']
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Achievements API Error] Failed for student {student.id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve student achievements due to a server error.',
            'code': 'ACHIEVEMENTS_RETRIEVAL_ERROR'
        }), 500



# ============================================================================
# PHASE 6.3.2 STAGE 5: STUDENT PROFILE UPDATE API
# ============================================================================

VALID_EDUCATION_LEVELS = {
    'JSS 1', 'JSS 2', 'JSS 3', 'SS1', 'SS2', 'SS3', 'JAMB/UTME', 'Other supported programmes'
}

VALID_INTENDED_EXAMS = {
    'WASSCE', 'WAEC', 'NECO', 'GCE', 'JAMB', 'UTME', 'JAMB/UTME', 'Post-UTME', 'POST-UTME',
    'Senior Secondary', 'School Examination', 'Not yet decided'
}

PERMITTED_PROFILE_FIELDS = {'full_name', 'education_level', 'intended_exam', 'phone', 'avatar_url', 'csrf_token'}
FORBIDDEN_PROFILE_FIELDS = {
    'id', 'student_id', 'auth_user_id', 'email', 'password', 'password_hash',
    'role', 'is_active', 'session_version', 'last_login', 'created_at', 'updated_at'
}


@app.route('/api/student/profile', methods=['PUT'])
@student_login_required
def update_student_profile(student):
    """
    Updates permitted profile information for the authenticated student.
    Enforces strict field whitelisting, CSRF validation, and input sanitization.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid request payload. Expected a JSON object.',
            'code': 'INVALID_PAYLOAD'
        }), 400

    # 1. CSRF Token Verification
    session_csrf = session.get('csrf_token')
    req_csrf = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or data.get('csrf_token')
    if not session_csrf or not req_csrf or not secrets.compare_digest(str(req_csrf), str(session_csrf)):
        return jsonify({
            'success': False,
            'message': 'Missing or invalid CSRF token. Please refresh and try again.',
            'code': 'CSRF_FAILED'
        }), 400

    # 2. Check for forbidden or unknown fields
    for key in data.keys():
        if key in FORBIDDEN_PROFILE_FIELDS:
            return jsonify({
                'success': False,
                'message': f'Cannot modify protected account field: "{key}".',
                'code': 'PROTECTED_FIELD'
            }), 400
        if key not in PERMITTED_PROFILE_FIELDS:
            return jsonify({
                'success': False,
                'message': f'Unknown or unsupported profile field: "{key}".',
                'code': 'UNKNOWN_FIELD'
            }), 400

    # Filter down to editable fields provided
    editable_keys = [k for k in data.keys() if k != 'csrf_token']
    if not editable_keys:
        return jsonify({
            'success': False,
            'message': 'No editable profile fields provided for update.',
            'code': 'NO_FIELDS_PROVIDED'
        }), 400

    # 3. Field Validations
    # full_name
    if 'full_name' in data:
        val = data.get('full_name')
        if not isinstance(val, str):
            return jsonify({
                'success': False,
                'message': 'full_name must be a string.',
                'code': 'INVALID_FULL_NAME'
            }), 400
        cleaned_name = val.strip()
        if len(cleaned_name) < 2 or len(cleaned_name) > 150:
            return jsonify({
                'success': False,
                'message': 'full_name must be between 2 and 150 characters.',
                'code': 'INVALID_FULL_NAME'
            }), 400
        student.full_name = cleaned_name
        session['full_name'] = cleaned_name

    # education_level
    if 'education_level' in data:
        val = data.get('education_level')
        if not isinstance(val, str):
            return jsonify({
                'success': False,
                'message': 'education_level must be a string.',
                'code': 'INVALID_EDUCATION_LEVEL'
            }), 400
        cleaned_level = val.strip()
        if cleaned_level not in VALID_EDUCATION_LEVELS:
            return jsonify({
                'success': False,
                'message': f'Invalid education_level. Supported values: {sorted(list(VALID_EDUCATION_LEVELS))}.',
                'code': 'INVALID_EDUCATION_LEVEL'
            }), 400
        student.education_level = cleaned_level

    # intended_exam
    if 'intended_exam' in data:
        val = data.get('intended_exam')
        if not isinstance(val, str):
            return jsonify({
                'success': False,
                'message': 'intended_exam must be a string.',
                'code': 'INVALID_INTENDED_EXAM'
            }), 400
        cleaned_exam = val.strip()
        # Case-insensitive normalization against VALID_INTENDED_EXAMS
        normalized_exam = None
        for valid_e in VALID_INTENDED_EXAMS:
            if valid_e.upper() == cleaned_exam.upper():
                normalized_exam = valid_e
                break
        if not normalized_exam:
            return jsonify({
                'success': False,
                'message': f'Invalid intended_exam. Supported values: {sorted(list(VALID_INTENDED_EXAMS))}.',
                'code': 'INVALID_INTENDED_EXAM'
            }), 400
        student.intended_exam = normalized_exam

    # phone
    if 'phone' in data:
        val = data.get('phone')
        if val is None or (isinstance(val, str) and not val.strip()):
            student.phone = None
        elif isinstance(val, str):
            cleaned_phone = val.strip()
            if len(cleaned_phone) > 30:
                return jsonify({
                    'success': False,
                    'message': 'phone cannot exceed 30 characters.',
                    'code': 'INVALID_PHONE'
                }), 400
            if not re.match(r'^\+?[0-9\s\-\(\)]{7,30}$', cleaned_phone):
                return jsonify({
                    'success': False,
                    'message': 'phone must contain a valid phone number (digits, spaces, dashes, parentheses, optional leading +).',
                    'code': 'INVALID_PHONE'
                }), 400
            student.phone = cleaned_phone
        else:
            return jsonify({
                'success': False,
                'message': 'phone must be a string or null.',
                'code': 'INVALID_PHONE'
            }), 400

    # avatar_url
    if 'avatar_url' in data:
        val = data.get('avatar_url')
        if val is None or (isinstance(val, str) and not val.strip()):
            student.avatar_url = None
        elif isinstance(val, str):
            cleaned_url = val.strip()
            if len(cleaned_url) > 500:
                return jsonify({
                    'success': False,
                    'message': 'avatar_url cannot exceed 500 characters.',
                    'code': 'INVALID_AVATAR_URL'
                }), 400
            lower_url = cleaned_url.lower()
            if any(lower_url.startswith(scheme) for scheme in ['javascript:', 'data:', 'vbscript:', 'file:']):
                return jsonify({
                    'success': False,
                    'message': 'avatar_url contains an unsafe or unsupported URL scheme.',
                    'code': 'UNSAFE_AVATAR_URL'
                }), 400
            if not (lower_url.startswith('http://') or lower_url.startswith('https://') or lower_url.startswith('/')):
                return jsonify({
                    'success': False,
                    'message': 'avatar_url must start with http://, https://, or a valid relative path starting with /.',
                    'code': 'INVALID_AVATAR_URL'
                }), 400
            student.avatar_url = cleaned_url
        else:
            return jsonify({
                'success': False,
                'message': 'avatar_url must be a string or null.',
                'code': 'INVALID_AVATAR_URL'
            }), 400

    # 4. Commit update transaction
    try:
        student.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        updated_profile = {
            'full_name': student.full_name,
            'email': student.email,
            'education_level': student.education_level,
            'intended_exam': student.intended_exam,
            'phone': student.phone or '',
            'avatar_url': student.avatar_url or ''
        }

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully.',
            'student': updated_profile
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Profile Update Error] Failed to update profile for student {student.id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update student profile due to a database error.',
            'code': 'PERSISTENCE_ERROR'
        }), 500


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
