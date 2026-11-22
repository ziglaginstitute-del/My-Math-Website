-- ============================================================================
-- Phase 6.4.2: Study-Time Tracking Database Rollback (Final Destructive SQL)
-- Target: PostgreSQL 18.7 (Neon Database: public schema)
-- Features: Complete Dependency Audit Across All 4 Relations, Exact Identity Verification,
--           Ownership-Guided, Preserves Pre-Existing Compatible Objects, Non-Cascading,
--           Comprehensive Baseline Re-Assertion
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- STEP 1: PRE-ROLLBACK OWNERSHIP & DEPENDENCY VALIDATION
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_ext_fks INTEGER;
    v_fk_details TEXT;
    v_col_fks INTEGER;
    v_col_fk_details TEXT;
    v_views INTEGER;
    v_view_names TEXT;
    v_extra_triggers INTEGER;
    v_trig_names TEXT;
    v_proc_deps INTEGER;
    v_proc_dep_names TEXT;
    v_prosrc_refs INTEGER;
    v_prosrc_names TEXT;
    v_unexpected_rules INTEGER;
    v_rule_names TEXT;
    v_unexpected_indexes INTEGER;
    v_unexpected_checks INTEGER;
    v_obj_names TEXT;
BEGIN
    -- 1. Ownership metadata verification: Refuse rollback if ownership table is missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = '_migration_phase6_4_2_ownership'
    ) THEN
        RAISE EXCEPTION 'Rollback Blocked: Migration ownership table public._migration_phase6_4_2_ownership not found. Ownership cannot be established.'
            USING ERRCODE = 'object_not_in_prerequisite_state';
    END IF;

    -- Check if any external foreign key references _migration_phase6_4_2_ownership
    SELECT COUNT(*), string_agg(c.conrelid::regclass::text || '.' || c.conname, '; ')
    INTO v_ext_fks, v_fk_details
    FROM pg_constraint c
    WHERE c.confrelid = 'public._migration_phase6_4_2_ownership'::regclass;

    IF v_ext_fks > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: Foreign key(s) reference _migration_phase6_4_2_ownership: %', v_fk_details
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    -- 2. Foreign keys referencing study tables (excluding the internal fk_study_clocks_active_session_owner)
    SELECT COUNT(*), string_agg(c.conrelid::regclass::text || '.' || c.conname, '; ')
    INTO v_ext_fks, v_fk_details
    FROM pg_constraint c
    WHERE c.confrelid IN (
        'public.student_study_sessions'::regclass,
        'public.student_study_clocks'::regclass
    )
    AND NOT (
        c.conrelid = 'public.student_study_clocks'::regclass 
        AND c.conname = 'fk_study_clocks_active_session_owner'
        AND c.confrelid = 'public.student_study_sessions'::regclass
        AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['active_session_id', 'student_id']::text[]
        AND ARRAY(SELECT a.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id', 'student_id']::text[]
        AND c.confdeltype = 'n'
        AND c.confdelsetcols = ARRAY[2::smallint]
    );

    IF v_ext_fks > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: Unexpected foreign key(s) reference study tables: %', v_fk_details
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    -- 3. External foreign keys referencing seconds_spent on student_daily_activity or student_lesson_progress
    SELECT COUNT(*), string_agg(c.conrelid::regclass::text || '.' || c.conname || ' -> ' || c.confrelid::regclass::text || '(' || a.attname || ')', '; ')
    INTO v_col_fks, v_col_fk_details
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = ANY(c.confkey)
    WHERE c.confrelid IN ('public.student_daily_activity'::regclass, 'public.student_lesson_progress'::regclass)
      AND c.contype = 'f'
      AND a.attname = 'seconds_spent';

    IF v_col_fks > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: External foreign key(s) reference seconds_spent: %', v_col_fk_details
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    -- 4. Unexpected rewrite rules across all affected relations
    SELECT COUNT(*), string_agg(c.relname || '.' || r.rulename, '; ')
    INTO v_unexpected_rules, v_rule_names
    FROM pg_rewrite r
    JOIN pg_class c ON c.oid = r.ev_class
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('student_study_sessions', 'student_study_clocks', 'student_daily_activity', 'student_lesson_progress', '_migration_phase6_4_2_ownership')
      AND r.rulename != '_RETURN';

    IF v_unexpected_rules > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: Unexpected rule(s) found on affected tables: %', v_rule_names
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    -- 5. Unexpected triggers across all affected relations
    SELECT COUNT(*), string_agg(c.relname || '.' || t.tgname, '; ')
    INTO v_extra_triggers, v_trig_names
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN ('student_study_sessions', 'student_study_clocks', 'student_daily_activity', 'student_lesson_progress', '_migration_phase6_4_2_ownership')
      AND NOT t.tgisinternal
      AND NOT (
          c.relname = 'student_daily_activity' 
          AND t.tgname = 'trg_sync_student_daily_minutes'
          AND t.tgfoid = ('public.sync_student_daily_minutes()')::regprocedure
      )
      AND NOT (
          c.relname = 'student_lesson_progress'
          AND t.tgname = 'trg_phase6_2_validate_lesson_course'
      );

    IF v_extra_triggers > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: Unexpected trigger(s) found on tracked tables: %', v_trig_names
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    -- 6. Trigger function dependencies (pg_depend catalog check + procedural source text search)
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'sync_student_daily_minutes' AND pronamespace = 'public'::regnamespace) THEN
        SELECT COUNT(*), string_agg(d.classid::regclass::text || ' ' || d.objid::text, '; ')
        INTO v_proc_deps, v_proc_dep_names
        FROM pg_depend d
        WHERE d.refobjid = 'public.sync_student_daily_minutes()'::regprocedure
          AND d.deptype = 'n'
          AND NOT (
              d.classid = 'pg_trigger'::regclass 
              AND d.objid IN (
                  SELECT t.oid FROM pg_trigger t 
                  JOIN pg_class c ON c.oid = t.tgrelid 
                  WHERE c.relnamespace = 'public'::regnamespace
                    AND c.relname = 'student_daily_activity' 
                    AND t.tgname = 'trg_sync_student_daily_minutes'
              )
          );

        IF v_proc_deps > 0 THEN
            RAISE EXCEPTION 'Rollback Blocked: Catalog dependencies found on sync_student_daily_minutes(): %', v_proc_dep_names
                USING ERRCODE = 'dependent_objects_still_exist';
        END IF;

        SELECT COUNT(*), string_agg(n.nspname || '.' || p.proname, '; ')
        INTO v_prosrc_refs, v_prosrc_names
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE p.prosrc ILIKE '%sync_student_daily_minutes%'
          AND p.oid != 'public.sync_student_daily_minutes()'::regprocedure;

        IF v_prosrc_refs > 0 THEN
            RAISE EXCEPTION 'Rollback Blocked: Stored function(s) reference sync_student_daily_minutes in source text: %', v_prosrc_names
                USING ERRCODE = 'dependent_objects_still_exist';
        END IF;
    END IF;

    -- 7. Views and materialized views depending on affected tables
    SELECT COUNT(*), string_agg(n.nspname || '.' || v.relname, '; ')
    INTO v_views, v_view_names
    FROM pg_depend d
    JOIN pg_rewrite r ON r.oid = d.objid
    JOIN pg_class v ON v.oid = r.ev_class
    JOIN pg_namespace n ON n.oid = v.relnamespace
    WHERE d.refobjid IN (
        'public.student_study_sessions'::regclass,
        'public.student_study_clocks'::regclass,
        'public.student_daily_activity'::regclass,
        'public.student_lesson_progress'::regclass,
        'public._migration_phase6_4_2_ownership'::regclass
    )
    AND v.relkind IN ('v', 'm');

    IF v_views > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: View(s) or materialized view(s) depend on affected tables: %', v_view_names
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    -- 8. Unexpected indexes or CHECK constraints on seconds_spent
    SELECT COUNT(*), string_agg(i.relname, '; ')
    INTO v_unexpected_indexes, v_obj_names
    FROM pg_index x
    JOIN pg_class i ON i.oid = x.indexrelid
    JOIN pg_attribute a ON a.attrelid = x.indrelid AND a.attnum = ANY(x.indkey)
    WHERE x.indrelid IN ('public.student_daily_activity'::regclass, 'public.student_lesson_progress'::regclass)
      AND a.attname = 'seconds_spent';

    IF v_unexpected_indexes > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: Unexpected index on seconds_spent: %', v_obj_names
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    SELECT COUNT(*), string_agg(c.conname, '; ')
    INTO v_unexpected_checks, v_obj_names
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
    WHERE c.conrelid IN ('public.student_daily_activity'::regclass, 'public.student_lesson_progress'::regclass)
      AND a.attname = 'seconds_spent'
      AND c.contype = 'c'
      AND c.conname NOT IN ('ck_student_daily_seconds_non_negative', 'chk_lesson_progress_seconds_nonneg');

    IF v_unexpected_checks > 0 THEN
        RAISE EXCEPTION 'Rollback Blocked: Unexpected CHECK constraint on seconds_spent: %', v_obj_names
            USING ERRCODE = 'dependent_objects_still_exist';
    END IF;

    RAISE NOTICE 'Pre-rollback safety & dependency validation passed.';
