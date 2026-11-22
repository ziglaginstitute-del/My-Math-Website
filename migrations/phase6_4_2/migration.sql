-- ============================================================================
-- Phase 6.4.2: Study-Time Tracking Database Migration (Final Executable SQL)
-- Target: PostgreSQL 18.7 (Neon Database: public schema)
-- Features: 7-Table Prerequisite Audit, Exact Normalized Defaults, Strict Ownership Tracking, Non-Destructive
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- STEP 1: COMPREHENSIVE PREFLIGHT VALIDATION (Exhaustive 7-Table & Study Audit)
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_rec RECORD;
    v_hash TEXT;
    v_fn_count INTEGER;
BEGIN
    -- 1. Base table existence (7 prerequisite tables)
    FOR v_rec IN 
        SELECT unnest(ARRAY[
            'students', 'courses', 'lectures', 'student_enrollments',
            'student_daily_activity', 'student_lesson_progress', 'student_diagnostic_history'
        ]) AS tbl
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = v_rec.tbl) THEN
            RAISE EXCEPTION 'Preflight Failure: Prerequisite table public.% is missing', v_rec.tbl
                USING ERRCODE = 'undefined_table';
        END IF;
    END LOOP;

    -- 2. Primary keys and ordered unique constraints on prerequisite tables
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.students'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.students'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['email']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: students PK or unique email missing' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.courses'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.courses'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['slug']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: courses PK or unique slug missing' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.lectures'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: lectures primary key must be (id)' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_enrollments'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_enrollments'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'course_id']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: student_enrollments PK or unique (student_id, course_id) missing' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_lesson_progress'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_lesson_progress'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'lecture_id']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: student_lesson_progress PK or unique (student_id, lecture_id) missing' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_daily_activity'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_daily_activity'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'activity_date']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: student_daily_activity PK or unique (student_id, activity_date) missing' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_diagnostic_history'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_diagnostic_history'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'subject', 'attempt_number']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: student_diagnostic_history PK or unique attempt missing' USING ERRCODE = 'invalid_table_definition';
    END IF;

    -- 3. Student foreign keys (ON DELETE CASCADE required)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_enrollments'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.students'::regclass AND c.confdeltype = 'c'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_lesson_progress'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.students'::regclass AND c.confdeltype = 'c'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_daily_activity'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.students'::regclass AND c.confdeltype = 'c'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_diagnostic_history'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.students'::regclass AND c.confdeltype = 'c'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: prerequisite student foreign keys must be ON DELETE CASCADE' USING ERRCODE = 'invalid_table_definition';
    END IF;

    -- 4. Content foreign keys (ON DELETE RESTRICT required)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_enrollments'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.courses'::regclass AND c.confdeltype = 'r'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['course_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_lesson_progress'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.courses'::regclass AND c.confdeltype = 'r'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['course_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_lesson_progress'::regclass AND c.contype = 'f'
          AND c.confrelid = 'public.lectures'::regclass AND c.confdeltype = 'r'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['lecture_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: student content FKs missing or not ON DELETE RESTRICT' USING ERRCODE = 'invalid_table_definition';
    END IF;

    -- 5. Existing CHECK constraints on prerequisite tables
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_daily_activity'::regclass AND c.contype = 'c'
          AND c.conname = 'chk_daily_activity_minutes_nonneg'
          AND pg_get_constraintdef(c.oid) = 'CHECK ((minutes_spent >= 0))'
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: student_daily_activity missing chk_daily_activity_minutes_nonneg' USING ERRCODE = 'invalid_table_definition';
    END IF;

    -- 6. Existing seconds_spent columns and CHECK constraint inspection
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'seconds_spent') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'seconds_spent'
              AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0'
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: Existing student_lesson_progress.seconds_spent is incompatible in type, nullability, or default' USING ERRCODE = 'datatype_mismatch';
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.student_lesson_progress'::regclass AND conname = 'chk_lesson_progress_seconds_nonneg') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conrelid = 'public.student_lesson_progress'::regclass 
              AND conname = 'chk_lesson_progress_seconds_nonneg'
              AND contype = 'c'
              AND pg_get_constraintdef(oid) = 'CHECK ((seconds_spent >= 0))'
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: Existing chk_lesson_progress_seconds_nonneg expression is incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'seconds_spent') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'seconds_spent'
              AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0'
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: Existing student_daily_activity.seconds_spent is incompatible in type, nullability, or default' USING ERRCODE = 'datatype_mismatch';
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'public.student_daily_activity'::regclass AND conname = 'ck_student_daily_seconds_non_negative') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conrelid = 'public.student_daily_activity'::regclass 
              AND conname = 'ck_student_daily_seconds_non_negative'
              AND contype = 'c'
              AND pg_get_constraintdef(oid) = 'CHECK ((seconds_spent >= 0))'
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: Existing ck_student_daily_seconds_non_negative expression is incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
    END IF;

    -- 7. Exhaustive Validation of Existing student_study_sessions (if present)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'student_study_sessions') THEN
        -- Column definitions, types, nullability, and exact normalized defaults
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'id' AND data_type = 'uuid' AND is_nullable = 'NO' AND TRIM(column_default) = 'gen_random_uuid()') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'student_id' AND data_type = 'uuid' AND is_nullable = 'NO') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.student_id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'course_id' AND data_type = 'character varying' AND character_maximum_length = 100 AND is_nullable = 'NO') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.course_id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'lecture_id' AND data_type = 'character varying' AND character_maximum_length = 100 AND is_nullable = 'NO') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.lecture_id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'session_token' AND data_type = 'character varying' AND character_maximum_length = 128 AND is_nullable = 'NO') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.session_token incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'started_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND TRIM(column_default) = 'clock_timestamp()') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.started_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_heartbeat_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND TRIM(column_default) = 'clock_timestamp()') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.last_heartbeat_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'expires_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND column_default IS NULL) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.expires_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'ended_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.ended_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'duration_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.duration_seconds incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'active_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.active_seconds incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'is_active' AND data_type = 'boolean' AND is_nullable = 'NO' AND TRIM(column_default) = 'true') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.is_active incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'client_ip' AND data_type = 'character varying' AND character_maximum_length = 45 AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.client_ip incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'user_agent' AND data_type = 'text' AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.user_agent incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'status' AND data_type = 'character varying' AND character_maximum_length = 20 AND is_nullable = 'NO' AND TRIM(column_default) = '''ACTIVE''::character varying') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.status incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_sequence_number' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.last_sequence_number incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_payload_hash' AND data_type = 'character varying' AND character_maximum_length = 64 AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.last_payload_hash incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_response_json' AND data_type = 'text' AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.last_response_json incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_credited_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.last_credited_seconds incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'total_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.total_seconds incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'close_reason' AND data_type = 'character varying' AND character_maximum_length = 50 AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions.close_reason incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Primary Key
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'p'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions PK mismatch' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Unique constraints
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'u'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['session_token']::text[]
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'u'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id', 'student_id']::text[]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions unique constraint mismatch' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Foreign keys on student_study_sessions
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'f'
              AND c.confrelid = 'public.students'::regclass AND c.confdeltype = 'c'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
              AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'f'
              AND c.confrelid = 'public.courses'::regclass AND c.confdeltype = 'r'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['course_id']::text[]
              AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'f'
              AND c.confrelid = 'public.lectures'::regclass AND c.confdeltype = 'r'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['lecture_id']::text[]
              AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions foreign keys mismatch' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Non-negative CHECK constraints (mandatory)
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.conname = 'ck_study_sessions_duration_non_negative'
              AND c.contype = 'c' AND pg_get_constraintdef(c.oid) = 'CHECK ((duration_seconds >= 0))'
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.conname = 'ck_study_sessions_active_non_negative'
              AND c.contype = 'c' AND pg_get_constraintdef(c.oid) = 'CHECK ((active_seconds >= 0))'
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.conname = 'ck_study_sessions_last_sequence_non_negative'
              AND c.contype = 'c' AND pg_get_constraintdef(c.oid) = 'CHECK ((last_sequence_number >= 0))'
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.conname = 'ck_study_sessions_last_credited_non_negative'
              AND c.contype = 'c' AND pg_get_constraintdef(c.oid) = 'CHECK ((last_credited_seconds >= 0))'
        ) OR NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.conname = 'ck_study_sessions_total_seconds_non_negative'
              AND c.contype = 'c' AND pg_get_constraintdef(c.oid) = 'CHECK ((total_seconds >= 0))'
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions non-negative CHECK constraints missing or incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Status check: MANDATORY exact six-value definition (Missing constraint must fail)
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.conname = 'ck_study_sessions_status'
              AND c.contype = 'c'
              AND pg_get_constraintdef(c.oid) = 'CHECK (((status)::text = ANY ((ARRAY[''ACTIVE''::character varying, ''DISPLACED''::character varying, ''CLOSED''::character varying, ''PAUSED''::character varying, ''COMPLETED''::character varying, ''EXPIRED''::character varying])::text[])))'
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_sessions ck_study_sessions_status missing or incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Tightened Index Validation (key column count, no INCLUDE columns, validity, predicates)
        IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_study_sessions_student_status' AND relnamespace = 'public'::regnamespace) THEN
            IF NOT EXISTS (
                SELECT 1 FROM pg_index i
                JOIN pg_class c ON c.oid = i.indexrelid
                WHERE c.relname = 'idx_study_sessions_student_status' AND c.relnamespace = 'public'::regnamespace
                  AND i.indrelid = 'public.student_study_sessions'::regclass
                  AND i.indnkeyatts = 2 AND i.indnatts = 2
                  AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey[0:i.indnkeyatts-1]) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'status']::text[]
                  AND NOT i.indisunique AND i.indisvalid AND i.indpred IS NULL
            ) THEN
                RAISE EXCEPTION 'Preflight Failure: Existing idx_study_sessions_student_status definition incompatible' USING ERRCODE = 'invalid_table_definition';
            END IF;
        END IF;

        IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_study_sessions_student_lecture' AND relnamespace = 'public'::regnamespace) THEN
            IF NOT EXISTS (
                SELECT 1 FROM pg_index i
                JOIN pg_class c ON c.oid = i.indexrelid
                WHERE c.relname = 'idx_study_sessions_student_lecture' AND c.relnamespace = 'public'::regnamespace
                  AND i.indrelid = 'public.student_study_sessions'::regclass
                  AND i.indnkeyatts = 2 AND i.indnatts = 2
                  AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey[0:i.indnkeyatts-1]) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'lecture_id']::text[]
                  AND NOT i.indisunique AND i.indisvalid AND i.indpred IS NULL
            ) THEN
                RAISE EXCEPTION 'Preflight Failure: Existing idx_study_sessions_student_lecture definition incompatible' USING ERRCODE = 'invalid_table_definition';
            END IF;
        END IF;

        IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_study_sessions_expires_at' AND relnamespace = 'public'::regnamespace) THEN
            IF NOT EXISTS (
                SELECT 1 FROM pg_index i
                JOIN pg_class c ON c.oid = i.indexrelid
                WHERE c.relname = 'idx_study_sessions_expires_at' AND c.relnamespace = 'public'::regnamespace
                  AND i.indrelid = 'public.student_study_sessions'::regclass
                  AND i.indnkeyatts = 1 AND i.indnatts = 1
                  AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey[0:i.indnkeyatts-1]) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['expires_at']::text[]
                  AND pg_get_expr(i.indpred, i.indrelid) = '((status)::text = ''ACTIVE''::text)'
                  AND NOT i.indisunique AND i.indisvalid
            ) THEN
                RAISE EXCEPTION 'Preflight Failure: Existing idx_study_sessions_expires_at has incompatible column, predicate, or uniqueness' USING ERRCODE = 'invalid_table_definition';
            END IF;
        END IF;
    END IF;

    -- 8. Exhaustive Validation of Existing student_study_clocks (if present)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'student_study_clocks') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'student_id' AND data_type = 'uuid' AND is_nullable = 'NO') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks.student_id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'active_session_id' AND data_type = 'uuid' AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks.active_session_id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'active_lecture_id' AND data_type = 'character varying' AND character_maximum_length = 100 AND is_nullable = 'YES') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks.active_lecture_id incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'lease_expires_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND column_default IS NULL) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks.lease_expires_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'last_credited_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND column_default IS NULL) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks.last_credited_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'updated_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND TRIM(column_default) = 'clock_timestamp()') THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks.updated_at incompatible' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Primary Key
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_clocks'::regclass AND c.contype = 'p'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks PK must be (student_id)' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Foreign keys on student_study_clocks
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_clocks'::regclass AND c.contype = 'f'
              AND c.confrelid = 'public.students'::regclass AND c.confdeltype = 'c'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
              AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks student FK missing or not ON DELETE CASCADE' USING ERRCODE = 'invalid_table_definition';
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_clocks'::regclass AND c.contype = 'f'
              AND c.confrelid = 'public.lectures'::regclass AND c.confdeltype = 'n'
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['active_lecture_id']::text[]
              AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks lecture FK missing or not ON DELETE SET NULL' USING ERRCODE = 'invalid_table_definition';
        END IF;

        -- Composite FK
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            WHERE c.conrelid = 'public.student_study_clocks'::regclass AND c.contype = 'f'
              AND c.conname = 'fk_study_clocks_active_session_owner'
              AND c.confrelid = 'public.student_study_sessions'::regclass
              AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['active_session_id', 'student_id']::text[]
              AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id', 'student_id']::text[]
              AND c.confdeltype = 'n'
              AND c.confdelsetcols = ARRAY[2::smallint]
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: student_study_clocks composite FK is incompatible or missing' USING ERRCODE = 'invalid_table_definition';
        END IF;
    END IF;

    -- 9. Trigger-function identity and security properties validation
    SELECT COUNT(*) INTO v_fn_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'sync_student_daily_minutes';

    IF v_fn_count > 1 THEN
        RAISE EXCEPTION 'Preflight Failure: Multiple overloaded functions named sync_student_daily_minutes found' USING ERRCODE = 'duplicate_function';
    END IF;

    IF v_fn_count = 1 THEN
        SELECT md5(regexp_replace(trim(p.prosrc), '\s+', ' ', 'g')) INTO v_hash
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public' AND p.proname = 'sync_student_daily_minutes'
          AND p.pronargs = 0
          AND p.prorettype = 'trigger'::regtype
          AND p.provolatile = 'v'
          AND p.prosecdef = false
          AND p.prolang = (SELECT oid FROM pg_language WHERE lanname = 'plpgsql');

        IF (v_hash IS DISTINCT FROM '644b5902680d7b4ea4c38b0554d04b8a') THEN
            RAISE EXCEPTION 'Preflight Failure: Existing sync_student_daily_minutes() body or properties incompatible' USING ERRCODE = 'invalid_function_definition';
        END IF;
    END IF;

    -- Trigger relation, events, timing, and enabled state validation
    IF EXISTS (
        SELECT 1 FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND t.tgname = 'trg_sync_student_daily_minutes' AND c.relname != 'student_daily_activity'
    ) THEN
        RAISE EXCEPTION 'Preflight Failure: Trigger trg_sync_student_daily_minutes found on unexpected table' USING ERRCODE = 'invalid_table_definition';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND t.tgname = 'trg_sync_student_daily_minutes'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_proc p ON p.oid = t.tgfoid
            WHERE n.nspname = 'public' AND c.relname = 'student_daily_activity' AND t.tgname = 'trg_sync_student_daily_minutes'
              AND t.tgenabled = 'O'
              AND NOT t.tgisinternal
              AND (t.tgtype & 2) = 2   -- BEFORE
              AND (t.tgtype & 4) = 4   -- INSERT
              AND (t.tgtype & 16) = 16 -- UPDATE
              AND (t.tgtype & 8) = 0   -- NOT DELETE
              AND (t.tgtype & 1) = 1   -- FOR EACH ROW
              AND p.proname = 'sync_student_daily_minutes'
              AND t.tgfoid = ('public.sync_student_daily_minutes()')::regprocedure
        ) THEN
            RAISE EXCEPTION 'Preflight Failure: Existing trg_sync_student_daily_minutes has incompatible target table, events, or function identity' USING ERRCODE = 'invalid_table_definition';
        END IF;
    END IF;

    RAISE NOTICE 'Preflight schema validation completed successfully.';
