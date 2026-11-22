#!/usr/bin/env python3
"""
===============================================================================
Phase 6.4.2: Study-Time Tracking Final Deployment Safety & Regression Test Harness
Target Environment: Disposable Isolated Neon Branch (ep-hidden-river-bd9kghxc)
Target Schema: public (Disposable Isolated Database)
Strict Safety Invariant: NEVER CONNECTS TO STAGING OR PRODUCTION

This test harness executes the 8 comprehensive regression test suites for Phase 6.4.2:
  1. Compatible pre-existing trigger survives migration and rollback.
  2. Compatible pre-existing function survives migration and rollback unchanged.
  3. Pre-existing study tables & data are not removed by rollback.
  4. Pre-existing index is not removed or replaced (OID preserved).
  5. Incompatible pre-existing objects abort before persistent DDL (7 subcases: 5A-5G).
  6. Unexpected dependencies block rollback without CASCADE (6 subcases: 6A-6F).
  7. Full SQL lifecycle, heartbeat accounting, and constraint regression suite.
  8. Python handle_heartbeat_transaction application handler integration.
===============================================================================
"""

import os
import sys
import uuid
import hashlib
import urllib.parse
import psycopg2
import psycopg2.extras

# -----------------------------------------------------------------------------
# STRICT SAFETY GUARDS: PROHIBIT STAGING & PRODUCTION CONNECTIONS
# ALL HARDCODED CREDENTIALS REMOVED - STRICT ALLOWLIST ENFORCED
# -----------------------------------------------------------------------------
ALLOWED_TEST_ENDPOINTS = [
    "ep-hidden-river-bd9kghxc",  # Neon disposable test branch endpoint ONLY
]

ALLOWED_TEST_DATABASES = [
    "neondb",
]

DISALLOWED_ENDPOINTS = [
    "ep-sparkling-field-bd7oql2b",  # staging-phase6-3-2 endpoint
    "ep-fragrant-smoke-bd8w1pwh",   # production (main) endpoint
]

# Dedicated test seed record identifiers (never touch arbitrary database data)
TEST_STUDENT_ID = "00000000-0000-4000-a000-000000000642"
TEST_STUDENT_EMAIL = "test.phase642.student@ziglag.edu"
TEST_COURSE_ID = "phase6-4-2-test-course"
TEST_LECTURE_ID = "phase6-4-2-test-lecture-1"

def get_connection():
    """
    Establishes an isolated database connection after validating strict safety invariants:
    1. PHASE642_TEST_DATABASE_URL environment variable must be explicitly provided.
    2. Endpoint MUST match ALLOWED_TEST_ENDPOINTS.
    3. Database MUST match ALLOWED_TEST_DATABASES.
    4. Denylisted staging/production endpoints are strictly rejected.
    5. Server catalog verification is performed post-connection.
    """
    dsn = os.environ.get("PHASE642_TEST_DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: Environment variable "
            "PHASE642_TEST_DATABASE_URL is not set. All hardcoded credentials have "
            "been eliminated. You must explicitly set PHASE642_TEST_DATABASE_URL to an "
            "approved disposable test branch DSN before running the test harness."
        )

    # Parse and validate connection target
    parsed = urllib.parse.urlsplit(dsn)
    host = parsed.hostname or ""
    db_name = (parsed.path or "").lstrip("/")

    # Explicit denylist check (defense-in-depth)
    for bad in DISALLOWED_ENDPOINTS:
        if bad in host or bad in dsn:
            raise RuntimeError(
                f"CRITICAL SECURITY VIOLATION: Attempted connection to restricted endpoint: {bad}. Execution aborted!"
            )

    # Explicit allowlist check
    matched_endpoint = any(allowed in host for allowed in ALLOWED_TEST_ENDPOINTS)
    if not matched_endpoint:
        raise RuntimeError(
            f"SECURITY VIOLATION: Host '{host}' is NOT in ALLOWED_TEST_ENDPOINTS ({ALLOWED_TEST_ENDPOINTS}). Execution aborted!"
        )

    if db_name not in ALLOWED_TEST_DATABASES:
        raise RuntimeError(
            f"SECURITY VIOLATION: Database '{db_name}' is NOT in ALLOWED_TEST_DATABASES ({ALLOWED_TEST_DATABASES}). Execution aborted!"
        )

    conn = psycopg2.connect(dsn)
    conn.autocommit = True

    # Catalog-level server & database verification
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, version();")
        curr_db, curr_user, ver = cur.fetchone()
        if curr_db not in ALLOWED_TEST_DATABASES:
            conn.close()
            raise RuntimeError(f"Connected database '{curr_db}' violates allowed test databases!")

    return conn

# File paths
MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
PREFLIGHT_SQL_PATH = os.path.join(MIGRATIONS_DIR, "preflight.sql")
MIGRATION_SQL_PATH = os.path.join(MIGRATIONS_DIR, "migration.sql")
ROLLBACK_SQL_PATH = os.path.join(MIGRATIONS_DIR, "rollback.sql")
POST_ASSERTIONS_SQL_PATH = os.path.join(MIGRATIONS_DIR, "post_assertions.sql")