END $$;

-- ----------------------------------------------------------------------------
-- STEP 2: NON-CASCADING REMOVAL GUIDED EXCLUSIVELY BY OWNERSHIP
-- ----------------------------------------------------------------------------

-- 1. Remove trigger ONLY if created by Phase 6.4.2 and identity is verified
DO $$
DECLARE
    v_trg_oid OID;
    v_fn_oid OID;
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'TRIGGER' AND object_name = 'trg_sync_student_daily_minutes' 
          AND created_by_phase6_4_2 = true
    ) THEN
        SELECT t.oid, t.tgfoid INTO v_trg_oid, v_fn_oid
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'student_daily_activity' AND t.tgname = 'trg_sync_student_daily_minutes';

        IF v_trg_oid IS NOT NULL THEN
            IF v_fn_oid IS DISTINCT FROM ('public.sync_student_daily_minutes()')::regprocedure::oid THEN
                RAISE EXCEPTION 'Rollback Aborted: trg_sync_student_daily_minutes does not point to public.sync_student_daily_minutes(). Collision detected.'
                    USING ERRCODE = 'object_not_in_prerequisite_state';
            END IF;
            DROP TRIGGER trg_sync_student_daily_minutes ON public.student_daily_activity;
            RAISE NOTICE 'Dropped trigger trg_sync_student_daily_minutes (owned by Phase 6.4.2).';
        END IF;
    ELSE
        RAISE NOTICE 'Preserved pre-existing trigger trg_sync_student_daily_minutes.';
    END IF;
