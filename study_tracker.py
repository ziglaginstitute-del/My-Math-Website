import json
import uuid
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from flask import request, jsonify, Response, session
from sqlalchemy import text
from app import db, app

def build_heartbeat_response(payload, status_code=200):
    """
    Serializes payload to raw JSON string with consistent key ordering,
    returning both the raw string and the Flask Response object.
    Ensures byte-for-byte fidelity for idempotent duplicate replays.
    """
    raw_body = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    resp = Response(raw_body, status=status_code, mimetype='application/json')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return raw_body, resp

def apply_lagos_daily_activity_increment(db_session, student_id, credited_seconds, now, schema='public'):
    """
    Increments student_daily_activity.seconds_spent with Africa/Lagos calendar
    midnight boundary splitting.
    """
    if credited_seconds <= 0:
        return

    lagos_tz = ZoneInfo("Africa/Lagos")
    interval_start = now - timedelta(seconds=credited_seconds)
    start_lagos = interval_start.astimezone(lagos_tz)
    end_lagos = now.astimezone(lagos_tz)
    date_start = start_lagos.date()
    date_end = end_lagos.date()

    prefix = f"{schema}." if schema else ""

    if date_start == date_end:
        db_session.execute(text(f"""
            INSERT INTO {prefix}student_daily_activity (
                id, student_id, activity_date, seconds_spent, minutes_spent, lessons_completed, questions_practiced, xp_earned, last_active_at
            )
            VALUES (gen_random_uuid(), :sid, :dt, :sec, FLOOR(:sec / 60), 0, 0, 0, :now)
            ON CONFLICT (student_id, activity_date)
            DO UPDATE SET
                seconds_spent = {prefix}student_daily_activity.seconds_spent + EXCLUDED.seconds_spent,
                last_active_at = :now;
        """), {'sid': str(student_id), 'dt': date_start, 'sec': credited_seconds, 'now': now})
    else:
        midnight_boundary = datetime(date_end.year, date_end.month, date_end.day, 0, 0, 0, tzinfo=lagos_tz)
        sec_day1 = int((midnight_boundary - start_lagos).total_seconds())
        sec_day2 = int((end_lagos - midnight_boundary).total_seconds())

        if sec_day1 > 0:
            db_session.execute(text(f"""
                INSERT INTO {prefix}student_daily_activity (
                    id, student_id, activity_date, seconds_spent, minutes_spent, lessons_completed, questions_practiced, xp_earned, last_active_at
                )
                VALUES (gen_random_uuid(), :sid, :dt, :sec, FLOOR(:sec / 60), 0, 0, 0, :now)
                ON CONFLICT (student_id, activity_date)
                DO UPDATE SET
                    seconds_spent = {prefix}student_daily_activity.seconds_spent + EXCLUDED.seconds_spent,
                    last_active_at = :now;
            """), {'sid': str(student_id), 'dt': date_start, 'sec': sec_day1, 'now': now})
        if sec_day2 > 0:
            db_session.execute(text(f"""
                INSERT INTO {prefix}student_daily_activity (
                    id, student_id, activity_date, seconds_spent, minutes_spent, lessons_completed, questions_practiced, xp_earned, last_active_at
                )
                VALUES (gen_random_uuid(), :sid, :dt, :sec, FLOOR(:sec / 60), 0, 0, 0, :now)
                ON CONFLICT (student_id, activity_date)
                DO UPDATE SET
                    seconds_spent = {prefix}student_daily_activity.seconds_spent + EXCLUDED.seconds_spent,
                    last_active_at = :now;
            """), {'sid': str(student_id), 'dt': date_end, 'sec': sec_day2, 'now': now})