END $$;

-- ----------------------------------------------------------------------------
-- STEP 2: OWNERSHIP INITIALIZATION & DDL EXECUTION
-- ----------------------------------------------------------------------------

-- 0. Track & Create Phase 6.4.2 Migration Ownership Metadata Table
DO $$
DECLARE
    v_tbl_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = '_migration_phase6_4_2_ownership'
    ) INTO v_tbl_exists;

    IF NOT v_tbl_exists THEN
        CREATE TABLE public._migration_phase6_4_2_ownership (
            schema_name VARCHAR(63) NOT NULL,
            object_type VARCHAR(50) NOT NULL,
            object_name VARCHAR(150) NOT NULL,
            created_by_phase6_4_2 BOOLEAN NOT NULL,
            recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
            CONSTRAINT pk_phase6_4_2_ownership PRIMARY KEY (schema_name, object_type, object_name)
        );
        INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
        VALUES ('public', 'TABLE', '_migration_phase6_4_2_ownership', true)
        ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;
    ELSE
        INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
        VALUES ('public', 'TABLE', '_migration_phase6_4_2_ownership', false)
        ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;
    END IF;
END $$;

-- 1. Track & Add seconds_spent to student_lesson_progress
DO $$
DECLARE
    v_col_exists BOOLEAN;
    v_chk_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'seconds_spent'
    ) INTO v_col_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'COLUMN', 'student_lesson_progress.seconds_spent', NOT v_col_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_col_exists THEN
        ALTER TABLE public.student_lesson_progress ADD COLUMN seconds_spent INTEGER NOT NULL DEFAULT 0;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_lesson_progress'::regclass AND conname = 'chk_lesson_progress_seconds_nonneg'
    ) INTO v_chk_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'CONSTRAINT', 'student_lesson_progress.chk_lesson_progress_seconds_nonneg', NOT v_chk_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_chk_exists THEN
        ALTER TABLE public.student_lesson_progress ADD CONSTRAINT chk_lesson_progress_seconds_nonneg CHECK (seconds_spent >= 0);
    END IF;