END $$;

-- 2. Remove function ONLY if created by Phase 6.4.2 and body hash is verified
DO $$
DECLARE
    v_hash TEXT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'FUNCTION' AND object_name = 'sync_student_daily_minutes()' 
          AND created_by_phase6_4_2 = true
    ) THEN
        IF EXISTS (
            SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.proname = 'sync_student_daily_minutes'
        ) THEN
            SELECT md5(regexp_replace(trim(p.prosrc), '\s+', ' ', 'g')) INTO v_hash
            FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.proname = 'sync_student_daily_minutes'
              AND p.pronargs = 0 AND p.prorettype = 'trigger'::regtype;

            IF (v_hash IS DISTINCT FROM '644b5902680d7b4ea4c38b0554d04b8a') THEN
                RAISE EXCEPTION 'Rollback Aborted: Function public.sync_student_daily_minutes() body does not match Phase 6.4.2 implementation.'
                    USING ERRCODE = 'object_not_in_prerequisite_state';
            END IF;
            DROP FUNCTION public.sync_student_daily_minutes();
            RAISE NOTICE 'Dropped function sync_student_daily_minutes() (owned by Phase 6.4.2).';
        END IF;
    ELSE
        RAISE NOTICE 'Preserved pre-existing function sync_student_daily_minutes().';
    END IF;
END $$;

-- 3. Remove indexes ONLY if created by Phase 6.4.2
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'INDEX' AND object_name = 'idx_study_sessions_expires_at' 
          AND created_by_phase6_4_2 = true
    ) THEN
        DROP INDEX IF EXISTS public.idx_study_sessions_expires_at;
        RAISE NOTICE 'Dropped index idx_study_sessions_expires_at (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing index idx_study_sessions_expires_at.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'INDEX' AND object_name = 'idx_study_sessions_student_lecture' 
          AND created_by_phase6_4_2 = true
    ) THEN
        DROP INDEX IF EXISTS public.idx_study_sessions_student_lecture;
        RAISE NOTICE 'Dropped index idx_study_sessions_student_lecture (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing index idx_study_sessions_student_lecture.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'INDEX' AND object_name = 'idx_study_sessions_student_status' 
          AND created_by_phase6_4_2 = true
    ) THEN
        DROP INDEX IF EXISTS public.idx_study_sessions_student_status;
        RAISE NOTICE 'Dropped index idx_study_sessions_student_status (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing index idx_study_sessions_student_status.';
    END IF;
END $$;

-- 4. Remove study tables ONLY if created by Phase 6.4.2
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'TABLE' AND object_name = 'student_study_clocks' 
          AND created_by_phase6_4_2 = true
    ) THEN
        DROP TABLE IF EXISTS public.student_study_clocks;
        RAISE NOTICE 'Dropped table student_study_clocks (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing table student_study_clocks.';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'TABLE' AND object_name = 'student_study_sessions' 
          AND created_by_phase6_4_2 = true
    ) THEN
        DROP TABLE IF EXISTS public.student_study_sessions;
        RAISE NOTICE 'Dropped table student_study_sessions (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing table student_study_sessions.';
    END IF;
END $$;

