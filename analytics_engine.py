"""
analytics_engine.py - Backend Learning Analytics Engine & Recommendation Service
Part of Phase 6.5.2 for Ziglag Institute Math & Science Portal.

Provides:
- Topic-level curriculum mastery aggregation (lectures.topic_category).
- Study habits analytics (14d/30d consistency, attentiveness score, streaks, verified seconds).
- Diagnostic assessment analytics (attempt trajectory, improvement delta, strengths & weaknesses).
- Deterministic personalized recommendation engine (diagnostic-remedial, next lesson, spaced revision).
- Dense chronological daily activity history generation.
"""

import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import text, bindparam


# Topic-to-keyword taxonomy for deterministic semantic alignment
TOPIC_KEYWORDS = {
    'linear algebra': ['algebra', 'equation', 'matrix', 'vector', 'linear', 'simultaneous'],
    'algebra': ['algebra', 'equation', 'polynomial', 'fraction', 'factorisation', 'expansion'],
    'logarithms & indices': ['logarithm', 'indices', 'surd', 'power', 'exponent', 'base'],
    'indices': ['indices', 'surd', 'logarithm', 'power'],
    'number bases': ['base', 'binary', 'conversion', 'place value', 'denary', 'octal', 'hexadecimal'],
    'circle geometry theorems': ['circle', 'geometry', 'theorem', 'arc', 'angle', 'circumference', 'subtended', 'cyclic'],
    'geometry': ['geometry', 'plane', 'circle', 'angle', 'polygon', 'construction', 'bearing'],
    'trigonometry': ['trig', 'sine', 'cosine', 'tangent', 'bearing', 'elevation', 'depression'],
    'calculus': ['calculus', 'derivative', 'integral', 'limit', 'differentiation', 'integration'],
    'mechanics': ['mechanic', 'motion', 'projectile', 'force', 'kinematic', 'velocity', 'acceleration'],
    'physics': ['physics', 'heat', 'electricity', 'wave', 'light', 'expansion', 'field', 'nuclear'],
    'thermal energy & waves': ['thermal', 'heat', 'expansion', 'wave', 'sound', 'propagation'],
    'electricity & magnetism': ['electricity', 'current', 'ohm', 'electrostatic', 'magnetism', 'induction']
}


def matches_topic(lecture_topic, lecture_title, weak_topic):
    """
    Deterministically matches a course lecture against an identified weak topic.
    Returns True if exact match, substring containment, or keyword correlation is detected.
    """
    lt_clean = (lecture_topic or '').strip().lower()
    ltitle_clean = (lecture_title or '').strip().lower()
    wt_clean = (weak_topic or '').strip().lower()

    if not wt_clean:
        return False

    # 1. Exact match
    if lt_clean == wt_clean:
        return True

    # 2. Substring containment
    if lt_clean and (lt_clean in wt_clean or wt_clean in lt_clean):
        return True

    # 3. Direct title match
    if wt_clean in ltitle_clean:
        return True

    # 4. Keyword taxonomy match
    keywords = []
    for k, v in TOPIC_KEYWORDS.items():
        if k in wt_clean or wt_clean in k:
            keywords.extend(v)

    if not keywords:
        keywords = [w for w in re.split(r'[^a-zA-Z0-9]+', wt_clean) if len(w) > 3]

    for kw in set(keywords):
        kw_l = kw.lower()
        if kw_l in lt_clean or kw_l in ltitle_clean:
            return True

    return False