END $$;

-- 2. Track & Add seconds_spent to student_daily_activity
DO $$
DECLARE
    v_col_exists BOOLEAN;
    v_chk_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'seconds_spent'
    ) INTO v_col_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'COLUMN', 'student_daily_activity.seconds_spent', NOT v_col_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_col_exists THEN
        ALTER TABLE public.student_daily_activity ADD COLUMN seconds_spent INTEGER NOT NULL DEFAULT 0;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_daily_activity'::regclass AND conname = 'ck_student_daily_seconds_non_negative'
    ) INTO v_chk_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'CONSTRAINT', 'student_daily_activity.ck_student_daily_seconds_non_negative', NOT v_chk_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_chk_exists THEN
        ALTER TABLE public.student_daily_activity ADD CONSTRAINT ck_student_daily_seconds_non_negative CHECK (seconds_spent >= 0);
    END IF;
END $$;

-- 3. Data backfill with overflow preflight
DO $$
DECLARE
    v_overflow_count INTEGER;
    v_type_sec TEXT;
    v_type_min TEXT;
    v_updated_rows INTEGER;
    v_mismatch_count INTEGER;
BEGIN
    SELECT data_type INTO v_type_min
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'minutes_spent';

    SELECT data_type INTO v_type_sec
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'seconds_spent';

    IF (v_type_min IS DISTINCT FROM 'integer') OR (v_type_sec IS DISTINCT FROM 'integer') THEN
        RAISE EXCEPTION 'Backfill Preflight Failure: Incompatible column types (minutes_spent: %, seconds_spent: %)', v_type_min, v_type_sec
            USING ERRCODE = 'datatype_mismatch';
    END IF;

    SELECT COUNT(*) INTO v_overflow_count
    FROM public.student_daily_activity
    WHERE minutes_spent > 35791394;

    IF v_overflow_count > 0 THEN
        RAISE EXCEPTION 'Backfill Aborted: % row(s) in student_daily_activity have minutes_spent > 35,791,394', v_overflow_count
            USING ERRCODE = 'numeric_value_out_of_range';
    END IF;

    UPDATE public.student_daily_activity
    SET seconds_spent = minutes_spent * 60
    WHERE seconds_spent = 0 AND minutes_spent > 0;

    GET DIAGNOSTICS v_updated_rows = ROW_COUNT;

    SELECT COUNT(*) INTO v_mismatch_count
    FROM public.student_daily_activity
    WHERE minutes_spent > 0 AND FLOOR(seconds_spent / 60) != minutes_spent;

    IF v_mismatch_count > 0 THEN
        RAISE EXCEPTION 'Backfill Verification Failure: % rows have mismatched seconds/minutes ratio', v_mismatch_count
            USING ERRCODE = 'data_corrupted';
    END IF;
