"""
achievement_service.py - Student Engagement and Achievement System
Part of Phase 6.5.4 for Ziglag Institute Math & Science Portal.

Evaluates student engagement and academic achievements strictly and authoritatively
from verified database records across four foundational categories:
  Category A: Learning Progress (1, 5, 10, 25, 50 lessons completed)
  Category B: Study Consistency (1 active day, 3-day, 7-day, 14-day, 30-day study streaks)
  Category C: Study Commitment (30 minutes, 5 hours, 10 hours, 25 hours verified study time)
  Category D: Diagnostic Improvement (1st diagnostic, score improvement, 70% threshold, 90% threshold)

Ensures 100% idempotency, zero duplicate achievement awarding, and zero schema migrations.
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import text


# Milestone Definitions
MILESTONE_DEFINITIONS = [
    # -------------------------------------------------------------------------
    # Category A: Learning Progress (5 milestones)
    # -------------------------------------------------------------------------
    {
        'id': 'first_lesson',
        'title': 'First Step',
        'description': 'Completed your first published video lecture.',
        'category': 'learning_progress',
        'category_label': 'Learning Progress',
        'icon': '🌱',
        'target_progress': 1,
        'unit': 'lesson'
    },
    {
        'id': 'lessons_5',
        'title': 'Dedicated Scholar',
        'description': 'Completed 5 published curriculum lessons.',
        'category': 'learning_progress',
        'category_label': 'Learning Progress',
        'icon': '📚',
        'target_progress': 5,
        'unit': 'lessons'
    },
    {
        'id': 'lessons_10',
        'title': 'Knowledge Seeker',
        'description': 'Completed 10 published curriculum lessons.',
        'category': 'learning_progress',
        'category_label': 'Learning Progress',
        'icon': '📖',
        'target_progress': 10,
        'unit': 'lessons'
    },
    {
        'id': 'lessons_25',
        'title': 'Curriculum Voyager',
        'description': 'Completed 25 published curriculum lessons.',
        'category': 'learning_progress',
        'category_label': 'Learning Progress',
        'icon': '🧭',
        'target_progress': 25,
        'unit': 'lessons'
    },
    {
        'id': 'lessons_50',
        'title': 'Mastery Trailblazer',
        'description': 'Completed 50 published curriculum lessons.',
        'category': 'learning_progress',
        'category_label': 'Learning Progress',
        'icon': '🎓',
        'target_progress': 50,
        'unit': 'lessons'
    },

    # -------------------------------------------------------------------------
    # Category B: Study Consistency (5 milestones)
    # -------------------------------------------------------------------------
    {
        'id': 'first_active_day',
        'title': 'Day One',
        'description': 'Logged your first active day of authenticated learning.',
        'category': 'study_consistency',
        'category_label': 'Study Consistency',
        'icon': '☀️',
        'target_progress': 1,
        'unit': 'day'
    },
    {
        'id': 'streak_3',
        'title': 'Habit Builder',
        'description': 'Achieved a continuous 3-day study streak.',
        'category': 'study_consistency',
        'category_label': 'Study Consistency',
        'icon': '🔥',
        'target_progress': 3,
        'unit': 'days'
    },
    {
        'id': 'streak_7',
        'title': 'Weekly Warrior',
        'description': 'Achieved a continuous 7-day study streak.',
        'category': 'study_consistency',
        'category_label': 'Study Consistency',
        'icon': '⚡',
        'target_progress': 7,
        'unit': 'days'
    },
    {
        'id': 'streak_14',
        'title': 'Fortnight Focus',
        'description': 'Achieved a continuous 14-day study streak.',
        'category': 'study_consistency',
        'category_label': 'Study Consistency',
        'icon': '🛡️',
        'target_progress': 14,
        'unit': 'days'
    },
    {
        'id': 'streak_30',
        'title': 'Monthly Champion',
        'description': 'Achieved a continuous 30-day study streak.',
        'category': 'study_consistency',
        'category_label': 'Study Consistency',
        'icon': '👑',
        'target_progress': 30,
        'unit': 'days'
    },

    # -------------------------------------------------------------------------
    # Category C: Study Commitment (4 milestones)
    # -------------------------------------------------------------------------
    {
        'id': 'study_30m',
        'title': 'Study Starter',
        'description': 'Accumulated 30 minutes of verified active study time.',
        'category': 'study_commitment',
        'category_label': 'Study Commitment',
        'icon': '⏱️',
        'target_progress': 1800,  # 30 minutes in seconds
        'unit': 'minutes'
    },
    {
        'id': 'study_5h',
        'title': 'Deep Diver',
        'description': 'Accumulated 5 hours of verified active study time.',
        'category': 'study_commitment',
        'category_label': 'Study Commitment',
        'icon': '⏳',
        'target_progress': 18000,  # 5 hours in seconds
        'unit': 'hours'
    },
    {
        'id': 'study_10h',
        'title': 'Ten-Hour Pillar',
        'description': 'Accumulated 10 hours of verified active study time.',
        'category': 'study_commitment',
        'category_label': 'Study Commitment',
        'icon': '🏛️',
        'target_progress': 36000,  # 10 hours in seconds
        'unit': 'hours'
    },
    {
        'id': 'study_25h',
        'title': 'Academic Endurance',
        'description': 'Accumulated 25 hours of verified active study time.',
        'category': 'study_commitment',
        'category_label': 'Study Commitment',
        'icon': '🏔️',
        'target_progress': 90000,  # 25 hours in seconds
        'unit': 'hours'
    },

    # -------------------------------------------------------------------------
    # Category D: Diagnostic Improvement (4 milestones)
    # -------------------------------------------------------------------------
    {
        'id': 'first_diagnostic',
        'title': 'Diagnostic Explorer',
        'description': 'Completed your first comprehensive diagnostic assessment.',
        'category': 'diagnostic_improvement',
        'category_label': 'Diagnostic Improvement',
        'icon': '🎯',
        'target_progress': 1,
        'unit': 'assessment'
    },
    {
        'id': 'improved_diagnostic',
        'title': 'Ascending Score',
        'description': 'Exceeded your baseline score on a subsequent diagnostic attempt.',
        'category': 'diagnostic_improvement',
        'category_label': 'Diagnostic Improvement',
        'icon': '📈',
        'target_progress': 1,
        'unit': 'improvement'
    },
    {
        'id': 'diagnostic_70',
        'title': 'Silver Standard',
        'description': 'Scored 70% or higher on a diagnostic assessment.',
        'category': 'diagnostic_improvement',
        'category_label': 'Diagnostic Improvement',
        'icon': '🥈',
        'target_progress': 70,
        'unit': 'percent'
    },
    {
        'id': 'diagnostic_90',
        'title': 'Gold Distinction',
        'description': 'Scored 90% or higher on a diagnostic assessment.',
        'category': 'diagnostic_improvement',
        'category_label': 'Diagnostic Improvement',
        'icon': '🥇',
        'target_progress': 90,
        'unit': 'percent'
    }
]


def _format_time_progress(current_sec, target_sec):
    """Formats seconds into friendly human-readable strings."""
    def _sec_to_str(s):
        if s < 3600:
            m = s // 60
            return f"{m}m"
        h = s // 3600
        m = (s % 3600) // 60
        if m > 0:
            return f"{h}h {m}m"
        return f"{h}h"
    return f"{_sec_to_str(current_sec)} / {_sec_to_str(target_sec)}"


def get_student_achievements(db_session, student_id):
    """
    Evaluates all 18 milestones across 4 categories for the specified student.
    Uses strictly authoritative database queries.
    Returns:
      {
        'summary': { 'total': 18, 'earned': N, 'unearned': 18-N, 'completion_percentage': P, 'next_milestone': ... },
        'categories': [ ... ],
        'achievements': [ ... ],
        'recent_unlocked': [ ... ]
      }
    """
    sid = str(student_id)

    # =========================================================================
    # 1. CATEGORY A: LEARNING PROGRESS
    # =========================================================================
    # Query all completed published lectures ordered chronologically by first_completed_at
    lesson_query = text("""
        SELECT lp.first_completed_at, lp.lecture_id, l.title
        FROM student_lesson_progress lp
        JOIN lectures l ON lp.lecture_id = l.id
        WHERE lp.student_id = :student_id
          AND lp.is_completed = true
          AND lp.first_completed_at IS NOT NULL
          AND l.is_published = true
        ORDER BY lp.first_completed_at ASC;
    """)
    completed_lessons = db_session.execute(lesson_query, {'student_id': sid}).fetchall()
    total_lessons = len(completed_lessons)

    # =========================================================================
    # 2. CATEGORY B: STUDY CONSISTENCY (Active days & streaks)
    # =========================================================================
    # Query distinct active dates and chronological rows from student_daily_activity
    activity_query = text("""
        SELECT activity_date, COALESCE(seconds_spent, minutes_spent * 60, 0) AS sec,
               COALESCE(minutes_spent, 0) AS mins, lessons_completed, xp_earned,
               questions_practiced, last_active_at
        FROM student_daily_activity
        WHERE student_id = :student_id
          AND (COALESCE(seconds_spent, 0) > 0 
               OR COALESCE(minutes_spent, 0) > 0
               OR xp_earned > 0 
               OR lessons_completed > 0 
               OR questions_practiced > 0)
        ORDER BY activity_date ASC;
    """)
    activity_rows = db_session.execute(activity_query, {'student_id': sid}).fetchall()

    active_dates = sorted(list({r.activity_date for r in activity_rows}))
    total_active_days = len(active_dates)

    # Compute streak progression and track dates when streak targets were reached
    streak_milestones_dates = {3: None, 7: None, 14: None, 30: None}
    max_streak_achieved = 0

    if active_dates:
        running_streak = 1
        max_streak_achieved = 1

        for i in range(1, len(active_dates)):
            if active_dates[i] == active_dates[i - 1] + timedelta(days=1):
                running_streak += 1
                if running_streak > max_streak_achieved:
                    max_streak_achieved = running_streak
                for st in [3, 7, 14, 30]:
                    if running_streak >= st and streak_milestones_dates[st] is None:
                        streak_milestones_dates[st] = active_dates[i].isoformat()
            else:
                running_streak = 1

    first_active_date_str = active_dates[0].isoformat() if active_dates else None

    # =========================================================================
    # 3. CATEGORY C: STUDY COMMITMENT (Verified Study Time)
    # =========================================================================
    # Cumulative study time chronologically
    time_milestones_dates = {1800: None, 18000: None, 36000: None, 90000: None}
    total_study_seconds = 0

    for row in activity_rows:
        sec = row.sec or 0
        total_study_seconds += sec
        for target_sec in [1800, 18000, 36000, 90000]:
            if total_study_seconds >= target_sec and time_milestones_dates[target_sec] is None:
                if row.last_active_at:
                    time_milestones_dates[target_sec] = row.last_active_at.isoformat()
                else:
                    time_milestones_dates[target_sec] = row.activity_date.isoformat()

    # =========================================================================
    # 4. CATEGORY D: DIAGNOSTIC IMPROVEMENT
    # =========================================================================
    diag_query = text("""
        SELECT attempt_number, score, max_score, percentage, completed_at
        FROM student_diagnostic_history
        WHERE student_id = :student_id
        ORDER BY attempt_number ASC, completed_at ASC;
    """)
    diag_rows = db_session.execute(diag_query, {'student_id': sid}).fetchall()
    total_diag_attempts = len(diag_rows)

    first_diag_date = diag_rows[0].completed_at.isoformat() if total_diag_attempts > 0 and diag_rows[0].completed_at else None
    
    improved_diag_earned = False
    improved_diag_date = None
    baseline_pct = None
    highest_diag_pct = 0.0

    diag_70_date = None
    diag_90_date = None

    if total_diag_attempts > 0:
        baseline_pct = float(diag_rows[0].percentage)
        for idx, d in enumerate(diag_rows):
            pct = float(d.percentage or 0.0)
            if pct > highest_diag_pct:
                highest_diag_pct = pct

            if idx > 0 and baseline_pct is not None and pct > baseline_pct:
                if not improved_diag_earned:
                    improved_diag_earned = True
                    improved_diag_date = d.completed_at.isoformat() if d.completed_at else None

            if pct >= 70.0 and diag_70_date is None:
                diag_70_date = d.completed_at.isoformat() if d.completed_at else None

            if pct >= 90.0 and diag_90_date is None:
                diag_90_date = d.completed_at.isoformat() if d.completed_at else None

    # =========================================================================
    # 5. ASSEMBLE ALL 18 MILESTONES WITH PROGRESS & EARNED STATUS
    # =========================================================================
    achievements = []

    for defn in MILESTONE_DEFINITIONS:
        m_id = defn['id']
        category = defn['category']
        target = defn['target_progress']

        is_earned = False
        earned_at = None
        current = 0
        formatted_prog = ""

        # Category A: Learning Progress
        if m_id == 'first_lesson':
            current = min(total_lessons, 1)
            is_earned = total_lessons >= 1
            if is_earned and completed_lessons:
                earned_at = completed_lessons[0].first_completed_at.isoformat() if completed_lessons[0].first_completed_at else None
            formatted_prog = f"{current} / {target} lesson"

        elif m_id == 'lessons_5':
            current = min(total_lessons, 5)
            is_earned = total_lessons >= 5
            if is_earned and len(completed_lessons) >= 5:
                earned_at = completed_lessons[4].first_completed_at.isoformat() if completed_lessons[4].first_completed_at else None
            formatted_prog = f"{current} / {target} lessons"

        elif m_id == 'lessons_10':
            current = min(total_lessons, 10)
            is_earned = total_lessons >= 10
            if is_earned and len(completed_lessons) >= 10:
                earned_at = completed_lessons[9].first_completed_at.isoformat() if completed_lessons[9].first_completed_at else None
            formatted_prog = f"{current} / {target} lessons"

        elif m_id == 'lessons_25':
            current = min(total_lessons, 25)
            is_earned = total_lessons >= 25
            if is_earned and len(completed_lessons) >= 25:
                earned_at = completed_lessons[24].first_completed_at.isoformat() if completed_lessons[24].first_completed_at else None
            formatted_prog = f"{current} / {target} lessons"

        elif m_id == 'lessons_50':
            current = min(total_lessons, 50)
            is_earned = total_lessons >= 50
            if is_earned and len(completed_lessons) >= 50:
                earned_at = completed_lessons[49].first_completed_at.isoformat() if completed_lessons[49].first_completed_at else None
            formatted_prog = f"{current} / {target} lessons"

        # Category B: Study Consistency
        elif m_id == 'first_active_day':
            current = min(total_active_days, 1)
            is_earned = total_active_days >= 1
            earned_at = first_active_date_str if is_earned else None
            formatted_prog = f"{current} / {target} day"

        elif m_id in ('streak_3', 'streak_7', 'streak_14', 'streak_30'):
            current = min(max_streak_achieved, target)
            is_earned = max_streak_achieved >= target
            earned_at = streak_milestones_dates.get(target) if is_earned else None
            formatted_prog = f"{current} / {target} days"

        # Category C: Study Commitment
        elif m_id in ('study_30m', 'study_5h', 'study_10h', 'study_25h'):
            current = min(total_study_seconds, target)
            is_earned = total_study_seconds >= target
            earned_at = time_milestones_dates.get(target) if is_earned else None
            formatted_prog = _format_time_progress(current, target)

        # Category D: Diagnostic Improvement
        elif m_id == 'first_diagnostic':
            current = min(total_diag_attempts, 1)
            is_earned = total_diag_attempts >= 1
            earned_at = first_diag_date if is_earned else None
            formatted_prog = f"{current} / {target} assessment"

        elif m_id == 'improved_diagnostic':
            current = 1 if improved_diag_earned else 0
            is_earned = improved_diag_earned
            earned_at = improved_diag_date if is_earned else None
            if is_earned:
                formatted_prog = "Score improved"
            elif total_diag_attempts == 0:
                formatted_prog = "No assessment yet"
            elif total_diag_attempts == 1:
                formatted_prog = f"Baseline: {int(round(baseline_pct))}% (Attempt 2 needed)"
            else:
                formatted_prog = f"Highest: {int(round(highest_diag_pct))}% vs Base {int(round(baseline_pct))}%"

        elif m_id == 'diagnostic_70':
            current = min(int(round(highest_diag_pct)), 70)
            is_earned = highest_diag_pct >= 70.0
            earned_at = diag_70_date if is_earned else None
            formatted_prog = f"{current}% / 70%"

        elif m_id == 'diagnostic_90':
            current = min(int(round(highest_diag_pct)), 90)
            is_earned = highest_diag_pct >= 90.0
            earned_at = diag_90_date if is_earned else None
            formatted_prog = f"{current}% / 90%"

        # Progress percentage
        if target > 0:
            if m_id == 'improved_diagnostic':
                prog_pct = 100 if is_earned else (50 if total_diag_attempts >= 1 else 0)
            else:
                prog_pct = int(round((min(current, target) / float(target)) * 100))
        else:
            prog_pct = 100 if is_earned else 0

        achievements.append({
            'id': m_id,
            'title': defn['title'],
            'description': defn['description'],
            'category': category,
            'category_label': defn['category_label'],
            'icon': defn['icon'],
            'target_progress': target,
            'current_progress': current,
            'progress_percentage': prog_pct,
            'is_earned': is_earned,
            'earned_at': earned_at,
            'unit': defn['unit'],
            'formatted_progress': formatted_prog
        })

    # Summary calculations
    total_count = len(achievements)
    earned_count = sum(1 for a in achievements if a['is_earned'])
    unearned_count = total_count - earned_count
    completion_percentage = int(round((earned_count / float(total_count)) * 100)) if total_count > 0 else 0

    # Find the next closest milestone to unlock
    unearned_milestones = [a for a in achievements if not a['is_earned']]
    next_milestone = None
    if unearned_milestones:
        # Sort by progress percentage descending, then by target progress ascending
        unearned_sorted = sorted(
            unearned_milestones,
            key=lambda x: (x['progress_percentage'], -x['target_progress']),
            reverse=True
        )
        next_milestone = unearned_sorted[0]

    # Category summaries
    category_keys = [
        ('learning_progress', 'Learning Progress'),
        ('study_consistency', 'Study Consistency'),
        ('study_commitment', 'Study Commitment'),
        ('diagnostic_improvement', 'Diagnostic Improvement')
    ]
    categories = []
    for cat_id, cat_label in category_keys:
        cat_achievements = [a for a in achievements if a['category'] == cat_id]
        cat_total = len(cat_achievements)
        cat_earned = sum(1 for a in cat_achievements if a['is_earned'])
        categories.append({
            'id': cat_id,
            'label': cat_label,
            'total': cat_total,
            'earned': cat_earned,
            'percentage': int(round((cat_earned / float(cat_total)) * 100)) if cat_total > 0 else 0
        })

    # Recently unlocked (up to 4, sorted by earned_at desc)
    earned_list = [a for a in achievements if a['is_earned'] and a['earned_at']]
    recent_unlocked = sorted(
        earned_list,
        key=lambda x: x['earned_at'] or '',
        reverse=True
    )[:4]

    return {
        'summary': {
            'total': total_count,
            'earned': earned_count,
            'unearned': unearned_count,
            'completion_percentage': completion_percentage,
            'next_milestone': next_milestone
        },
        'categories': categories,
        'achievements': achievements,
        'recent_unlocked': recent_unlocked
    }
