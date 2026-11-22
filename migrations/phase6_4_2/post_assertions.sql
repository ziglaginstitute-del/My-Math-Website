-- ============================================================================
-- Phase 6.4.2: Post-Migration Schema & Catalog Assertion Script
-- Target: PostgreSQL 18.7 (Neon Database: public schema)
-- Validates All Target Objects, Precise Definitions, Indexes, Constraints & Status
-- ============================================================================

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