END $$;

-- 4. Track & Create Trigger Function (Preserving pre-existing compatible function)
DO $$
DECLARE
    v_fn_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'sync_student_daily_minutes' AND pronamespace = 'public'::regnamespace
    ) INTO v_fn_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'FUNCTION', 'sync_student_daily_minutes()', NOT v_fn_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_fn_exists THEN
        EXECUTE $fn_create$
            CREATE FUNCTION public.sync_student_daily_minutes()
            RETURNS TRIGGER
            LANGUAGE plpgsql
            AS $trg$
            DECLARE
                v_seconds_changed BOOLEAN;
                v_minutes_changed BOOLEAN;
            BEGIN
                IF NEW.seconds_spent IS NOT NULL AND NEW.seconds_spent < 0 THEN
                    RAISE EXCEPTION 'seconds_spent cannot be negative: %', NEW.seconds_spent USING ERRCODE = 'check_violation';
                END IF;
                IF NEW.minutes_spent IS NOT NULL AND NEW.minutes_spent < 0 THEN
                    RAISE EXCEPTION 'minutes_spent cannot be negative: %', NEW.minutes_spent USING ERRCODE = 'check_violation';
                END IF;
                IF NEW.seconds_spent IS NULL AND NEW.minutes_spent IS NULL THEN
                    RAISE EXCEPTION 'Both seconds_spent and minutes_spent cannot be NULL' USING ERRCODE = 'not_null_violation';
                END IF;
                IF NEW.seconds_spent IS NULL THEN
                    IF NEW.minutes_spent > 35791394 THEN
                        RAISE EXCEPTION 'minutes_spent % would cause integer overflow (max 35,791,394)', NEW.minutes_spent USING ERRCODE = 'numeric_value_out_of_range';
                    END IF;
                    NEW.seconds_spent := NEW.minutes_spent * 60;
                    RETURN NEW;
                END IF;
                IF NEW.minutes_spent IS NULL THEN
                    NEW.minutes_spent := FLOOR(NEW.seconds_spent / 60);
                    RETURN NEW;
                END IF;
                IF TG_OP = 'INSERT' THEN
                    IF NEW.seconds_spent > 0 THEN
                        NEW.minutes_spent := FLOOR(NEW.seconds_spent / 60);
                    ELSIF NEW.minutes_spent > 0 THEN
                        IF NEW.minutes_spent > 35791394 THEN
                            RAISE EXCEPTION 'minutes_spent % would cause integer overflow (max 35,791,394)', NEW.minutes_spent USING ERRCODE = 'numeric_value_out_of_range';
                        END IF;
                        NEW.seconds_spent := NEW.minutes_spent * 60;
                    ELSE
                        NEW.seconds_spent := 0;
                        NEW.minutes_spent := 0;
                    END IF;
                    RETURN NEW;
                END IF;
                IF TG_OP = 'UPDATE' THEN
                    v_seconds_changed := (NEW.seconds_spent IS DISTINCT FROM OLD.seconds_spent);
                    v_minutes_changed := (NEW.minutes_spent IS DISTINCT FROM OLD.minutes_spent);
                    IF v_seconds_changed AND v_minutes_changed THEN
                        NEW.minutes_spent := FLOOR(NEW.seconds_spent / 60);
                    ELSIF v_seconds_changed THEN
                        NEW.minutes_spent := FLOOR(NEW.seconds_spent / 60);
                    ELSIF v_minutes_changed THEN
                        IF NEW.minutes_spent > 35791394 THEN
                            RAISE EXCEPTION 'minutes_spent % would cause integer overflow (max 35,791,394)', NEW.minutes_spent USING ERRCODE = 'numeric_value_out_of_range';
                        END IF;
                        NEW.seconds_spent := NEW.minutes_spent * 60;
                    END IF;
                    RETURN NEW;
                END IF;
                RETURN NEW;
            END;
            $trg$;
        $fn_create$;
    END IF;
