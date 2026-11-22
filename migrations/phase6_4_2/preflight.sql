-- ============================================================================
-- Phase 6.4.2: Preflight Schema & Constraint Verification Script
-- Target: PostgreSQL 18.7 (Neon Database: public schema)
-- Idempotent, Read-Only Audit. Aborts on any missing or incompatible object.
-- ============================================================================

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