def get_student_topic_mastery(db_session, student_id):
    """
    Stage 1: Calculates server-side topic mastery for a student across all enrolled courses.
    Respects actual course enrollments and excludes unpublished lectures.
    Avoids duplicate lecture counting through DISTINCT aggregation.
    """
    query = text("""
        WITH enrolled_lectures AS (
            SELECT 
                l.id AS lecture_id,
                l.course_id,
                COALESCE(NULLIF(TRIM(l.topic_category), ''), 'General') AS topic_category,
                COALESCE(slp.is_completed, false) AS is_completed
            FROM student_enrollments se
            JOIN courses c ON c.id = se.course_id AND c.is_published = true
            JOIN lectures l ON l.course_id = se.course_id AND l.is_published = true
            LEFT JOIN student_lesson_progress slp 
                ON slp.lecture_id = l.id 
               AND slp.student_id = se.student_id
               AND slp.is_completed = true
            WHERE se.student_id = :student_id
        )
        SELECT 
            topic_category,
            COUNT(DISTINCT lecture_id) AS total_lectures,
            COUNT(DISTINCT CASE WHEN is_completed THEN lecture_id END) AS completed_lectures,
            ROUND(
                (COUNT(DISTINCT CASE WHEN is_completed THEN lecture_id END)::numeric / 
                 NULLIF(COUNT(DISTINCT lecture_id), 0)::numeric) * 100
            )::integer AS percentage,
            ARRAY_AGG(DISTINCT course_id) AS course_ids
        FROM enrolled_lectures
        GROUP BY topic_category
        ORDER BY topic_category ASC;
    """)

    rows = db_session.execute(query, {'student_id': str(student_id)}).fetchall()

    topic_mastery = []
    for row in rows:
        topic_name = row[0]
        total_lec = row[1] or 0
        comp_lec = row[2] or 0
        pct = row[3] if row[3] is not None else 0
        courses = row[4] if isinstance(row[4], list) else []

        topic_mastery.append({
            'topic': topic_name,
            'completed_lectures': comp_lec,
            'total_lectures': total_lec,
            'percentage': pct,
            'course_ids': courses
        })

    return topic_mastery