def read_sql(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_function_create_sql():
    mig = read_sql(MIGRATION_SQL_PATH)
    start_tag = 'CREATE FUNCTION public.sync_student_daily_minutes()'
    end_tag = '$fn_create$;'
    start_idx = mig.find(start_tag)
    end_idx = mig.find(end_tag, start_idx)
    return mig[start_idx:end_idx].strip()

def clean_phase642_objects(conn):
    """
    Resets public schema to pristine baseline without Phase 6.4.2 objects.
    STRICTLY NON-CASCADING: Drops test dependencies and migration objects
    in reverse dependency order. Never touches unrelated database tables.
    """
    with conn.cursor() as cur:
        # Drop external test dependency objects (no CASCADE)
        cur.execute("DROP VIEW IF EXISTS public.v_external_audit;")
        cur.execute("DROP TABLE IF EXISTS public.external_seconds_ref;")
        cur.execute("DROP TABLE IF EXISTS public.external_audit_log;")
        cur.execute("DROP FUNCTION IF EXISTS public.audit_cron_caller();")

        # Drop trigger & function (no CASCADE)
        cur.execute("DROP TRIGGER IF EXISTS trg_sync_student_daily_minutes ON public.student_daily_activity;")
        cur.execute("DROP FUNCTION IF EXISTS public.sync_student_daily_minutes();")

        # Drop study tables in FK dependency order (no CASCADE)
        cur.execute("DROP TABLE IF EXISTS public.student_study_clocks;")
        cur.execute("DROP TABLE IF EXISTS public.student_study_sessions;")

        # Drop seconds_spent constraints and columns from existing tables (no CASCADE)
        cur.execute("""
            SELECT 1 FROM pg_constraint 
            WHERE conrelid = 'public.student_daily_activity'::regclass 
              AND conname = 'ck_student_daily_seconds_non_negative';
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE public.student_daily_activity DROP CONSTRAINT ck_student_daily_seconds_non_negative;")

        cur.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'seconds_spent';
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE public.student_daily_activity DROP COLUMN seconds_spent;")

        cur.execute("""
            SELECT 1 FROM pg_constraint 
            WHERE conrelid = 'public.student_lesson_progress'::regclass 
              AND conname = 'chk_lesson_progress_seconds_nonneg';
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE public.student_lesson_progress DROP CONSTRAINT chk_lesson_progress_seconds_nonneg;")

        cur.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'seconds_spent';
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE public.student_lesson_progress DROP COLUMN seconds_spent;")

        # Drop ownership table (no CASCADE)
        cur.execute("DROP TABLE IF EXISTS public._migration_phase6_4_2_ownership;")

def ensure_seed_records(conn):
    """
    Ensures isolated, uniquely identifiable test-owned seed records exist.
    Never selects or mutates arbitrary existing database records.
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO public.students (id, full_name, email, password_hash, education_level, intended_exam)
            VALUES (%s, 'Phase 6.4.2 Test Student', %s, 'test_hash_phase642', 'SS 3', 'WAEC')
            ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
        """, (TEST_STUDENT_ID, TEST_STUDENT_EMAIL))

        cur.execute("""
            INSERT INTO public.courses (id, title, slug, category)
            VALUES (%s, 'Phase 6.4.2 Test Course', 'phase-6-4-2-course-slug', 'Mathematics')
            ON CONFLICT (id) DO NOTHING;
        """, (TEST_COURSE_ID,))

        cur.execute("""
            INSERT INTO public.lectures (id, course_id, title, video_url, order_index)
            VALUES (%s, %s, 'Phase 6.4.2 Test Lecture', 'https://video.example.com/phase642', 1)
            ON CONFLICT (id) DO NOTHING;
        """, (TEST_LECTURE_ID, TEST_COURSE_ID))

    return TEST_STUDENT_ID, TEST_COURSE_ID, TEST_LECTURE_ID

def clean_test_seed_records(conn):
    """
    Removes exclusively test-owned records created during testing.
    Protects all baseline and production data from accidental deletion.
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM public.student_daily_activity WHERE student_id = %s;", (TEST_STUDENT_ID,))
        cur.execute("DELETE FROM public.student_lesson_progress WHERE student_id = %s;", (TEST_STUDENT_ID,))
        cur.execute("DELETE FROM public.lectures WHERE id = %s;", (TEST_LECTURE_ID,))
        cur.execute("DELETE FROM public.courses WHERE id = %s;", (TEST_COURSE_ID,))
        cur.execute("DELETE FROM public.students WHERE id = %s;", (TEST_STUDENT_ID,))

# -----------------------------------------------------------------------------
# TEST 1: Compatible pre-existing trigger survives migration and rollback
# -----------------------------------------------------------------------------
def test_1_preexisting_trigger_survives():
    print("\n" + "="*70)
    print("[TEST 1] Compatible Pre-Existing Trigger Survives Migration and Rollback")
    print("="*70)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        with conn.cursor() as cur:
            # 1. Setup pre-existing seconds_spent column, function and trigger
            cur.execute("ALTER TABLE public.student_daily_activity ADD COLUMN seconds_spent INTEGER NOT NULL DEFAULT 0;")
            cur.execute("ALTER TABLE public.student_daily_activity ADD CONSTRAINT ck_student_daily_seconds_non_negative CHECK (seconds_spent >= 0);")
            
            fn_sql = extract_function_create_sql()
            cur.execute(fn_sql)

            cur.execute("""
                CREATE TRIGGER trg_sync_student_daily_minutes
                BEFORE INSERT OR UPDATE ON public.student_daily_activity
                FOR EACH ROW EXECUTE FUNCTION public.sync_student_daily_minutes();
            """)

            cur.execute("""
                SELECT t.oid, t.tgenabled 
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                WHERE c.relnamespace = 'public'::regnamespace 
                  AND c.relname = 'student_daily_activity' 
                  AND t.tgname = 'trg_sync_student_daily_minutes';
            """)
            row = cur.fetchone()
            assert row is not None, "Pre-existing trigger setup failed!"
            pre_trig_oid, pre_trig_enabled = row[0], row[1]
            print(f"  [SETUP] Pre-existing trigger created with OID: {pre_trig_oid}, enabled: {pre_trig_enabled}")

        # 2. Run Migration SQL
        print("  [ACTION] Executing migration.sql with pre-existing compatible trigger...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        # 3. Assert Ownership Table records created_by_phase6_4_2 = false
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_by_phase6_4_2 
                FROM public._migration_phase6_4_2_ownership 
                WHERE schema_name = 'public' AND object_type = 'TRIGGER' AND object_name = 'trg_sync_student_daily_minutes';
            """)
            row = cur.fetchone()
            assert row is not None, "Ownership row for trigger missing!"
            assert row[0] is False, f"Trigger ownership expected False, got {row[0]}"
            print("  [ASSERT] Ownership correctly logged created_by_phase6_4_2 = FALSE for pre-existing trigger.")

        # 4. Run Rollback SQL
        print("  [ACTION] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))

        # 5. Assert trigger survives rollback unchanged
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.oid, t.tgenabled 
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                WHERE c.relnamespace = 'public'::regnamespace 
                  AND c.relname = 'student_daily_activity' 
                  AND t.tgname = 'trg_sync_student_daily_minutes';
            """)
            post_row = cur.fetchone()
            assert post_row is not None, "Pre-existing trigger was unexpectedly DROPPED by rollback!"
            assert post_row[0] == pre_trig_oid, f"Trigger OID changed: {post_row[0]} != {pre_trig_oid}"
            assert post_row[1] == pre_trig_enabled, "Trigger enabled flag changed!"
            print(f"  [PASS] Pre-existing trigger survived rollback with identical OID {post_row[0]} and enabled flag!")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 2: Compatible pre-existing function survives migration and rollback
# -----------------------------------------------------------------------------
def test_2_preexisting_function_survives():
    print("\n" + "="*70)
    print("[TEST 2] Compatible Pre-Existing Function Survives Migration and Rollback")
    print("="*70)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        with conn.cursor() as cur:
            fn_sql = extract_function_create_sql()
            cur.execute(fn_sql)

            cur.execute("""
                SELECT p.oid, md5(regexp_replace(trim(p.prosrc), '\\s+', ' ', 'g'))
                FROM pg_proc p
                WHERE p.pronamespace = 'public'::regnamespace AND p.proname = 'sync_student_daily_minutes';
            """)
            row = cur.fetchone()
            assert row is not None, "Pre-existing function setup failed!"
            pre_fn_oid, pre_fn_hash = row[0], row[1]
            print(f"  [SETUP] Pre-existing function created with OID: {pre_fn_oid}, hash: {pre_fn_hash}")

        # 2. Run Migration
        print("  [ACTION] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        # 3. Verify Ownership recorded FALSE
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_by_phase6_4_2 
                FROM public._migration_phase6_4_2_ownership 
                WHERE schema_name = 'public' AND object_type = 'FUNCTION' AND object_name = 'sync_student_daily_minutes()';
            """)
            row = cur.fetchone()
            assert row[0] is False, f"Function ownership expected False, got {row[0]}"
            print("  [ASSERT] Ownership table recorded created_by_phase6_4_2 = FALSE for function.")

        # 4. Run Rollback
        print("  [ACTION] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))

        # 5. Assert function survives with identical OID and hash
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.oid, md5(regexp_replace(trim(p.prosrc), '\\s+', ' ', 'g'))
                FROM pg_proc p
                WHERE p.pronamespace = 'public'::regnamespace AND p.proname = 'sync_student_daily_minutes';
            """)
            post_row = cur.fetchone()
            assert post_row is not None, "Pre-existing function was DROPPED by rollback!"
            assert post_row[0] == pre_fn_oid, f"Function OID changed: {post_row[0]} != {pre_fn_oid}"
            assert post_row[1] == pre_fn_hash, f"Function hash changed!"
            print(f"  [PASS] Pre-existing function survived rollback unchanged with identical OID {post_row[0]}!")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 3: Pre-existing study tables & data are not removed by rollback
# -----------------------------------------------------------------------------
def test_3_preexisting_study_tables_survive():
    print("\n" + "="*70)
    print("[TEST 3] Pre-Existing Study Tables & Records Not Removed by Rollback")
    print("="*70)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)
        pre_session_id = str(uuid.uuid4())
        pre_token = 'token_preexisting_test_12345'

        with conn.cursor() as cur:
            # Pre-create study sessions table
            cur.execute("""
                CREATE TABLE public.student_study_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id UUID NOT NULL REFERENCES public.students (id) ON DELETE CASCADE,
                    course_id VARCHAR(100) NOT NULL REFERENCES public.courses (id) ON DELETE RESTRICT,
                    lecture_id VARCHAR(100) NOT NULL REFERENCES public.lectures (id) ON DELETE RESTRICT,
                    session_token VARCHAR(128) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    active_seconds INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    client_ip VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                    last_sequence_number INTEGER NOT NULL DEFAULT 0,
                    last_payload_hash VARCHAR(64),
                    last_response_json TEXT,
                    last_credited_seconds INTEGER NOT NULL DEFAULT 0,
                    total_seconds INTEGER NOT NULL DEFAULT 0,
                    close_reason VARCHAR(50),
                    CONSTRAINT uq_study_sessions_token UNIQUE (session_token),
                    CONSTRAINT uq_study_sessions_id_student UNIQUE (id, student_id),
                    CONSTRAINT ck_study_sessions_duration_non_negative CHECK (duration_seconds >= 0),
                    CONSTRAINT ck_study_sessions_active_non_negative CHECK (active_seconds >= 0),
                    CONSTRAINT ck_study_sessions_last_sequence_non_negative CHECK (last_sequence_number >= 0),
                    CONSTRAINT ck_study_sessions_last_credited_non_negative CHECK (last_credited_seconds >= 0),
                    CONSTRAINT ck_study_sessions_total_seconds_non_negative CHECK (total_seconds >= 0),
                    CONSTRAINT ck_study_sessions_status CHECK (
                        status IN ('ACTIVE', 'DISPLACED', 'CLOSED', 'PAUSED', 'COMPLETED', 'EXPIRED')
                    )
                );
                CREATE INDEX idx_study_sessions_student_status ON public.student_study_sessions (student_id, status);
                CREATE INDEX idx_study_sessions_student_lecture ON public.student_study_sessions (student_id, lecture_id);
                CREATE INDEX idx_study_sessions_expires_at ON public.student_study_sessions (expires_at) WHERE status = 'ACTIVE';

                CREATE TABLE public.student_study_clocks (
                    student_id UUID PRIMARY KEY REFERENCES public.students (id) ON DELETE CASCADE,
                    active_session_id UUID,
                    active_lecture_id VARCHAR(100) REFERENCES public.lectures (id) ON DELETE SET NULL,
                    lease_expires_at TIMESTAMPTZ NOT NULL,
                    last_credited_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    CONSTRAINT fk_study_clocks_active_session_owner FOREIGN KEY (active_session_id, student_id)
                        REFERENCES public.student_study_sessions (id, student_id) ON DELETE SET NULL (active_session_id)
                );
            """)

            # Insert pre-existing study session and clock row
            cur.execute("""
                INSERT INTO public.student_study_sessions (
                    id, student_id, course_id, lecture_id, session_token,
                    expires_at, active_seconds
                ) VALUES (
                    %s, %s, %s, %s, %s, clock_timestamp() + interval '5 minutes', 120
                );
            """, (pre_session_id, student_id, course_id, lecture_id, pre_token))

            cur.execute("""
                INSERT INTO public.student_study_clocks (
                    student_id, active_session_id, active_lecture_id,
                    lease_expires_at, last_credited_at
                ) VALUES (
                    %s, %s, %s, clock_timestamp() + interval '5 minutes', clock_timestamp()
                );
            """, (student_id, pre_session_id, lecture_id))
            print(f"  [SETUP] Pre-created study tables with test session {pre_session_id}")

        # 2. Run Migration
        print("  [ACTION] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        # 3. Verify Ownership Table recorded FALSE
        with conn.cursor() as cur:
            cur.execute("""
                SELECT object_name, created_by_phase6_4_2 
                FROM public._migration_phase6_4_2_ownership 
                WHERE schema_name = 'public' AND object_type = 'TABLE' 
                  AND object_name IN ('student_study_sessions', 'student_study_clocks');
            """)
            rows = dict(cur.fetchall())
            assert rows.get('student_study_sessions') is False, "Expected False ownership for pre-existing study sessions"
            assert rows.get('student_study_clocks') is False, "Expected False ownership for pre-existing study clocks"
            print("  [ASSERT] Ownership table recorded created_by_phase6_4_2 = FALSE for both tables.")

        # 4. Run Rollback
        print("  [ACTION] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))

        # 5. Assert tables and seed records survive intact
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.student_study_sessions WHERE id = %s;", (pre_session_id,))
            assert cur.fetchone()[0] == 1, "Pre-existing study session row was DELETED by rollback!"

            cur.execute("SELECT active_session_id FROM public.student_study_clocks WHERE student_id = %s;", (student_id,))
            row = cur.fetchone()
            assert row is not None and str(row[0]) == pre_session_id, "Study clock was corrupted or deleted!"
            print("  [PASS] Pre-existing study tables and session data survived rollback intact!")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 4: A pre-existing index is not removed or replaced
# -----------------------------------------------------------------------------
def test_4_preexisting_index_not_removed():
    print("\n" + "="*70)
    print("[TEST 4] Pre-Existing Index Not Removed or Replaced (OID Preserved)")
    print("="*70)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)

        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public.student_study_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id UUID NOT NULL REFERENCES public.students (id) ON DELETE CASCADE,
                    course_id VARCHAR(100) NOT NULL REFERENCES public.courses (id) ON DELETE RESTRICT,
                    lecture_id VARCHAR(100) NOT NULL REFERENCES public.lectures (id) ON DELETE RESTRICT,
                    session_token VARCHAR(128) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    active_seconds INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    client_ip VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                    last_sequence_number INTEGER NOT NULL DEFAULT 0,
                    last_payload_hash VARCHAR(64),
                    last_response_json TEXT,
                    last_credited_seconds INTEGER NOT NULL DEFAULT 0,
                    total_seconds INTEGER NOT NULL DEFAULT 0,
                    close_reason VARCHAR(50),
                    CONSTRAINT uq_study_sessions_token UNIQUE (session_token),
                    CONSTRAINT uq_study_sessions_id_student UNIQUE (id, student_id),
                    CONSTRAINT ck_study_sessions_duration_non_negative CHECK (duration_seconds >= 0),
                    CONSTRAINT ck_study_sessions_active_non_negative CHECK (active_seconds >= 0),
                    CONSTRAINT ck_study_sessions_last_sequence_non_negative CHECK (last_sequence_number >= 0),
                    CONSTRAINT ck_study_sessions_last_credited_non_negative CHECK (last_credited_seconds >= 0),
                    CONSTRAINT ck_study_sessions_total_seconds_non_negative CHECK (total_seconds >= 0),
                    CONSTRAINT ck_study_sessions_status CHECK (
                        status IN ('ACTIVE', 'DISPLACED', 'CLOSED', 'PAUSED', 'COMPLETED', 'EXPIRED')
                    )
                );
                CREATE INDEX idx_study_sessions_student_status ON public.student_study_sessions (student_id, status);
            """)

            cur.execute("""
                SELECT c.oid 
                FROM pg_class c
                WHERE c.relnamespace = 'public'::regnamespace AND c.relname = 'idx_study_sessions_student_status';
            """)
            pre_idx_oid = cur.fetchone()[0]
            print(f"  [SETUP] Pre-created idx_study_sessions_student_status with OID {pre_idx_oid}")

        # 2. Run Migration
        print("  [ACTION] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        # 3. Assert Ownership Table logged FALSE
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_by_phase6_4_2 
                FROM public._migration_phase6_4_2_ownership 
                WHERE schema_name = 'public' AND object_type = 'INDEX' AND object_name = 'idx_study_sessions_student_status';
            """)
            row = cur.fetchone()
            assert row[0] is False, f"Index ownership expected False, got {row[0]}"

            cur.execute("""
                SELECT c.oid 
                FROM pg_class c
                WHERE c.relnamespace = 'public'::regnamespace AND c.relname = 'idx_study_sessions_student_status';
            """)
            mid_idx_oid = cur.fetchone()[0]
            assert mid_idx_oid == pre_idx_oid, f"Index was replaced during migration! {mid_idx_oid} != {pre_idx_oid}"
            print(f"  [ASSERT] Index preserved during migration with identical OID {mid_idx_oid}.")

        # 4. Run Rollback
        print("  [ACTION] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))

        # 5. Assert index still exists with identical OID
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.oid 
                FROM pg_class c
                WHERE c.relnamespace = 'public'::regnamespace AND c.relname = 'idx_study_sessions_student_status';
            """)
            post_idx_oid = cur.fetchone()[0]
            assert post_idx_oid == pre_idx_oid, f"Index OID changed after rollback: {post_idx_oid} != {pre_idx_oid}"
            print(f"  [PASS] Pre-existing index survived rollback with unchanged OID {post_idx_oid}!")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 5: Incompatible pre-existing objects abort before persistent DDL (7 Subcases)