def handle_heartbeat_transaction(
    student_id, session_token, course_id, lecture_id, seq, payload_hash,
    is_active, event_type, credited_candidate=30, user_notice=None, schema='public'
):
    """
    Executes the complete study-time heartbeat lifecycle within a single atomic PostgreSQL transaction.
    Enforces the strict, verified order:
      1. Clock Lock (Primary Mutex)
      2. Calling Session Lock & Ownership Verification
      3. State Validation (CLOSED -> 409, Invalid -> 400)
      4. Duplicate Retry Check (Replay Stored Response, 0 DB writes)
      5. Monotonic Sequence Check
      6. Path 7: Explicit Takeover (ACTIVE/DISPLACED only, 0 credit)
      7. Displaced Session Safeguard (0 credit, clock unmutated)
      8. Path 2: Natural Lease Resumption (Eligible ACTIVE session only, 0 credit)
      9. Strict Non-Owner Barrier (Displaced, 0 credit, clock unmutated)
     10. Verified Owner Accounting (Paths 1, 3, 4, 5) with Progress-before-Daily lock order.
    """
    prefix = f"{schema}." if schema else ""

    sess = db.session() if callable(db.session) else db.session
    tx = sess.begin_nested() if sess.in_transaction() else sess.begin()
    with tx:
        # --------------------------------------------------------------------
        # 1. LOCK CLOCK FIRST (Deterministic Primary Mutex)
        # --------------------------------------------------------------------
        clock = db.session.execute(text(f"""
            SELECT student_id, active_session_id, active_lecture_id, lease_expires_at, last_credited_at
            FROM {prefix}student_study_clocks
            WHERE student_id = :sid
            FOR UPDATE;
        """), {'sid': str(student_id)}).fetchone()

        if not clock:
            db.session.execute(text(f"""
                INSERT INTO {prefix}student_study_clocks (student_id, lease_expires_at, last_credited_at, updated_at)
                VALUES (:sid, clock_timestamp() - interval '1 hour', clock_timestamp() - interval '1 hour', clock_timestamp())
                ON CONFLICT (student_id) DO NOTHING;
            """), {'sid': str(student_id)})
            clock = db.session.execute(text(f"""
                SELECT student_id, active_session_id, active_lecture_id, lease_expires_at, last_credited_at
                FROM {prefix}student_study_clocks WHERE student_id = :sid FOR UPDATE;
            """), {'sid': str(student_id)}).fetchone()

        _, active_session_id, active_lecture_id, lease_expires_at, last_credited_at = clock

        # --------------------------------------------------------------------
        # 2. LOCK CALLING SESSION SECOND & VERIFY OWNERSHIP / BINDING
        # --------------------------------------------------------------------
        calling_session = db.session.execute(text(f"""
            SELECT id, student_id, course_id, lecture_id, status, last_sequence_number, 
                   last_payload_hash, total_seconds, last_response_json
            FROM {prefix}student_study_sessions
            WHERE session_token = :token AND student_id = :sid
            FOR UPDATE;
        """), {'token': str(session_token), 'sid': str(student_id)}).fetchone()

        if not calling_session:
            return build_heartbeat_response({
                "success": False,
                "error": "Invalid session token or student ownership mismatch.",
                "status": "unauthorized"
            }, status_code=403)[1]

        sess_id, _, s_course, s_lecture, s_status, last_seq, last_hash, total_sec, last_json = calling_session

        # Permanent lecture binding check
        if s_course != course_id or s_lecture != lecture_id:
            return build_heartbeat_response({
                "success": False,
                "error": "Lecture binding violation: course_id or lecture_id does not match session.",
                "status": "relational_mismatch"
            }, status_code=400)[1]

        # --------------------------------------------------------------------
        # 3. EXPLICIT SESSION STATUS VALIDATION (FIRST DECISION BRANCH)
        # Invariant: Evaluated BEFORE duplicate replays and takeovers!
        # --------------------------------------------------------------------
        if s_status == 'CLOSED':
            return build_heartbeat_response({
                "success": False,
                "error": "Session is closed and cannot receive heartbeats or replay duplicates.",
                "status": "closed"
            }, status_code=409)[1]

        if s_status not in ('ACTIVE', 'DISPLACED'):
            return build_heartbeat_response({
                "success": False,
                "error": f"Invalid or unsupported session status: '{s_status}'.",
                "status": "invalid_status"
            }, status_code=400)[1]

        # --------------------------------------------------------------------
        # 4. DUPLICATE RETRY CHECK (SECOND DECISION BRANCH)
        # Permitted ONLY for valid ACTIVE or DISPLACED sessions. Zero DB writes.
        # --------------------------------------------------------------------
        if seq == last_seq and payload_hash == last_hash:
            return Response(last_json, status=200, mimetype='application/json')

        # --------------------------------------------------------------------
        # 5. MONOTONIC SEQUENCE CHECK (THIRD DECISION BRANCH)
        # --------------------------------------------------------------------
        if seq <= last_seq:
            return build_heartbeat_response({
                "success": False,
                "error": "Stale or out-of-order sequence number.",
                "status": "stale_sequence"
            }, status_code=400)[1]

        now = db.session.execute(text("SELECT clock_timestamp();")).scalar()
        is_lease_expired = (lease_expires_at is None or lease_expires_at <= now)
        is_current_active = (active_session_id == sess_id)

        # --------------------------------------------------------------------
        # 6. PATH 7: EXPLICIT TAKEOVER (FOURTH DECISION BRANCH)
        # Permitted ONLY for validated ACTIVE or DISPLACED sessions.
        # --------------------------------------------------------------------
        if event_type == 'takeover':
            # Lock previous active session THIRD if exists and differs
            if active_session_id is not None and active_session_id != sess_id:
                db.session.execute(text(f"""
                    UPDATE {prefix}student_study_sessions
                    SET status = 'DISPLACED', ended_at = :now, close_reason = 'PREEMPTED_BY_NEW_TAB'
                    WHERE id = :prev_id;
                """), {'now': now, 'prev_id': str(active_session_id)})

            # Activate incoming session with 0 initial credit
            resp_payload = {
                "success": True, "credited_seconds": 0, "status": "lease_acquired",
                "session_total_seconds": total_sec
            }
            raw_body, response = build_heartbeat_response(resp_payload, status_code=200)

            db.session.execute(text(f"""
                UPDATE {prefix}student_study_sessions
                SET status = 'ACTIVE', last_sequence_number = :seq, last_payload_hash = :hash,
                    last_heartbeat_at = :now, last_credited_seconds = 0, last_response_json = :raw
                WHERE id = :id;
            """), {'seq': seq, 'hash': payload_hash, 'now': now, 'raw': raw_body, 'id': str(sess_id)})

            db.session.execute(text(f"""
                UPDATE {prefix}student_study_clocks
                SET active_session_id = :id, active_lecture_id = :lid,
                    lease_expires_at = :now + interval '35 seconds',
                    last_credited_at = :now, updated_at = :now
                WHERE student_id = :sid;
            """), {'id': str(sess_id), 'lid': lecture_id, 'now': now, 'sid': str(student_id)})

            return response

        # --------------------------------------------------------------------
        # 7. DISPLACED SESSION SAFEGUARD (FIFTH DECISION BRANCH)
        # A DISPLACED session can NEVER reacquire the clock via ordinary heartbeat!
        # Even if the current lease has expired!
        # --------------------------------------------------------------------
        if s_status == 'DISPLACED':
            resp_payload = {
                "success": True, "credited_seconds": 0, "status": "displaced",
                "session_total_seconds": total_sec,
                "message": user_notice or "This session was displaced. Click 'Continue Studying Here' to resume."
            }
            raw_body, response = build_heartbeat_response(resp_payload, status_code=200)

            db.session.execute(text(f"""
                UPDATE {prefix}student_study_sessions
                SET last_sequence_number = :seq, last_payload_hash = :hash,
                    last_heartbeat_at = :now, last_credited_seconds = 0, last_response_json = :raw
                WHERE id = :id;
            """), {'seq': seq, 'hash': payload_hash, 'now': now, 'raw': raw_body, 'id': str(sess_id)})

            # Clock is COMPLETELY UNTOUCHED!
            return response

        # --------------------------------------------------------------------
        # 8. PATH 2: NATURAL LEASE RESUMPTION (SIXTH DECISION BRANCH)
        # Invariants: Calling session MUST be eligible (s_status == 'ACTIVE'),
        # lease must be expired, and calling session must have been last leaseholder.
        # --------------------------------------------------------------------
        if s_status == 'ACTIVE' and is_lease_expired and (is_current_active or active_session_id is None):
            resp_payload = {
                "success": True, "credited_seconds": 0, "status": "lease_acquired",
                "session_total_seconds": total_sec
            }
            raw_body, response = build_heartbeat_response(resp_payload, status_code=200)

            db.session.execute(text(f"""
                UPDATE {prefix}student_study_sessions
                SET status = 'ACTIVE', last_sequence_number = :seq, last_payload_hash = :hash,
                    last_heartbeat_at = :now, last_credited_seconds = 0, last_response_json = :raw
                WHERE id = :id;
            """), {'seq': seq, 'hash': payload_hash, 'now': now, 'raw': raw_body, 'id': str(sess_id)})

            db.session.execute(text(f"""
                UPDATE {prefix}student_study_clocks
                SET active_session_id = :id, active_lecture_id = :lid,
                    lease_expires_at = :now + interval '35 seconds',
                    last_credited_at = :now, updated_at = :now
                WHERE student_id = :sid;
            """), {'id': str(sess_id), 'lid': lecture_id, 'now': now, 'sid': str(student_id)})

            return response

        # --------------------------------------------------------------------
        # 9. STRICT NON-OWNER BARRIER (SEVENTH DECISION BRANCH)
        # If calling session is NOT the current active owner, it CANNOT enter accounting!
        # Catches:
        # A) Non-owner calling ordinary heartbeat while another lease is active (Path 6).
        # B) Non-owner calling ordinary heartbeat while another lease is expired.
        # Session is marked DISPLACED; 0 credit awarded; CLOCK UNTOUCHED!
        # --------------------------------------------------------------------
        if not is_current_active:
            resp_payload = {
                "success": True, "credited_seconds": 0, "status": "displaced",
                "session_total_seconds": total_sec,
                "message": user_notice or "Another study session owns the clock. Click 'Continue Studying Here' to resume."
            }
            raw_body, response = build_heartbeat_response(resp_payload, status_code=200)

            db.session.execute(text(f"""
                UPDATE {prefix}student_study_sessions
                SET status = 'DISPLACED', last_sequence_number = :seq, last_payload_hash = :hash,
                    last_heartbeat_at = :now, last_credited_seconds = 0, last_response_json = :raw
                WHERE id = :id;
            """), {'seq': seq, 'hash': payload_hash, 'now': now, 'raw': raw_body, 'id': str(sess_id)})

            # Clock is COMPLETELY UNTOUCHED!
            return response

        # --------------------------------------------------------------------
        # 10. VERIFIED CURRENT OWNER ACCOUNTING (PATHS 1, 3, 4, 5)
        # MATHEMATICAL INVARIANTS GUARANTEED:
        # 1. s_status == 'ACTIVE'
        # 2. is_current_active == True (sess_id == clock.active_session_id)
        # 3. Clock lease is valid and held by this exact calling session.
        # --------------------------------------------------------------------
        delta_seconds = int(round((now - last_credited_at).total_seconds())) if last_credited_at else 0

        if not is_active:
            # PATH 3: IDLE HEARTBEAT
            credited_seconds = 0
            resp_status = "idle"
            should_renew_lease = False
        elif delta_seconds > 90:
            # PATH 4: STALE HEARTBEAT
            credited_seconds = 0
            resp_status = "stale_reset"
            should_renew_lease = True
        elif delta_seconds > 60:
            # PATH 5: CLAMPED HEARTBEAT
            credited_seconds = 60
            resp_status = "active"
            should_renew_lease = True
        else:
            # PATH 1: STANDARD CREDITED HEARTBEAT
            credited_seconds = max(0, min(delta_seconds, 60))
            resp_status = "active"
            should_renew_lease = True

        # Increments for Credited Intervals (Paths 1, 5)
        # Enforce Global Lock Order: Progress updated FIRST, Daily Activity SECOND
        if credited_seconds > 0:
            # 1. Lesson Progress
            db.session.execute(text(f"""
                INSERT INTO {prefix}student_lesson_progress (
                    id, student_id, course_id, lecture_id, seconds_spent, view_count, is_completed, xp_awarded, last_accessed_at
                )
                VALUES (gen_random_uuid(), :sid, :cid, :lid, :sec, 0, FALSE, 0, :now)
                ON CONFLICT (student_id, lecture_id)
                DO UPDATE SET
                    seconds_spent = {prefix}student_lesson_progress.seconds_spent + EXCLUDED.seconds_spent,
                    last_accessed_at = :now;
            """), {'sid': str(student_id), 'cid': course_id, 'lid': lecture_id, 'sec': credited_seconds, 'now': now})

            # 2. Daily Activity (Africa/Lagos midnight boundary split)
            apply_lagos_daily_activity_increment(db.session, student_id, credited_seconds, now, schema=schema)

            total_sec += credited_seconds

        # Update Calling Session Row
        resp_payload = {
            "success": True, "credited_seconds": credited_seconds,
            "status": resp_status, "session_total_seconds": total_sec
        }
        if user_notice:
            resp_payload["message"] = user_notice

        raw_body, response = build_heartbeat_response(resp_payload, status_code=200)

        db.session.execute(text(f"""
            UPDATE {prefix}student_study_sessions
            SET last_sequence_number = :seq, last_payload_hash = :hash,
                last_heartbeat_at = :now, last_credited_seconds = :sec,
                total_seconds = :tot, last_response_json = :raw
            WHERE id = :id;
        """), {'seq': seq, 'hash': payload_hash, 'now': now, 'sec': credited_seconds, 'tot': total_sec, 'raw': raw_body, 'id': str(sess_id)})

        # Update Clock Row
        lease_update_sql = ":now + interval '35 seconds'" if should_renew_lease else ":now"
        db.session.execute(text(f"""
            UPDATE {prefix}student_study_clocks
            SET lease_expires_at = {lease_update_sql},
                last_credited_at = :now, updated_at = :now
            WHERE student_id = :sid;
        """), {'now': now, 'sid': str(student_id)})

        return response