def get_student_study_habits(db_session, student_id):
    """
    Stage 2: Calculates 14-day and 30-day study consistency indices, daily/weekly verified duration,
    attentiveness score (active_seconds / duration_seconds), and active streaks in Africa/Lagos time.
    Safely avoids division by zero and handles edge cases.
    """
    lagos_tz = ZoneInfo("Africa/Lagos")
    lagos_now = datetime.now(lagos_tz)
    lagos_today = lagos_now.date()

    start_14d = lagos_today - timedelta(days=13)
    start_30d = lagos_today - timedelta(days=29)

    lagos_monday = lagos_today - timedelta(days=lagos_today.weekday())
    lagos_sunday = lagos_monday + timedelta(days=6)

    # 1. 14-day & 30-day consistency from verified activity records
    consistency_query = text("""
        SELECT 
            COUNT(DISTINCT CASE WHEN activity_date >= :start_14d AND (seconds_spent > 0 OR xp_earned > 0 OR lessons_completed > 0 OR questions_practiced > 0) THEN activity_date END) AS active_14d,
            COUNT(DISTINCT CASE WHEN activity_date >= :start_30d AND (seconds_spent > 0 OR xp_earned > 0 OR lessons_completed > 0 OR questions_practiced > 0) THEN activity_date END) AS active_30d
        FROM student_daily_activity
        WHERE student_id = :student_id
          AND activity_date >= :start_30d AND activity_date <= :lagos_today;
    """)
    cons_row = db_session.execute(consistency_query, {
        'student_id': str(student_id),
        'start_14d': start_14d,
        'start_30d': start_30d,
        'lagos_today': lagos_today
    }).fetchone()

    active_14d = (cons_row[0] or 0) if cons_row else 0
    active_30d = (cons_row[1] or 0) if cons_row else 0

    consistency_14d = int(round((active_14d / 14.0) * 100))
    consistency_30d = int(round((active_30d / 30.0) * 100))

    # 2. Daily verified duration (today)
    daily_query = text("""
        SELECT COALESCE(seconds_spent, 0)
        FROM student_daily_activity
        WHERE student_id = :student_id AND activity_date = :lagos_today;
    """)
    today_row = db_session.execute(daily_query, {
        'student_id': str(student_id),
        'lagos_today': lagos_today
    }).fetchone()
    today_seconds = today_row[0] if today_row else 0
    today_minutes = today_seconds // 60

    # 3. Weekly verified duration (Monday to Sunday)
    weekly_query = text("""
        SELECT COALESCE(SUM(seconds_spent), 0)
        FROM student_daily_activity
        WHERE student_id = :student_id 
          AND activity_date >= :monday AND activity_date <= :sunday;
    """)
    weekly_row = db_session.execute(weekly_query, {
        'student_id': str(student_id),
        'monday': lagos_monday,
        'sunday': lagos_sunday
    }).fetchone()
    weekly_seconds = (weekly_row[0] or 0) if weekly_row else 0
    weekly_minutes = weekly_seconds // 60
    weekly_hours = round(weekly_seconds / 3600.0, 1)

    # 4. Attentiveness Score (active_seconds / duration_seconds)
    att_query = text("""
        SELECT 
            COALESCE(SUM(duration_seconds), 0) AS total_duration,
            COALESCE(SUM(LEAST(active_seconds, duration_seconds)), 0) AS total_active,
            COUNT(*) AS total_sessions
        FROM student_study_sessions
        WHERE student_id = :student_id 
          AND duration_seconds > 0 
          AND active_seconds >= 0;
    """)
    att_row = db_session.execute(att_query, {'student_id': str(student_id)}).fetchone()
    total_duration = att_row[0] if att_row else 0
    total_active = att_row[1] if att_row else 0
    total_sessions = att_row[2] if att_row else 0

    if total_duration > 0:
        attentiveness_score = int(round((total_active / float(total_duration)) * 100))
    else:
        attentiveness_score = 100  # Default 100% when no duration recorded

    # 5. Streak Tracking (Current and Longest historical in Lagos calendar dates)
    streak_query = text("""
        SELECT activity_date
        FROM student_daily_activity
        WHERE student_id = :student_id
          AND (seconds_spent > 0 OR xp_earned > 0 OR lessons_completed > 0 OR questions_practiced > 0)
        ORDER BY activity_date ASC;
    """)
    streak_rows = db_session.execute(streak_query, {'student_id': str(student_id)}).fetchall()
    active_dates = {r[0] for r in streak_rows}

    current_streak = 0
    lagos_yesterday = lagos_today - timedelta(days=1)
    if lagos_today in active_dates:
        current_streak = 1
        chk = lagos_today - timedelta(days=1)
        while chk in active_dates:
            current_streak += 1
            chk -= timedelta(days=1)
    elif lagos_yesterday in active_dates:
        current_streak = 1
        chk = lagos_yesterday - timedelta(days=1)
        while chk in active_dates:
            current_streak += 1
            chk -= timedelta(days=1)

    longest_streak = 0
    sorted_dates = sorted(active_dates)
    if sorted_dates:
        running = 1
        max_streak = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                running += 1
                if running > max_streak:
                    max_streak = running
            elif sorted_dates[i] > sorted_dates[i - 1] + timedelta(days=1):
                running = 1
        longest_streak = max(max_streak, current_streak)

    return {
        'consistency_index_14d': consistency_14d,
        'consistency_index_30d': consistency_30d,
        'active_days_14d': active_14d,
        'active_days_30d': active_30d,
        'total_days_14d': 14,
        'total_days_30d': 30,
        'today_verified_seconds': today_seconds,
        'today_verified_minutes': today_minutes,
        'weekly_verified_seconds': weekly_seconds,
        'weekly_verified_minutes': weekly_minutes,
        'weekly_verified_hours': weekly_hours,
        'attentiveness_score': attentiveness_score,
        'total_session_duration_seconds': total_duration,
        'total_session_active_seconds': total_active,
        'recorded_sessions_count': total_sessions,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'is_today_active': lagos_today in active_dates
    }