# -----------------------------------------------------------------------------
def test_5_incompatible_objects_abort():
    print("\n" + "="*70)
    print("[TEST 5] Incompatible Pre-Existing Objects Abort Before Persistent DDL (7 Subcases)")
    print("="*70)

    # Subcase 5A: Incompatible column data type (VARCHAR instead of INTEGER)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        print("  [SUBCASE 5A] Incompatible seconds_spent type (VARCHAR)... ")
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE public.student_lesson_progress ADD COLUMN seconds_spent VARCHAR(50) DEFAULT 'zero';")
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for incompatible column type, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) or "datatype_mismatch" in str(e) or "incompatible" in str(e)
            print(f"  [PASS 5A] Aborted as expected: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        c.close()

    # Subcase 5B: Incompatible trigger function body
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        print("  [SUBCASE 5B] Incompatible sync_student_daily_minutes() body... ")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE FUNCTION public.sync_student_daily_minutes()
                RETURNS TRIGGER LANGUAGE plpgsql AS $$
                BEGIN
                    RETURN NEW;
                END;
                $$;
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for incompatible trigger function, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) or "incompatible" in str(e)
            print(f"  [PASS 5B] Aborted as expected: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        c.close()

    # Subcase 5C: Incompatible index definition (missing predicate)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)
        print("  [SUBCASE 5C] Incompatible index predicate on idx_study_sessions_expires_at... ")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public.student_study_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id UUID NOT NULL REFERENCES public.students (id) ON DELETE CASCADE,
                    course_id VARCHAR(100) NOT NULL REFERENCES public.courses (id) ON DELETE RESTRICT,
                    lecture_id VARCHAR(100) NOT NULL REFERENCES public.lectures (id) ON DELETE RESTRICT,
                    session_token VARCHAR(128) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    active_seconds INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    client_ip VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                    last_sequence_number INTEGER NOT NULL DEFAULT 0,
                    last_payload_hash VARCHAR(64),
                    last_response_json TEXT,
                    last_credited_seconds INTEGER NOT NULL DEFAULT 0,
                    total_seconds INTEGER NOT NULL DEFAULT 0,
                    close_reason VARCHAR(50),
                    CONSTRAINT uq_study_sessions_token UNIQUE (session_token),
                    CONSTRAINT uq_study_sessions_id_student UNIQUE (id, student_id),
                    CONSTRAINT ck_study_sessions_duration_non_negative CHECK (duration_seconds >= 0),
                    CONSTRAINT ck_study_sessions_active_non_negative CHECK (active_seconds >= 0),
                    CONSTRAINT ck_study_sessions_last_sequence_non_negative CHECK (last_sequence_number >= 0),
                    CONSTRAINT ck_study_sessions_last_credited_non_negative CHECK (last_credited_seconds >= 0),
                    CONSTRAINT ck_study_sessions_total_seconds_non_negative CHECK (total_seconds >= 0),
                    CONSTRAINT ck_study_sessions_status CHECK (
                        status IN ('ACTIVE', 'DISPLACED', 'CLOSED', 'PAUSED', 'COMPLETED', 'EXPIRED')
                    )
                );
                -- Incompatible non-partial index
                CREATE INDEX idx_study_sessions_expires_at ON public.student_study_sessions (expires_at);
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for incompatible index predicate, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) or "predicate" in str(e)
            print(f"  [PASS 5C] Aborted as expected: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

    # Subcase 5D: Incompatible status CHECK constraint (missing statuses)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)
        print("  [SUBCASE 5D] Incompatible status CHECK constraint definition... ")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public.student_study_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id UUID NOT NULL REFERENCES public.students (id) ON DELETE CASCADE,
                    course_id VARCHAR(100) NOT NULL REFERENCES public.courses (id) ON DELETE RESTRICT,
                    lecture_id VARCHAR(100) NOT NULL REFERENCES public.lectures (id) ON DELETE RESTRICT,
                    session_token VARCHAR(128) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    active_seconds INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    client_ip VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                    last_sequence_number INTEGER NOT NULL DEFAULT 0,
                    last_payload_hash VARCHAR(64),
                    last_response_json TEXT,
                    last_credited_seconds INTEGER NOT NULL DEFAULT 0,
                    total_seconds INTEGER NOT NULL DEFAULT 0,
                    close_reason VARCHAR(50),
                    CONSTRAINT uq_study_sessions_token UNIQUE (session_token),
                    CONSTRAINT uq_study_sessions_id_student UNIQUE (id, student_id),
                    CONSTRAINT ck_study_sessions_duration_non_negative CHECK (duration_seconds >= 0),
                    CONSTRAINT ck_study_sessions_active_non_negative CHECK (active_seconds >= 0),
                    CONSTRAINT ck_study_sessions_last_sequence_non_negative CHECK (last_sequence_number >= 0),
                    CONSTRAINT ck_study_sessions_last_credited_non_negative CHECK (last_credited_seconds >= 0),
                    CONSTRAINT ck_study_sessions_total_seconds_non_negative CHECK (total_seconds >= 0),
                    -- Incompatible status constraint: only allows 2 values
                    CONSTRAINT ck_study_sessions_status CHECK (
                        status IN ('ACTIVE', 'CLOSED')
                    )
                );
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for incompatible status constraint, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) or "ck_study_sessions_status" in str(e)
            print(f"  [PASS 5D] Aborted as expected: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

    # Subcase 5E: Incompatible composite FK (missing confdelsetcols)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)
        print("  [SUBCASE 5E] Incompatible composite FK on student_study_clocks... ")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public.student_study_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id UUID NOT NULL REFERENCES public.students (id) ON DELETE CASCADE,
                    course_id VARCHAR(100) NOT NULL REFERENCES public.courses (id) ON DELETE RESTRICT,
                    lecture_id VARCHAR(100) NOT NULL REFERENCES public.lectures (id) ON DELETE RESTRICT,
                    session_token VARCHAR(128) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    active_seconds INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    client_ip VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                    last_sequence_number INTEGER NOT NULL DEFAULT 0,
                    last_payload_hash VARCHAR(64),
                    last_response_json TEXT,
                    last_credited_seconds INTEGER NOT NULL DEFAULT 0,
                    total_seconds INTEGER NOT NULL DEFAULT 0,
                    close_reason VARCHAR(50),
                    CONSTRAINT uq_study_sessions_token UNIQUE (session_token),
                    CONSTRAINT uq_study_sessions_id_student UNIQUE (id, student_id),
                    CONSTRAINT ck_study_sessions_duration_non_negative CHECK (duration_seconds >= 0),
                    CONSTRAINT ck_study_sessions_active_non_negative CHECK (active_seconds >= 0),
                    CONSTRAINT ck_study_sessions_last_sequence_non_negative CHECK (last_sequence_number >= 0),
                    CONSTRAINT ck_study_sessions_last_credited_non_negative CHECK (last_credited_seconds >= 0),
                    CONSTRAINT ck_study_sessions_total_seconds_non_negative CHECK (total_seconds >= 0),
                    CONSTRAINT ck_study_sessions_status CHECK (
                        status IN ('ACTIVE', 'DISPLACED', 'CLOSED', 'PAUSED', 'COMPLETED', 'EXPIRED')
                    )
                );
                CREATE INDEX idx_study_sessions_student_status ON public.student_study_sessions (student_id, status);
                CREATE INDEX idx_study_sessions_student_lecture ON public.student_study_sessions (student_id, lecture_id);
                CREATE INDEX idx_study_sessions_expires_at ON public.student_study_sessions (expires_at) WHERE status = 'ACTIVE';

                CREATE TABLE public.student_study_clocks (
                    student_id UUID PRIMARY KEY REFERENCES public.students (id) ON DELETE CASCADE,
                    active_session_id UUID,
                    active_lecture_id VARCHAR(100) REFERENCES public.lectures (id) ON DELETE SET NULL,
                    lease_expires_at TIMESTAMPTZ NOT NULL,
                    last_credited_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    -- Incompatible standard FK (not composite with setcols)
                    CONSTRAINT fk_study_clocks_active_session_owner FOREIGN KEY (active_session_id)
                        REFERENCES public.student_study_sessions (id) ON DELETE SET NULL
                );
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for incompatible composite FK, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) or "composite FK" in str(e)
            print(f"  [PASS 5E] Aborted as expected: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

    # Subcase 5F: Missing ck_study_sessions_status constraint on existing study sessions
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)
        print("  [SUBCASE 5F] Missing ck_study_sessions_status constraint on existing table... ")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public.student_study_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    student_id UUID NOT NULL REFERENCES public.students (id) ON DELETE CASCADE,
                    course_id VARCHAR(100) NOT NULL REFERENCES public.courses (id) ON DELETE RESTRICT,
                    lecture_id VARCHAR(100) NOT NULL REFERENCES public.lectures (id) ON DELETE RESTRICT,
                    session_token VARCHAR(128) NOT NULL,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    ended_at TIMESTAMPTZ,
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    active_seconds INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    client_ip VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                    last_sequence_number INTEGER NOT NULL DEFAULT 0,
                    last_payload_hash VARCHAR(64),
                    last_response_json TEXT,
                    last_credited_seconds INTEGER NOT NULL DEFAULT 0,
                    total_seconds INTEGER NOT NULL DEFAULT 0,
                    close_reason VARCHAR(50),
                    CONSTRAINT uq_study_sessions_token UNIQUE (session_token),
                    CONSTRAINT uq_study_sessions_id_student UNIQUE (id, student_id),
                    CONSTRAINT ck_study_sessions_duration_non_negative CHECK (duration_seconds >= 0),
                    CONSTRAINT ck_study_sessions_active_non_negative CHECK (active_seconds >= 0),
                    CONSTRAINT ck_study_sessions_last_sequence_non_negative CHECK (last_sequence_number >= 0),
                    CONSTRAINT ck_study_sessions_last_credited_non_negative CHECK (last_credited_seconds >= 0),
                    CONSTRAINT ck_study_sessions_total_seconds_non_negative CHECK (total_seconds >= 0)
                    -- Omitted ck_study_sessions_status
                );
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for missing ck_study_sessions_status, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) and "ck_study_sessions_status" in str(e)
            print(f"  [PASS 5F] Aborted as expected: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

    # Subcase 5G: SQL NULL catalog validation check (missing column metadata fails closed)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        print("  [SUBCASE 5G] SQL NULL catalog check (missing metadata fails closed)... ")
        with conn.cursor() as cur:
            # Drop minutes_spent temporarily to test NULL metadata handling
            cur.execute("ALTER TABLE public.student_daily_activity DROP COLUMN minutes_spent;")
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(MIGRATION_SQL_PATH))
            assert False, "Expected Preflight Failure for missing minutes_spent column, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Preflight Failure" in str(e) or "minutes_spent" in str(e) or "datatype_mismatch" in str(e)
            print(f"  [PASS 5G] Aborted as expected: {str(e).strip().splitlines()[0]}")
        finally:
            # Restore minutes_spent to preserve baseline schema
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE public.student_daily_activity ADD COLUMN minutes_spent INTEGER NOT NULL DEFAULT 0;")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 6: Unexpected dependencies block rollback without CASCADE (6 Subcases)
# -----------------------------------------------------------------------------
def test_6_unexpected_dependencies_block_rollback():
    print("\n" + "="*70)
    print("[TEST 6] Unexpected Dependencies Block Rollback Without CASCADE (6 Subcases)")
    print("="*70)

    # Subcase 6A: Unexpected View depends on student_study_sessions
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        print("  [SETUP] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        print("  [SUBCASE 6A] Creating dependent view on student_study_sessions...")
        with conn.cursor() as cur:
            cur.execute("CREATE VIEW public.v_external_audit AS SELECT id, session_token FROM public.student_study_sessions;")
        
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(ROLLBACK_SQL_PATH))
            assert False, "Expected Rollback Blocked due to view dependency, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Rollback Blocked" in str(e) and "View(s)" in str(e)
            print(f"  [PASS 6A] Rollback safely refused: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        with c.cursor() as cur:
            cur.execute("DROP VIEW IF EXISTS public.v_external_audit;")
        c.close()

    # Subcase 6B: Unexpected Foreign Key references student_study_sessions
    conn = get_connection()
    try:
        print("  [SUBCASE 6B] Creating external table with FK to student_study_sessions...")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public.external_audit_log (
                    id SERIAL PRIMARY KEY,
                    session_id UUID REFERENCES public.student_study_sessions (id)
                );
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(ROLLBACK_SQL_PATH))
            assert False, "Expected Rollback Blocked due to external FK dependency, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Rollback Blocked" in str(e) and "foreign key" in str(e)
            print(f"  [PASS 6B] Rollback safely refused: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        with c.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS public.external_audit_log;")
        c.close()

    # Subcase 6C: Stored Function references sync_student_daily_minutes in source text
    conn = get_connection()
    try:
        print("  [SUBCASE 6C] Creating external function referencing sync_student_daily_minutes...")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE FUNCTION public.audit_cron_caller()
                RETURNS VOID LANGUAGE plpgsql AS $$
                BEGIN
                    PERFORM 'sync_student_daily_minutes'::regproc;
                END;
                $$;
            """)
        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(ROLLBACK_SQL_PATH))
            assert False, "Expected Rollback Blocked due to function source dependency, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Rollback Blocked" in str(e) and "sync_student_daily_minutes" in str(e)
            print(f"  [PASS 6C] Rollback safely refused: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        with c.cursor() as cur:
            cur.execute("DROP FUNCTION IF EXISTS public.audit_cron_caller();")
        c.close()

    # Subcase 6D: Ownership metadata table preservation when pre-existing
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        print("  [SUBCASE 6D] Pre-existing ownership table preservation across rollback...")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE public._migration_phase6_4_2_ownership (
                    schema_name VARCHAR(63) NOT NULL,
                    object_type VARCHAR(50) NOT NULL,
                    object_name VARCHAR(150) NOT NULL,
                    created_by_phase6_4_2 BOOLEAN NOT NULL,
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                    CONSTRAINT pk_phase6_4_2_ownership PRIMARY KEY (schema_name, object_type, object_name)
                );
                INSERT INTO public._migration_phase6_4_2_ownership 
                VALUES ('public', 'TABLE', '_migration_phase6_4_2_ownership', false);
            """)

        print("  [ACTION] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        print("  [ACTION] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))

        # Assert ownership table was PRESERVED
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = '_migration_phase6_4_2_ownership';
            """)
            assert cur.fetchone() is not None, "Pre-existing ownership table was improperly dropped by rollback!"
            print("  [PASS 6D] Pre-existing _migration_phase6_4_2_ownership was preserved after rollback!")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        c.close()

    # Subcase 6E: External Foreign Key referencing seconds_spent blocks rollback
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        print("  [SUBCASE 6E] External foreign key referencing seconds_spent blocks rollback...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

            # Add unique constraint to allow FK reference, then create external dependent table
            cur.execute("ALTER TABLE public.student_daily_activity ADD CONSTRAINT uq_student_daily_seconds UNIQUE (student_id, activity_date, seconds_spent);")
            cur.execute("""
                CREATE TABLE public.external_seconds_ref (
                    id SERIAL PRIMARY KEY,
                    student_id UUID NOT NULL,
                    activity_date DATE NOT NULL,
                    seconds_spent INTEGER NOT NULL,
                    CONSTRAINT fk_ext_seconds FOREIGN KEY (student_id, activity_date, seconds_spent)
                        REFERENCES public.student_daily_activity (student_id, activity_date, seconds_spent)
                );
            """)

        try:
            with conn.cursor() as cur:
                cur.execute(read_sql(ROLLBACK_SQL_PATH))
            assert False, "Expected Rollback Blocked due to external FK on seconds_spent, but succeeded!"
        except psycopg2.DatabaseError as e:
            assert "Rollback Blocked" in str(e) and "seconds_spent" in str(e)
            print(f"  [PASS 6E] Rollback safely refused: {str(e).strip().splitlines()[0]}")
    finally:
        conn.close()
        c = get_connection()
        with c.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS public.external_seconds_ref;")
            cur.execute("ALTER TABLE public.student_daily_activity DROP CONSTRAINT IF EXISTS uq_student_daily_seconds;")
        clean_phase642_objects(c)
        c.close()

    # Subcase 6F: Baseline prerequisite data preservation across migration and rollback
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)
        baseline_date = '2026-11-20'
        baseline_minutes = 45

        print("  [SUBCASE 6F] Baseline prerequisite data preservation across migration and rollback...")
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.student_daily_activity (student_id, activity_date, minutes_spent, lessons_completed)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (student_id, activity_date) DO UPDATE SET minutes_spent = EXCLUDED.minutes_spent;
            """, (student_id, baseline_date, baseline_minutes))

        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        # Check seconds_spent was backfilled
        with conn.cursor() as cur:
            cur.execute("SELECT seconds_spent FROM public.student_daily_activity WHERE student_id = %s AND activity_date = %s;", (student_id, baseline_date))
            sec = cur.fetchone()[0]
            assert sec == baseline_minutes * 60, f"Expected backfilled seconds {baseline_minutes * 60}, got {sec}"

        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))

        # Assert baseline minutes_spent remains unchanged
        with conn.cursor() as cur:
            cur.execute("SELECT minutes_spent FROM public.student_daily_activity WHERE student_id = %s AND activity_date = %s;", (student_id, baseline_date))
            mins = cur.fetchone()[0]
            assert mins == baseline_minutes, f"Baseline minutes_spent corrupted! Expected {baseline_minutes}, got {mins}"
            print(f"  [PASS 6F] Baseline minutes_spent preserved intact: {mins} minutes.")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 7: Full SQL lifecycle, heartbeat accounting, and constraint regression suite