-- 5. Remove seconds_spent from student_lesson_progress ONLY if created by Phase 6.4.2
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'CONSTRAINT' AND object_name = 'student_lesson_progress.chk_lesson_progress_seconds_nonneg' 
          AND created_by_phase6_4_2 = true
    ) THEN
        ALTER TABLE public.student_lesson_progress DROP CONSTRAINT IF EXISTS chk_lesson_progress_seconds_nonneg;
        RAISE NOTICE 'Dropped constraint chk_lesson_progress_seconds_nonneg (owned by Phase 6.4.2).';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'COLUMN' AND object_name = 'student_lesson_progress.seconds_spent' 
          AND created_by_phase6_4_2 = true
    ) THEN
        ALTER TABLE public.student_lesson_progress DROP COLUMN IF EXISTS seconds_spent;
        RAISE NOTICE 'Dropped column student_lesson_progress.seconds_spent (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing column student_lesson_progress.seconds_spent.';
    END IF;
END $$;

-- 6. Remove seconds_spent from student_daily_activity ONLY if created by Phase 6.4.2
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'CONSTRAINT' AND object_name = 'student_daily_activity.ck_student_daily_seconds_non_negative' 
          AND created_by_phase6_4_2 = true
    ) THEN
        ALTER TABLE public.student_daily_activity DROP CONSTRAINT IF EXISTS ck_student_daily_seconds_non_negative;
        RAISE NOTICE 'Dropped constraint ck_student_daily_seconds_non_negative (owned by Phase 6.4.2).';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'COLUMN' AND object_name = 'student_daily_activity.seconds_spent' 
          AND created_by_phase6_4_2 = true
    ) THEN
        ALTER TABLE public.student_daily_activity DROP COLUMN IF EXISTS seconds_spent;
        RAISE NOTICE 'Dropped column student_daily_activity.seconds_spent (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing column student_daily_activity.seconds_spent.';
    END IF;
END $$;

-- 7. Remove migration ownership table ONLY IF created by Phase 6.4.2
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public._migration_phase6_4_2_ownership 
        WHERE schema_name = 'public' AND object_type = 'TABLE' AND object_name = '_migration_phase6_4_2_ownership' 
          AND created_by_phase6_4_2 = true
    ) THEN
        DROP TABLE public._migration_phase6_4_2_ownership;
        RAISE NOTICE 'Dropped table _migration_phase6_4_2_ownership (owned by Phase 6.4.2).';
    ELSE
        RAISE NOTICE 'Preserved pre-existing table _migration_phase6_4_2_ownership.';
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- STEP 3: POST-ROLLBACK COMPREHENSIVE BASELINE RE-ASSERTION
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_rec RECORD;
BEGIN
    -- 1. All 7 prerequisite tables must exist
    FOR v_rec IN 
        SELECT unnest(ARRAY[
            'students', 'courses', 'lectures', 'student_enrollments',
            'student_daily_activity', 'student_lesson_progress', 'student_diagnostic_history'
        ]) AS tbl
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = v_rec.tbl) THEN
            RAISE EXCEPTION 'Post-rollback assertion failed: Prerequisite table public.% is missing', v_rec.tbl
                USING ERRCODE = 'internal_error';
        END IF;
    END LOOP;

    -- 2. Verify primary keys on prerequisite tables
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.students'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.courses'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = 'public.lectures'::regclass AND c.contype = 'p'
          AND ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS u(attnum, ord) JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = u.attnum ORDER BY u.ord) = ARRAY['id']::text[]
    ) THEN
        RAISE EXCEPTION 'Post-rollback assertion failed: Core table primary keys missing' USING ERRCODE = 'internal_error';
    END IF;

    -- 3. Verify student_daily_activity baseline columns and integrity
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'student_id'
          AND data_type = 'uuid' AND is_nullable = 'NO'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'activity_date'
          AND data_type = 'date' AND is_nullable = 'NO'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_daily_activity' AND column_name = 'minutes_spent'
          AND data_type = 'integer' AND is_nullable = 'NO'
    ) THEN
        RAISE EXCEPTION 'Post-rollback assertion failed: student_daily_activity baseline columns damaged' USING ERRCODE = 'internal_error';
    END IF;

    -- 4. Verify student_lesson_progress baseline columns
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'student_id'
          AND data_type = 'uuid' AND is_nullable = 'NO'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'course_id'
          AND data_type = 'character varying' AND is_nullable = 'NO'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'student_lesson_progress' AND column_name = 'lecture_id'
          AND data_type = 'character varying' AND is_nullable = 'NO'
    ) THEN
        RAISE EXCEPTION 'Post-rollback assertion failed: student_lesson_progress baseline columns damaged' USING ERRCODE = 'internal_error';
    END IF;

    RAISE NOTICE 'Post-rollback comprehensive baseline re-asserted successfully.';
END $$;

COMMIT;