def get_student_diagnostic_analytics(db_session, student_id):
    """
    Stage 3: Evaluates diagnostic assessment trajectory, baseline/latest percentages,
    assessment-over-assessment improvement, and granular strengths/weaknesses from topic_breakdown JSONB.
    Inspects actual JSONB payload and gracefully handles malformed/missing fields.
    """
    query = text("""
        SELECT 
            id, subject, attempt_number, score, max_score, percentage,
            topic_breakdown, recommendations, time_spent_seconds, completed_at
        FROM student_diagnostic_history
        WHERE student_id = :student_id
        ORDER BY attempt_number ASC, completed_at ASC;
    """)
    rows = db_session.execute(query, {'student_id': str(student_id)}).fetchall()

    if not rows:
        return {
            'has_taken_diagnostic': False,
            'total_attempts': 0,
            'status': 'NOT_EVALUATED',
            'baseline_percentage': None,
            'latest_percentage': None,
            'improvement_percentage': 0,
            'baseline_attempt': None,
            'latest_attempt': None,
            'strengths': [],
            'weaknesses': [],
            'attempts_history': []
        }

    attempts_history = []
    for r in rows:
        attempts_history.append({
            'attempt_number': r[2],
            'subject': r[1],
            'score': r[3],
            'max_score': r[4],
            'percentage': r[5],
            'time_spent_seconds': r[8] or 0,
            'completed_at': r[9].isoformat() if r[9] else None
        })

    baseline = attempts_history[0]
    latest = attempts_history[-1]

    baseline_pct = baseline['percentage']
    latest_pct = latest['percentage']
    improvement_pct = latest_pct - baseline_pct

    # Granular topic breakdown from latest attempt
    latest_raw = rows[-1]
    topic_breakdown_raw = latest_raw[6] if isinstance(latest_raw[6], dict) else {}
    recommendations_raw = latest_raw[7] if isinstance(latest_raw[7], list) else []

    strengths = []
    weaknesses = []

    for topic_name, t_val in topic_breakdown_raw.items():
        if isinstance(t_val, dict):
            pct = t_val.get('percentage')
            needs_rem = t_val.get('needs_remediation')
            is_corr = t_val.get('is_correct')
            score = t_val.get('score', 0)
            max_s = t_val.get('max_score', 1)

            if pct is None and max_s > 0:
                pct = int(round((score / float(max_s)) * 100))
            elif pct is None:
                pct = 100 if is_corr else 0

            is_weak = (needs_rem is True) or (is_corr is False) or (pct < 70)
            item = {
                'topic': topic_name,
                'score': score,
                'max_score': max_s,
                'percentage': pct,
                'is_correct': bool(is_corr if is_corr is not None else (pct >= 70)),
                'needs_remediation': is_weak
            }
            if is_weak:
                weaknesses.append(item)
            else:
                strengths.append(item)
        elif isinstance(t_val, (int, float)):
            pct = int(round(t_val))
            is_weak = (pct < 70)
            item = {
                'topic': topic_name,
                'score': 1 if pct >= 70 else 0,
                'max_score': 1,
                'percentage': pct,
                'is_correct': not is_weak,
                'needs_remediation': is_weak
            }
            if is_weak:
                weaknesses.append(item)
            else:
                strengths.append(item)

    status = 'MASTERED' if latest_pct >= 80 else ('PROFICIENT' if latest_pct >= 50 else 'REMEDIATION_REQUIRED')

    return {
        'has_taken_diagnostic': True,
        'total_attempts': len(attempts_history),
        'status': status,
        'baseline_percentage': baseline_pct,
        'latest_percentage': latest_pct,
        'improvement_percentage': improvement_pct,
        'baseline_attempt': baseline,
        'latest_attempt': latest,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'recommendations': recommendations_raw,
        'attempts_history': attempts_history
    }