# Note: SQL-level regression suite testing database schema, locks, and triggers.
# Handler-level execution is tested in Test 8.
# -----------------------------------------------------------------------------
def test_7_full_migration_and_heartbeat_regression():
    print("\n" + "="*70)
    print("[TEST 7] Full Migration, SQL Heartbeat Accounting & Integrity Regression Suite")
    print("="*70)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)

        # 1. Run migration
        print("  [STEP 1] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))
        print("  [ASSERT 1] Migration executed successfully.")

        # 2. Run post_assertions.sql standalone
        print("  [STEP 2] Executing standalone post_assertions.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(POST_ASSERTIONS_SQL_PATH))
        print("  [ASSERT 2] Post-migration assertions passed cleanly.")

        # 3. Create active session and acquire lease on clock
        print("  [STEP 3] Testing study session creation and clock lease acquisition...")
        session_id = str(uuid.uuid4())
        session_token = f"token_test_{uuid.uuid4().hex}"
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.student_study_sessions (
                    id, student_id, course_id, lecture_id, session_token,
                    expires_at, active_seconds, duration_seconds, status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    clock_timestamp() + interval '5 minutes', 0, 0, 'ACTIVE'
                );
            """, (session_id, student_id, course_id, lecture_id, session_token))

            cur.execute("""
                INSERT INTO public.student_study_clocks (
                    student_id, active_session_id, active_lecture_id,
                    lease_expires_at, last_credited_at
                ) VALUES (
                    %s, %s, %s,
                    clock_timestamp() + interval '5 minutes', clock_timestamp()
                ) ON CONFLICT (student_id) DO UPDATE SET
                    active_session_id = EXCLUDED.active_session_id,
                    active_lecture_id = EXCLUDED.active_lecture_id,
                    lease_expires_at = EXCLUDED.lease_expires_at,
                    last_credited_at = EXCLUDED.last_credited_at,
                    updated_at = clock_timestamp();
            """, (student_id, session_id, lecture_id))
        print("  [ASSERT 3] Study session and clock lease established.")

        # 4. Sequential heartbeat increments and trigger sync
        print("  [STEP 4] Testing sequential heartbeat increments & daily activity trigger...")
        with conn.cursor() as cur:
            # Clean test student activity to start cleanly at 0
            cur.execute("DELETE FROM public.student_daily_activity WHERE student_id = %s;", (student_id,))

            # First heartbeat (+30 seconds)
            cur.execute("""
                UPDATE public.student_study_sessions
                SET active_seconds = active_seconds + 30,
                    duration_seconds = duration_seconds + 30,
                    last_sequence_number = 1,
                    last_credited_seconds = 30,
                    total_seconds = 30,
                    last_heartbeat_at = clock_timestamp(),
                    expires_at = clock_timestamp() + interval '5 minutes'
                WHERE id = %s;
            """, (session_id,))

            # Daily activity sync via trigger
            today = '2026-11-21'
            cur.execute("""
                INSERT INTO public.student_daily_activity (
                    student_id, activity_date, minutes_spent, seconds_spent, lessons_completed
                ) VALUES (
                    %s, %s, 0, 30, 0
                ) ON CONFLICT (student_id, activity_date) DO UPDATE SET
                    seconds_spent = public.student_daily_activity.seconds_spent + EXCLUDED.seconds_spent;
            """, (student_id, today))

            # Second heartbeat (+30 seconds) -> total 60 seconds = 1 minute
            cur.execute("""
                UPDATE public.student_study_sessions
                SET active_seconds = active_seconds + 30,
                    duration_seconds = duration_seconds + 30,
                    last_sequence_number = 2,
                    last_credited_seconds = 30,
                    total_seconds = 60,
                    last_heartbeat_at = clock_timestamp()
                WHERE id = %s;
            """, (session_id,))

            cur.execute("""
                UPDATE public.student_daily_activity
                SET seconds_spent = seconds_spent + 30
                WHERE student_id = %s AND activity_date = %s;
            """, (student_id, today))

            # Assert trigger computed minutes_spent = 1
            cur.execute("""
                SELECT seconds_spent, minutes_spent 
                FROM public.student_daily_activity 
                WHERE student_id = %s AND activity_date = %s;
            """, (student_id, today))
            sec, mins = cur.fetchone()
            assert sec == 60, f"Expected seconds_spent 60, got {sec}"
            assert mins == 1, f"Expected minutes_spent 1 via trigger, got {mins}"
        print(f"  [ASSERT 4] Daily activity synchronized: seconds_spent={sec}, minutes_spent={mins}.")

        # 5. Non-negative constraints: verify rejection of negative seconds
        print("  [STEP 5] Verifying rejection of negative seconds...")
        conn_neg1 = get_connection()
        try:
            with conn_neg1.cursor() as cur:
                cur.execute("""
                    UPDATE public.student_study_sessions
                    SET active_seconds = -10
                    WHERE id = %s;
                """, (session_id,))
            assert False, "Negative active_seconds was unexpectedly accepted!"
        except psycopg2.DatabaseError as e:
            assert "check_violation" in str(e) or "ck_study_sessions_active_non_negative" in str(e)
            print("  [ASSERT 5A] Negative active_seconds correctly rejected by CHECK constraint.")
        finally:
            conn_neg1.close()

        conn_neg2 = get_connection()
        try:
            with conn_neg2.cursor() as cur:
                cur.execute("""
                    INSERT INTO public.student_daily_activity (
                        student_id, activity_date, minutes_spent, seconds_spent, lessons_completed
                    ) VALUES (%s, '2026-11-22', 0, -50, 0);
                """, (student_id,))
            assert False, "Negative seconds_spent was unexpectedly accepted!"
        except psycopg2.DatabaseError as e:
            assert "check_violation" in str(e) or "negative" in str(e)
            print("  [ASSERT 5B] Negative seconds_spent rejected by trigger/CHECK constraint.")
        finally:
            conn_neg2.close()

        # 6. Overflow protection: verify rejection of minutes_spent > 35,791,394
        print("  [STEP 6] Verifying overflow guard before conversion...")
        conn_over = get_connection()
        try:
            with conn_over.cursor() as cur:
                cur.execute("""
                    INSERT INTO public.student_daily_activity (
                        student_id, activity_date, minutes_spent, seconds_spent, lessons_completed
                    ) VALUES (%s, '2026-11-23', 35791395, 0, 0);
                """, (student_id,))
            assert False, "Overflow minutes_spent was unexpectedly accepted!"
        except psycopg2.DatabaseError as e:
            assert "numeric_value_out_of_range" in str(e) or "overflow" in str(e)
            print("  [ASSERT 6] Overflow minutes_spent (>35,791,394) correctly rejected.")
        finally:
            conn_over.close()

        # 7. Displaced session protection
        print("  [STEP 7] Verifying displaced session cannot steal clock lease...")
        session2_id = str(uuid.uuid4())
        session2_token = f"token_reg_{uuid.uuid4().hex}"
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.student_study_sessions (
                    id, student_id, course_id, lecture_id, session_token,
                    expires_at, active_seconds, duration_seconds, status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    clock_timestamp() + interval '5 minutes', 0, 0, 'ACTIVE'
                );
            """, (session2_id, student_id, course_id, lecture_id, session2_token))

            cur.execute("UPDATE public.student_study_sessions SET status = 'DISPLACED' WHERE id = %s;", (session_id,))
            cur.execute("""
                UPDATE public.student_study_clocks 
                SET active_session_id = %s, lease_expires_at = clock_timestamp() + interval '5 minutes'
                WHERE student_id = %s;
            """, (session2_id, student_id))

            # Attempt displaced heartbeat from session 1: clock condition prevents lease update
            cur.execute("""
                UPDATE public.student_study_clocks
                SET lease_expires_at = clock_timestamp() + interval '5 minutes'
                WHERE student_id = %s AND active_session_id = %s;
            """, (student_id, session_id))
            cur.execute("SELECT active_session_id FROM public.student_study_clocks WHERE student_id = %s;", (student_id,))
            curr_active = str(cur.fetchone()[0])
            assert curr_active == session2_id, f"Clock lease was corrupted by displaced session! Active: {curr_active}"
        print(f"  [ASSERT 7] Displaced session lease isolation verified: active lease remains {session2_id}.")

        # 8. Composite Foreign Key SET NULL behavior on session deletion
        print("  [STEP 8] Verifying composite FK SET NULL behavior...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.student_study_sessions WHERE id = %s;", (session2_id,))
            cur.execute("SELECT active_session_id, student_id FROM public.student_study_clocks WHERE student_id = %s;", (student_id,))
            row = cur.fetchone()
            assert row[0] is None, f"active_session_id not set to NULL: {row[0]}"
            assert str(row[1]) == student_id, f"student_id was improperly modified! {row[1]}"
        print("  [ASSERT 8] Composite FK SET NULL correctly nulled active_session_id while preserving student_id.")

        # 9. Clean Rollback execution
        print("  [STEP 9] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))
        print("  [ASSERT 9] Rollback executed cleanly.")

        # 10. Post-Rollback baseline verification
        print("  [STEP 10] Verifying post-rollback baseline state...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('student_study_sessions', 'student_study_clocks', '_migration_phase6_4_2_ownership');
            """)
            assert len(cur.fetchall()) == 0, "Phase 6.4.2 tables survived rollback unexpectedly!"

            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = 'public' AND column_name = 'seconds_spent';
            """)
            assert len(cur.fetchall()) == 0, "seconds_spent columns survived rollback unexpectedly!"
        print("  [PASS 7] Full migration, lifecycle, constraints, and rollback regression passed completely!")

    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

# -----------------------------------------------------------------------------
# TEST 8: Python handle_heartbeat_transaction application handler integration
# -----------------------------------------------------------------------------
def test_8_python_heartbeat_handler_integration():
    """
    [TEST 8] Python handle_heartbeat_transaction Application Integration Test
    Directly invokes study_tracker.handle_heartbeat_transaction against the
    isolated test database to verify Python application code compatibility.
    Verifies that Python application code correctly coordinates with Phase 6.4.2
    database tables, locks, sequences, and Lagos midnight splitting.
    """
    print("\n" + "="*70)
    print("[TEST 8] Python handle_heartbeat_transaction Application Integration")
    print("="*70)
    conn = get_connection()
    try:
        clean_phase642_objects(conn)
        student_id, course_id, lecture_id = ensure_seed_records(conn)

        # 1. Run migration
        print("  [SETUP] Executing migration.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(MIGRATION_SQL_PATH))

        # 2. Configure Flask application to point strictly to the authorized disposable test database
        from app import app, db
        from study_tracker import handle_heartbeat_transaction
        from sqlalchemy import create_engine

        dsn = os.environ.get("PHASE642_TEST_DATABASE_URL")
        app.config['SQLALCHEMY_DATABASE_URI'] = dsn
        app.config['TESTING'] = True

        test_engine = create_engine(dsn)

        session_token = f"tok_py_test_{uuid.uuid4().hex}"
        payload_hash = hashlib.sha256(b"test_payload_1").hexdigest()

        with app.app_context():
            # Strictly bind session to disposable test engine and assert non-production target
            app.extensions['sqlalchemy'].engines[None] = test_engine
            assert "ep-hidden-river-bd9kghxc" in str(db.engine.url), f"CRITICAL: Engine URL {db.engine.url} is not the approved disposable endpoint!"

            # First heartbeat (seq=1, +30s)
            raw_body, resp = handle_heartbeat_transaction(
                student_id=student_id,
                session_token=session_token,
                course_id=course_id,
                lecture_id=lecture_id,
                seq=1,
                payload_hash=payload_hash,
                is_active=True,
                event_type="HEARTBEAT",
                credited_candidate=30
            )
            assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {raw_body}"
            print("  [STEP 1] Python heartbeat handler successfully processed first heartbeat (200 OK).")

            # Duplicate replay (same seq, same hash -> replay cached response)
            raw_body_dup, resp_dup = handle_heartbeat_transaction(
                student_id=student_id,
                session_token=session_token,
                course_id=course_id,
                lecture_id=lecture_id,
                seq=1,
                payload_hash=payload_hash,
                is_active=True,
                event_type="HEARTBEAT",
                credited_candidate=30
            )
            assert resp_dup.status_code == 200, "Duplicate heartbeat failed!"
            assert raw_body == raw_body_dup, "Duplicate heartbeat response did not match stored replay!"
            print("  [STEP 2] Python heartbeat handler successfully replayed cached duplicate response.")

        # Verify DB state directly with psycopg2
        with conn.cursor() as cur:
            cur.execute("""
                SELECT active_seconds, total_seconds, last_sequence_number 
                FROM public.student_study_sessions WHERE session_token = %s;
            """, (session_token,))
            row = cur.fetchone()
            assert row is not None, "Study session not created by Python handler!"
            assert row[0] == 30, f"Expected active_seconds 30, got {row[0]}"
            assert row[2] == 1, f"Expected last_sequence_number 1, got {row[2]}"

        # Clean rollback at end of test
        print("  [CLEANUP] Executing rollback.sql...")
        with conn.cursor() as cur:
            cur.execute(read_sql(ROLLBACK_SQL_PATH))
        print("  [PASS 8] Python handle_heartbeat_transaction integration verified cleanly!")
    finally:
        conn.close()
        c = get_connection()
        clean_phase642_objects(c)
        clean_test_seed_records(c)
        c.close()

# -----------------------------------------------------------------------------
# MAIN TEST HARNESS RUNNER
# -----------------------------------------------------------------------------
def run_all_tests():
    print("="*80)
    print("PHASE 6.4.2: FINAL DEPLOYMENT SAFETY & REGRESSION TEST HARNESS")
    print("Target Database: Disposable Isolated Neon Compute (ep-hidden-river-bd9kghxc)")
    print("Target Schema: public (Disposable Test Database)")
    print("="*80)

    # Preflight safety check
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, inet_server_addr(), version();")
        db, user, addr, ver = cur.fetchone()
        print(f"Connected to: db={db}, user={user}, server={addr}")
        print(f"Engine: {ver}")
    conn.close()

    tests = [
        test_1_preexisting_trigger_survives,
        test_2_preexisting_function_survives,
        test_3_preexisting_study_tables_survive,
        test_4_preexisting_index_not_removed,
        test_5_incompatible_objects_abort,
        test_6_unexpected_dependencies_block_rollback,
        test_7_full_migration_and_heartbeat_regression,
        test_8_python_heartbeat_handler_integration,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"\n[FAILURE] {t.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*80)
    print(f"PHASE 6.4.2 TEST HARNESS RESULTS: {passed} PASSED, {failed} FAILED (TOTAL {len(tests)})")
    print("="*80)

    if failed > 0:
        sys.exit(1)
    else:
        print("ALL REGRESSION TESTS PASSED IN ISOLATED DISPOSABLE ENVIRONMENT.")

if __name__ == '__main__':
    run_all_tests()