END $$;

-- 5. Track & Create Trigger (Preserving pre-existing compatible trigger)
DO $$
DECLARE
    v_trg_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'student_daily_activity' AND t.tgname = 'trg_sync_student_daily_minutes'
    ) INTO v_trg_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'TRIGGER', 'trg_sync_student_daily_minutes', NOT v_trg_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_trg_exists THEN
        CREATE TRIGGER trg_sync_student_daily_minutes
        BEFORE INSERT OR UPDATE ON public.student_daily_activity
        FOR EACH ROW EXECUTE FUNCTION public.sync_student_daily_minutes();
    END IF;
END $$;

-- 6. Track & Create student_study_sessions Table
DO $$
DECLARE
    v_tbl_exists BOOLEAN;
    v_idx1_exists BOOLEAN;
    v_idx2_exists BOOLEAN;
    v_idx3_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'student_study_sessions'
    ) INTO v_tbl_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'TABLE', 'student_study_sessions', NOT v_tbl_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_tbl_exists THEN
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
    END IF;

    -- Track & Create Indexes
    SELECT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_study_sessions_student_status' AND relnamespace = 'public'::regnamespace) INTO v_idx1_exists;
    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'INDEX', 'idx_study_sessions_student_status', NOT v_idx1_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;
    IF NOT v_idx1_exists THEN
        CREATE INDEX idx_study_sessions_student_status ON public.student_study_sessions (student_id, status);
    END IF;

    SELECT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_study_sessions_student_lecture' AND relnamespace = 'public'::regnamespace) INTO v_idx2_exists;
    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'INDEX', 'idx_study_sessions_student_lecture', NOT v_idx2_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;
    IF NOT v_idx2_exists THEN
        CREATE INDEX idx_study_sessions_student_lecture ON public.student_study_sessions (student_id, lecture_id);
    END IF;

    SELECT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'idx_study_sessions_expires_at' AND relnamespace = 'public'::regnamespace) INTO v_idx3_exists;
    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'INDEX', 'idx_study_sessions_expires_at', NOT v_idx3_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;
    IF NOT v_idx3_exists THEN
        CREATE INDEX idx_study_sessions_expires_at ON public.student_study_sessions (expires_at) WHERE status = 'ACTIVE';
    END IF;