def get_student_recommendations(db_session, student_id, intended_exam=None, limit=5):
    """
    Stage 4: Deterministic recommendation engine.
    Priority hierarchy:
    1. Diagnostic weaknesses requiring remediation.
    2. Uncompleted lessons relevant to identified weak topics.
    3. Next uncompleted lecture in student's enrolled/target syllabus course.
    4. Spaced revision suggestion based on previous activity.
    Excludes completed lessons as new tasks, only recommends published lectures,
    and deduplicates by (course_id, lecture_id).
    """
    # 1. Fetch student's enrolled courses and target course
    enrolled_courses_query = text("""
        SELECT se.course_id, c.title, se.is_pinned
        FROM student_enrollments se
        JOIN courses c ON c.id = se.course_id AND c.is_published = true
        WHERE se.student_id = :student_id
        ORDER BY se.is_pinned DESC, se.enrolled_at ASC;
    """)
    enrolled_courses = db_session.execute(enrolled_courses_query, {'student_id': str(student_id)}).fetchall()
    enrolled_cids = [r[0] for r in enrolled_courses]

    # Fallback to general exam course if student has no enrollments yet
    if not enrolled_cids:
        from app import resolve_exam_course
        fallback_cid = resolve_exam_course(intended_exam)
        enrolled_cids = [fallback_cid]

    # 2. Fetch completed lecture IDs
    completed_query = text("""
        SELECT lecture_id
        FROM student_lesson_progress
        WHERE student_id = :student_id AND is_completed = true;
    """)
    comp_rows = db_session.execute(completed_query, {'student_id': str(student_id)}).fetchall()
    completed_lecture_ids = {r[0] for r in comp_rows}

    # 3. Fetch all published lectures for the student's enrolled courses
    lectures_query = text("""
        SELECT 
            l.id, l.course_id, l.title, l.topic_category, l.duration, l.order_index, c.title AS course_title
        FROM lectures l
        JOIN courses c ON c.id = l.course_id AND c.is_published = true
        WHERE l.course_id = ANY(:cids) AND l.is_published = true
        ORDER BY l.course_id, l.order_index ASC;
    """)
    published_lectures = db_session.execute(lectures_query, {'cids': enrolled_cids}).fetchall()

    recommendations = []
    seen_lecture_ids = set()

    # 4. Diagnostic Weaknesses Matching (Priority 1 & 2)
    diag_analytics = get_student_diagnostic_analytics(db_session, student_id)
    weak_topics = [w['topic'] for w in diag_analytics.get('weaknesses', []) if isinstance(w, dict) and 'topic' in w]

    for wt in weak_topics:
        for lec in published_lectures:
            lid = lec[0]
            cid = lec[1]
            title = lec[2]
            topic = lec[3] or 'Core Topic'
            dur = lec[4] or '25 mins'
            course_title = lec[6]

            if lid in completed_lecture_ids or lid in seen_lecture_ids:
                continue

            if matches_topic(topic, title, wt):
                seen_lecture_ids.add(lid)
                recommendations.append({
                    'id': f"rec_diag_{lid}",
                    'priority': 1,
                    'priority_label': 'High Priority Remediation',
                    'type': 'DIAGNOSTIC_REMEDIAL',
                    'topic': wt,
                    'course_id': cid,
                    'course_title': course_title,
                    'lecture_id': lid,
                    'lecture_title': title,
                    'duration': dur,
                    'badge': 'Remedial Priority',
                    'reason': f"Diagnostic Checkpoint identified '{wt}' as requiring targeted remediation.",
                    'action_url': f"course-view.html?id={cid}&lec={lid}"
                })
                if len(recommendations) >= limit:
                    break
        if len(recommendations) >= limit:
            break

    # 5. Next Uncompleted Syllabus Lecture (Priority 3)
    if len(recommendations) < limit:
        for lec in published_lectures:
            lid = lec[0]
            cid = lec[1]
            title = lec[2]
            topic = lec[3] or 'General'
            dur = lec[4] or '25 mins'
            course_title = lec[6]

            if lid in completed_lecture_ids or lid in seen_lecture_ids:
                continue

            seen_lecture_ids.add(lid)
            recommendations.append({
                'id': f"rec_next_{lid}",
                'priority': 2,
                'priority_label': 'Recommended Next Lesson',
                'type': 'SYLLABUS_CONTINUATION',
                'topic': topic,
                'course_id': cid,
                'course_title': course_title,
                'lecture_id': lid,
                'lecture_title': title,
                'duration': dur,
                'badge': 'Syllabus Milestone',
                'reason': f"Continue your structured curriculum progression in '{course_title}'.",
                'action_url': f"course-view.html?id={cid}&lec={lid}"
            })

            if len(recommendations) >= limit:
                break

    # 6. Spaced Revision Suggestion (Priority 4)
    # If student has completed lessons, recommend reviewing an earlier completed lecture (> 5 days ago)
    if len(recommendations) < limit and completed_lecture_ids:
        rev_query = text("""
            SELECT 
                l.id, l.course_id, l.title, l.topic_category, l.duration, c.title AS course_title
            FROM student_lesson_progress slp
            JOIN lectures l ON l.id = slp.lecture_id AND l.is_published = true
            JOIN courses c ON c.id = l.course_id AND c.is_published = true
            WHERE slp.student_id = :student_id 
              AND slp.is_completed = true
              AND l.id NOT IN :seen_lids
            ORDER BY slp.last_accessed_at ASC, slp.view_count ASC
            LIMIT 1;
        """).bindparams(
            bindparam("seen_lids", expanding=True)
        )
        seen_list = list(seen_lecture_ids) if seen_lecture_ids else ["__none__"]
        rev_row = db_session.execute(rev_query, {
            'student_id': str(student_id),
            'seen_lids': seen_list
        }).fetchone()

        if rev_row:
            seen_lecture_ids.add(rev_row[0])
            recommendations.append({
                'id': f"rec_rev_{rev_row[0]}",
                'priority': 3,
                'priority_label': 'Spaced Revision',
                'type': 'SPACED_REVISION',
                'topic': rev_row[3] or 'Revision',
                'course_id': rev_row[1],
                'course_title': rev_row[5],
                'lecture_id': rev_row[0],
                'lecture_title': rev_row[2],
                'duration': rev_row[4] or '15 mins',
                'badge': 'Reinforce Concept',
                'reason': "Reinforce long-term retention of core mathematical theorems through spaced review.",
                'action_url': f"course-view.html?id={rev_row[1]}&lec={rev_row[0]}"
            })

    return recommendations


