import os
import json
import logging
import urllib.request
from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Ensure .env is explicitly loaded from project root
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

# Set up basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-key-12345')

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
db_url = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "instance", "math_portal.db")}')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    avatar = db.Column(db.String(10), nullable=True)
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
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(20), default='📐')
    badge = db.Column(db.String(50), default='Comprehensive')
    instructor = db.Column(db.String(100), default='Mr. Isaac Olusola')
    duration_weeks = db.Column(db.Integer, default=6)
    display_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'category': self.category,
            'description': self.description or '',
            'icon': self.icon or '📐',
            'badge': self.badge or 'Comprehensive',
            'instructor': self.instructor or 'Mr. Isaac Olusola',
            'duration_weeks': self.duration_weeks,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class Lecture(db.Model):
    __tablename__ = 'lectures'
    id = db.Column(db.String(100), primary_key=True)
    course_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.String(50), default='30 mins')
    order_index = db.Column(db.Integer, default=1)
    notes_url = db.Column(db.String(500), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description or '',
            'video_url': self.video_url,
            'duration': self.duration or '30 mins',
            'order_index': self.order_index,
            'notes_url': self.notes_url or '',
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

class VaultResource(db.Model):
    __tablename__ = 'vault_resources'
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
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
            'file_url': self.file_url,
            'file_size': self.file_size or '1.5 MB',
            'badge': self.badge or 'PDF',
            'description': self.description or '',
            'downloads_count': self.downloads_count,
            'created_at': self.created_at.isoformat() if self.created_at else ''
        }

# ============================================================================
# 2. PAGE ROUTES
# ============================================================================

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/index.html')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/courses.html')
def courses():
    return send_from_directory(BASE_DIR, 'courses.html')

@app.route('/cbt.html')
def cbt_page():
    return send_from_directory(BASE_DIR, 'cbt.html')

@app.route('/cbt')
def cbt_alias():
    return send_from_directory(BASE_DIR, 'cbt.html')

@app.route('/tutoring.html')
def tutoring():
    return send_from_directory(BASE_DIR, 'tutoring.html')

@app.route('/vault.html')
def vault():
    return send_from_directory(BASE_DIR, 'vault.html')

@app.route('/course-view.html')
def course_view():
    return send_from_directory(BASE_DIR, 'course-view.html')

@app.route('/contact.html')
def contact_page():
    return send_from_directory(BASE_DIR, 'contact.html')

@app.route('/people.html')
def people_page():
    return send_from_directory(BASE_DIR, 'people.html')

@app.route('/admin.html')
def admin_page():
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/admin')
def admin_alias():
    return send_from_directory(BASE_DIR, 'admin.html')

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
        course = Course(
            id=cid,
            title=data.get('title'),
            slug=slug,
            category=data.get('category', 'JAMB / Post-JAMB'),
            description=data.get('description', ''),
            icon=data.get('icon', '📐'),
            badge=data.get('badge', 'Popular'),
            instructor=data.get('instructor', 'Mr. Isaac Olusola'),
            duration_weeks=int(data.get('duration_weeks') or 6),
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
        lec = Lecture(
            id=lid,
            course_id=data.get('course_id') or data.get('courseId'),
            title=data.get('title'),
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
            category=data.get('category', 'JAMB UTME'),
            file_url=data.get('file_url') or data.get('fileUrl', '#'),
            file_size=data.get('file_size', '1.5 MB'),
            badge=data.get('badge', 'PDF'),
            description=data.get('description', '')
        )
        db.session.add(res)
        db.session.commit()
        return jsonify({'success': True, 'resource': res.to_dict()})

    resources = VaultResource.query.order_by(VaultResource.created_at.desc()).all()
    return jsonify([r.to_dict() for r in resources])

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
        return jsonify({'success': True, 'message': 'Your inquiry has been successfully submitted! We will reach out shortly.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Server database error: {str(e)}'}), 500

# ============================================================================
# 4. STARTUP DATABASE INITIALIZATION & DEFAULT SEEDING
# ============================================================================
with app.app_context():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