END $$;

-- 7. Track & Create student_study_clocks Table
DO $$
DECLARE
    v_tbl_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'student_study_clocks'
    ) INTO v_tbl_exists;

    INSERT INTO public._migration_phase6_4_2_ownership (schema_name, object_type, object_name, created_by_phase6_4_2)
    VALUES ('public', 'TABLE', 'student_study_clocks', NOT v_tbl_exists)
    ON CONFLICT (schema_name, object_type, object_name) DO NOTHING;

    IF NOT v_tbl_exists THEN
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
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- STEP 3: POST-MIGRATION CATALOG ASSERTIONS
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_def TEXT;
    v_hash TEXT;
    v_fn_count INTEGER;
BEGIN
    -- 1. Assert seconds_spent columns, defaults, nullability and CHECK expressions
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'seconds_spent'
          AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'seconds_spent'
          AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0'
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: seconds_spent column definitions mismatch' USING ERRCODE = 'internal_error';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_lesson_progress'::regclass 
          AND conname = 'chk_lesson_progress_seconds_nonneg' 
          AND contype = 'c' 
          AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((seconds_spent >= 0))'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_daily_activity'::regclass 
          AND conname = 'ck_student_daily_seconds_non_negative' 
          AND contype = 'c' 
          AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((seconds_spent >= 0))'
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: seconds_spent CHECK constraints mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 2. Assert study session columns, types, nullability, and exact normalized defaults
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'id' AND data_type = 'uuid' AND is_nullable = 'NO' AND TRIM(column_default) = 'gen_random_uuid()')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'student_id' AND data_type = 'uuid' AND is_nullable = 'NO')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'course_id' AND data_type = 'character varying' AND character_maximum_length = 100 AND is_nullable = 'NO')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'lecture_id' AND data_type = 'character varying' AND character_maximum_length = 100 AND is_nullable = 'NO')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'session_token' AND data_type = 'character varying' AND character_maximum_length = 128 AND is_nullable = 'NO')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'started_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND TRIM(column_default) = 'clock_timestamp()')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_heartbeat_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND TRIM(column_default) = 'clock_timestamp()')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'expires_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND column_default IS NULL)
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'ended_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'duration_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'active_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'is_active' AND data_type = 'boolean' AND is_nullable = 'NO' AND TRIM(column_default) = 'true')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'client_ip' AND data_type = 'character varying' AND character_maximum_length = 45 AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'user_agent' AND data_type = 'text' AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'status' AND data_type = 'character varying' AND character_maximum_length = 20 AND is_nullable = 'NO' AND TRIM(column_default) = '''ACTIVE''::character varying')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_sequence_number' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_payload_hash' AND data_type = 'character varying' AND character_maximum_length = 64 AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_response_json' AND data_type = 'text' AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'last_credited_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'total_seconds' AND data_type = 'integer' AND is_nullable = 'NO' AND TRIM(column_default) = '0')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_sessions' AND column_name = 'close_reason' AND data_type = 'character varying' AND character_maximum_length = 50 AND is_nullable = 'YES')
    THEN
        RAISE EXCEPTION 'Post-migration assertion failed: student_study_sessions column definitions or defaults mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 3. Assert study session PK, UKs, and non-negative CHECK constraints
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['session_token']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_sessions'::regclass AND c.contype = 'u'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id', 'student_id']::text[]
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: student_study_sessions PK or unique constraints mismatch' USING ERRCODE = 'internal_error';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_study_sessions'::regclass 
          AND conname = 'ck_study_sessions_duration_non_negative' 
          AND contype = 'c' AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((duration_seconds >= 0))'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_study_sessions'::regclass 
          AND conname = 'ck_study_sessions_active_non_negative' 
          AND contype = 'c' AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((active_seconds >= 0))'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_study_sessions'::regclass 
          AND conname = 'ck_study_sessions_last_sequence_non_negative' 
          AND contype = 'c' AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((last_sequence_number >= 0))'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_study_sessions'::regclass 
          AND conname = 'ck_study_sessions_last_credited_non_negative' 
          AND contype = 'c' AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((last_credited_seconds >= 0))'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'public.student_study_sessions'::regclass 
          AND conname = 'ck_study_sessions_total_seconds_non_negative' 
          AND contype = 'c' AND convalidated
          AND pg_get_constraintdef(oid) = 'CHECK ((total_seconds >= 0))'
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: non-negative CHECK constraints mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 4. Assert status CHECK constraint using IS DISTINCT FROM (Fail open guard)
    SELECT pg_get_constraintdef(oid) INTO v_def
    FROM pg_constraint
    WHERE conrelid = 'public.student_study_sessions'::regclass AND conname = 'ck_study_sessions_status';

    IF (v_def IS DISTINCT FROM 'CHECK (((status)::text = ANY ((ARRAY[''ACTIVE''::character varying, ''DISPLACED''::character varying, ''CLOSED''::character varying, ''PAUSED''::character varying, ''COMPLETED''::character varying, ''EXPIRED''::character varying])::text[])))') THEN
        RAISE EXCEPTION 'Post-migration assertion failed: status CHECK mismatch or missing: %', v_def USING ERRCODE = 'internal_error';
    END IF;

    -- 5. Assert exact FKs on student_study_sessions
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_sessions'::regclass 
          AND c.confrelid = 'public.courses'::regclass 
          AND c.contype = 'f' AND c.confdeltype = 'r' AND c.convalidated
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['course_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_sessions'::regclass 
          AND c.confrelid = 'public.lectures'::regclass 
          AND c.contype = 'f' AND c.confdeltype = 'r' AND c.convalidated
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['lecture_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_sessions'::regclass 
          AND c.confrelid = 'public.students'::regclass 
          AND c.contype = 'f' AND c.confdeltype = 'c' AND c.convalidated
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: FK delete actions mismatch on student_study_sessions' USING ERRCODE = 'internal_error';
    END IF;

    -- 6. Assert student_study_clocks columns, PK, and FKs
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'student_id' AND data_type = 'uuid' AND is_nullable = 'NO')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'active_session_id' AND data_type = 'uuid' AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'active_lecture_id' AND data_type = 'character varying' AND character_maximum_length = 100 AND is_nullable = 'YES')
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'lease_expires_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND column_default IS NULL)
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'last_credited_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND column_default IS NULL)
       OR NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'student_study_clocks' AND column_name = 'updated_at' AND data_type = 'timestamp with time zone' AND is_nullable = 'NO' AND TRIM(column_default) = 'clock_timestamp()')
    THEN
        RAISE EXCEPTION 'Post-migration assertion failed: student_study_clocks columns mismatch' USING ERRCODE = 'internal_error';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_clocks'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_clocks'::regclass 
          AND c.confrelid = 'public.students'::regclass 
          AND c.contype = 'f' AND c.confdeltype = 'c' AND c.convalidated
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_clocks'::regclass 
          AND c.confrelid = 'public.lectures'::regclass 
          AND c.contype = 'f' AND c.confdeltype = 'n' AND c.convalidated
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['active_lecture_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: student_study_clocks PK or base FKs mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 7. Assert composite FK on student_study_clocks
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.student_study_clocks'::regclass 
          AND c.conname = 'fk_study_clocks_active_session_owner'
          AND c.confrelid = 'public.student_study_sessions'::regclass 
          AND c.contype = 'f' 
          AND c.confdeltype = 'n'
          AND c.confdelsetcols = ARRAY[2::smallint]
          AND c.convalidated
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['active_session_id', 'student_id']::text[]
          AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id', 'student_id']::text[]
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: fk_study_clocks_active_session_owner attributes mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 8. Assert tightened indexes on student_study_sessions (key columns, no INCLUDE, validity, predicates)
    IF NOT EXISTS (
        SELECT 1 FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'idx_study_sessions_student_status'
          AND i.indrelid = 'public.student_study_sessions'::regclass
          AND i.indnkeyatts = 2 AND i.indnatts = 2
          AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey[0:i.indnkeyatts-1]) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'status']::text[]
          AND NOT i.indisunique AND i.indisvalid AND i.indpred IS NULL
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: idx_study_sessions_student_status mismatch' USING ERRCODE = 'internal_error';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'idx_study_sessions_student_lecture'
          AND i.indrelid = 'public.student_study_sessions'::regclass
          AND i.indnkeyatts = 2 AND i.indnatts = 2
          AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey[0:i.indnkeyatts-1]) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['student_id', 'lecture_id']::text[]
          AND NOT i.indisunique AND i.indisvalid AND i.indpred IS NULL
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: idx_study_sessions_student_lecture mismatch' USING ERRCODE = 'internal_error';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'idx_study_sessions_expires_at'
          AND i.indrelid = 'public.student_study_sessions'::regclass
          AND i.indnkeyatts = 1 AND i.indnatts = 1
          AND ARRAY(SELECT a.attname::text FROM unnest(i.indkey[0:i.indnkeyatts-1]) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['expires_at']::text[]
          AND pg_get_expr(i.indpred, i.indrelid) = '((status)::text = ''ACTIVE''::text)'
          AND NOT i.indisunique AND i.indisvalid
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: idx_study_sessions_expires_at predicate mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 9. Assert trigger relation and function identity
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_proc p ON p.oid = t.tgfoid
        WHERE n.nspname = 'public' AND c.relname = 'student_daily_activity' 
          AND t.tgname = 'trg_sync_student_daily_minutes'
          AND p.proname = 'sync_student_daily_minutes'
          AND t.tgenabled = 'O'
          AND NOT t.tgisinternal
          AND (t.tgtype & 2) = 2   -- BEFORE
          AND (t.tgtype & 4) = 4   -- INSERT
          AND (t.tgtype & 16) = 16 -- UPDATE
          AND (t.tgtype & 8) = 0   -- NOT DELETE
          AND (t.tgtype & 1) = 1   -- FOR EACH ROW
          AND t.tgfoid = ('public.sync_student_daily_minutes()')::regprocedure
    ) THEN
        RAISE EXCEPTION 'Post-migration assertion failed: trg_sync_student_daily_minutes trigger properties mismatch' USING ERRCODE = 'internal_error';
    END IF;

    -- 10. Assert trigger function body definition & security properties
    SELECT COUNT(*) INTO v_fn_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'sync_student_daily_minutes';

    IF v_fn_count != 1 THEN
        RAISE EXCEPTION 'Post-migration assertion failed: Expected exactly 1 sync_student_daily_minutes function, found %', v_fn_count USING ERRCODE = 'internal_error';
    END IF;

    SELECT md5(regexp_replace(trim(p.prosrc), '\s+', ' ', 'g')) INTO v_hash
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname = 'sync_student_daily_minutes'
      AND p.pronargs = 0
      AND p.prorettype = 'trigger'::regtype
      AND p.provolatile = 'v'
      AND p.prosecdef = false
      AND p.prolang = (SELECT oid FROM pg_language WHERE lanname = 'plpgsql');

    IF (v_hash IS DISTINCT FROM '644b5902680d7b4ea4c38b0554d04b8a') THEN
        RAISE EXCEPTION 'Post-migration assertion failed: sync_student_daily_minutes() body definition mismatch' USING ERRCODE = 'internal_error';
    END IF;

    RAISE NOTICE 'All post-migration assertions verified successfully.';
END $$;
COMMIT;