def get_student_activity_history_data(db_session, student_id, days=30):
    """
    Stage 5: Generates a dense chronological history of daily learning activity
    over the requested number of Africa/Lagos calendar days.
    """
    if days is None or days < 1 or days > 90:
        raise ValueError("Parameter 'days' must be an integer between 1 and 90.")

    lagos_tz = ZoneInfo("Africa/Lagos")
    lagos_now = datetime.now(lagos_tz)
    lagos_today = lagos_now.date()
    start_date = lagos_today - timedelta(days=days - 1)

    query = text("""
        SELECT 
            activity_date, seconds_spent, minutes_spent, xp_earned, 
            lessons_completed, questions_practiced
        FROM student_daily_activity
        WHERE student_id = :student_id 
          AND activity_date >= :start_date AND activity_date <= :lagos_today
        ORDER BY activity_date ASC;
    """)
    rows = db_session.execute(query, {
        'student_id': str(student_id),
        'start_date': start_date,
        'lagos_today': lagos_today
    }).fetchall()

    activity_map = {r[0]: r for r in rows}

    day_abbrs = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    history = []
    total_seconds = 0
    total_xp = 0
    total_lessons = 0
    total_questions = 0
    total_active_days = 0

    for i in range(days):
        cur_date = start_date + timedelta(days=i)
        r = activity_map.get(cur_date)

        if r:
            sec = r[1] or 0
            mins = r[2] or (sec // 60)
            xp = r[3] or 0
            lessons = r[4] or 0
            questions = r[5] or 0
            is_active = (sec > 0 or xp > 0 or lessons > 0 or questions > 0)
        else:
            sec = 0
            mins = 0
            xp = 0
            lessons = 0
            questions = 0
            is_active = False

        if is_active:
            total_active_days += 1

        total_seconds += sec
        total_xp += xp
        total_lessons += lessons
        total_questions += questions

        history.append({
            'date': cur_date.isoformat(),
            'day_name': day_abbrs[cur_date.weekday()],
            'seconds_spent': sec,
            'minutes_spent': mins,
            'xp_earned': xp,
            'lessons_completed': lessons,
            'questions_practiced': questions,
            'is_active': is_active
        })

    return {
        'success': True,
        'days_requested': days,
        'start_date': start_date.isoformat(),
        'end_date': lagos_today.isoformat(),
        'total_active_days': total_active_days,
        'total_seconds_spent': total_seconds,
        'total_minutes_spent': total_seconds // 60,
        'total_hours_spent': round(total_seconds / 3600.0, 1),
        'total_xp_earned': total_xp,
        'total_lessons_completed': total_lessons,
        'total_questions_practiced': total_questions,
        'history': history
    }
