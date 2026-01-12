# cat > app / routes / main.py << "EOF"
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models import DailyEntry
import logging

# Setup logging
logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


def calculate_streaks(user_id):
    """
    Izračunava current streak i longest streak za korisnika.
    Streak = uzastopni dani s barem jednim završenim ritualom (jutro ili večer).
    """
    entries = (
        DailyEntry.query.filter_by(user_id=user_id)
        .filter(
            (DailyEntry.morning_completed_at.isnot(None))
            | (DailyEntry.evening_completed_at.isnot(None))
        )
        .order_by(DailyEntry.date.desc())
        .all()
    )

    if not entries:
        return {"current_streak": 0, "longest_streak": 0}

    # Sortiraj od najnovijeg prema najstarijem
    dates = [entry.date for entry in entries]

    # Izračunaj current streak
    current_streak = 0
    today = date.today()

    # Provjeri je li današnji ili jučerašnji dan popunjen
    if dates[0] == today or dates[0] == today - timedelta(days=1):
        current_streak = 1
        last_date = dates[0]

        for entry_date in dates[1:]:
            expected_date = last_date - timedelta(days=1)
            if entry_date == expected_date:
                current_streak += 1
                last_date = entry_date
            else:
                break

    # Izračunaj longest streak
    longest_streak = 0
    temp_streak = 1

    for i in range(len(dates) - 1):
        if dates[i] - dates[i + 1] == timedelta(days=1):
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1

    longest_streak = max(longest_streak, temp_streak)

    return {"current_streak": current_streak, "longest_streak": longest_streak}


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    return redirect(url_for("auth.login"))


@main_bp.route("/morning", methods=["GET", "POST"])
@login_required
def morning():
    today = date.today()
    entry = DailyEntry.query.filter_by(user_id=current_user.id, date=today).first()

    if entry and entry.is_morning_complete:
        flash("Jutarnji ritual već završen!", "info")
        return redirect(url_for("main.feed"))

    if request.method == "POST":
        energy = int(request.form.get("energy"))
        intent = request.form.get("intent")

        logger.info(f"Morning ritual: user_id={current_user.id}, date={today}, energy={energy}")

        if not entry:
            entry = DailyEntry(user_id=current_user.id, date=today)
            logger.info(f"Creating new entry for user {current_user.id} on {today}")

        entry.morning_energy = energy
        entry.morning_intent = intent
        entry.morning_completed_at = datetime.utcnow()

        db.session.add(entry)
        db.session.commit()

        logger.info(f"Saved morning entry: id={entry.id}, user={current_user.id}, date={entry.date}")
        flash("Jutarnji ritual završen! ✅", "success")
        return redirect(url_for("main.feed"))

    return render_template("morning.html")


@main_bp.route("/evening", methods=["GET", "POST"])
@login_required
def evening():
    today = date.today()
    entry = DailyEntry.query.filter_by(user_id=current_user.id, date=today).first()

    if entry and entry.is_evening_complete:
        flash("Večernji ritual već završen!", "info")
        return redirect(url_for("main.feed"))

    if request.method == "POST":
        wins = {
            "posao": request.form.get("win_posao", ""),
            "zdravlje": request.form.get("win_zdravlje", ""),
            "odnosi": request.form.get("win_odnosi", ""),
            "financije": request.form.get("win_financije", ""),
            "rast": request.form.get("win_rast", ""),
        }
        reflection = request.form.get("reflection")

        logger.info(f"Evening ritual: user_id={current_user.id}, date={today}")

        if not entry:
            entry = DailyEntry(user_id=current_user.id, date=today)
            logger.info(f"Creating new entry for user {current_user.id} on {today}")

        entry.evening_wins = wins
        entry.evening_reflection = reflection
        entry.evening_completed_at = datetime.utcnow()

        db.session.add(entry)
        db.session.commit()

        logger.info(f"Saved evening entry: id={entry.id}, user={current_user.id}, date={entry.date}")
        flash("Večernji ritual završen! 🌙", "success")
        return redirect(url_for("main.feed"))

    return render_template("evening.html")


@main_bp.route("/feed")
@login_required
def feed():
    logger.info(f"Feed accessed by user_id={current_user.id}, email={current_user.email}")

    # Paginacija
    page = request.args.get("page", 1, type=int)
    per_page = 15

    # Query za entries s paginacijom
    pagination = (
        DailyEntry.query.filter_by(user_id=current_user.id)
        .order_by(DailyEntry.date.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    entries = pagination.items

    # Izračunaj streaks
    streaks = calculate_streaks(current_user.id)

    logger.info(f"Found {len(entries)} entries for user {current_user.id} (page {page})")

    return render_template(
        "feed.html",
        entries=entries,
        streaks=streaks,
        pagination=pagination,
        page=page,
    )


@main_bp.route("/insights")
@login_required
def insights():
    from datetime import timedelta
    from sqlalchemy import func

    # Dohvati periode (7, 30, 90 dana)
    period = request.args.get("period", 30, type=int)
    period_ago = date.today() - timedelta(days=period)

    entries = (
        DailyEntry.query.filter(
            DailyEntry.user_id == current_user.id, DailyEntry.date >= period_ago
        )
        .order_by(DailyEntry.date.asc())
        .all()
    )

    # Statistika
    total_days = len(entries)
    avg_energy = (
        sum([e.morning_energy for e in entries if e.morning_energy]) / total_days
        if total_days > 0
        else 0
    )

    # Broji stupce
    pillar_counts = {"posao": 0, "zdravlje": 0, "odnosi": 0, "financije": 0, "rast": 0}

    for entry in entries:
        if entry.evening_wins:
            for pillar, value in entry.evening_wins.items():
                if value and value.strip():
                    pillar_counts[pillar] += 1

    # Pripremi podatke za Chart.js
    # Graf energije kroz vrijeme
    energy_data = {
        "labels": [entry.date.strftime("%d.%m") for entry in entries],
        "values": [entry.morning_energy if entry.morning_energy else 0 for entry in entries],
    }

    # Graf aktivnosti stupova (cumulative)
    pillar_activity = {
        "posao": [],
        "zdravlje": [],
        "odnosi": [],
        "financije": [],
        "rast": [],
    }

    cumulative_counts = {"posao": 0, "zdravlje": 0, "odnosi": 0, "financije": 0, "rast": 0}

    for entry in entries:
        if entry.evening_wins:
            for pillar in pillar_activity.keys():
                if entry.evening_wins.get(pillar, "").strip():
                    cumulative_counts[pillar] += 1
        for pillar in pillar_activity.keys():
            pillar_activity[pillar].append(cumulative_counts[pillar])

    # Streaks
    streaks = calculate_streaks(current_user.id)

    # Completion rate
    complete_days = sum(
        1 for e in entries if e.is_morning_complete and e.is_evening_complete
    )
    completion_rate = (complete_days / total_days * 100) if total_days > 0 else 0

    return render_template(
        "insights.html",
        total_days=total_days,
        avg_energy=round(avg_energy, 1),
        pillar_counts=pillar_counts,
        energy_data=energy_data,
        pillar_activity=pillar_activity,
        period=period,
        streaks=streaks,
        completion_rate=round(completion_rate, 1),
        complete_days=complete_days,
    )


@main_bp.route("/health")
def health():
    """Health check endpoint - vidi status aplikacije i baze"""
    try:
        from app.models import User
        # Provjeri DB konekciju
        db.session.execute(db.text('SELECT 1'))
        user_count = User.query.count()
        entries_count = DailyEntry.query.count()

        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'user_count': user_count,
            'entries_count': entries_count,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route("/debug/me")
@login_required
def debug_me():
    """Debug - prikaži info o trenutnom korisniku i njegovim podacima"""
    entries = DailyEntry.query.filter_by(user_id=current_user.id).all()

    return jsonify({
        'current_user': {
            'id': current_user.id,
            'email': current_user.email,
            'timezone': current_user.timezone,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None
        },
        'entries': {
            'total': len(entries),
            'data': [
                {
                    'id': e.id,
                    'date': str(e.date),
                    'morning_complete': e.is_morning_complete,
                    'evening_complete': e.is_evening_complete,
                    'morning_energy': e.morning_energy,
                    'morning_intent': e.morning_intent[:50] + '...' if e.morning_intent and len(e.morning_intent) > 50 else e.morning_intent,
                    'wins': e.evening_wins,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                }
                for e in entries
            ]
        }
    })


@main_bp.route("/debug/all-users")
def debug_all_users():
    """Debug - prikaži sve korisnike i njihove entry count (samo za development!)"""
    from app.models import User

    users = User.query.all()
    users_data = []

    for user in users:
        entry_count = DailyEntry.query.filter_by(user_id=user.id).count()
        users_data.append({
            'id': user.id,
            'email': user.email,
            'entry_count': entry_count,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })

    return jsonify({
        'total_users': len(users),
        'users': users_data
    })


@main_bp.route("/export")
@login_required
def export_data():
    import csv
    from io import StringIO
    from flask import make_response

    entries = (
        DailyEntry.query.filter_by(user_id=current_user.id)
        .order_by(DailyEntry.date)
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Datum",
            "Energija",
            "Namjera",
            "Posao",
            "Zdravlje",
            "Odnosi",
            "Financije",
            "Rast",
            "Refleksija",
        ]
    )

    # Data
    for entry in entries:
        wins = entry.evening_wins or {}
        writer.writerow(
            [
                entry.date,
                entry.morning_energy or "",
                entry.morning_intent or "",
                wins.get("posao", ""),
                wins.get("zdravlje", ""),
                wins.get("odnosi", ""),
                wins.get("financije", ""),
                wins.get("rast", ""),
                entry.evening_reflection or "",
            ]
        )

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = (
        f"attachment; filename=success_stacker_{date.today()}.csv"
    )
    response.headers["Content-Type"] = "text/csv; charset=utf-8"

    return response


@main_bp.route("/entry/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = DailyEntry.query.get_or_404(entry_id)

    # Provjeri da korisnik može uređivati samo svoje unose
    if entry.user_id != current_user.id:
        flash("Nemate dozvolu za uređivanje ovog unosa!", "error")
        return redirect(url_for("main.feed"))

    if request.method == "POST":
        # Ažuriraj jutarnje podatke ako postoje
        if request.form.get("energy"):
            entry.morning_energy = int(request.form.get("energy"))
            entry.morning_intent = request.form.get("intent")
            if not entry.morning_completed_at:
                entry.morning_completed_at = datetime.utcnow()

        # Ažuriraj večernje podatke ako postoje
        if request.form.get("reflection") is not None:
            entry.evening_wins = {
                "posao": request.form.get("win_posao", ""),
                "zdravlje": request.form.get("win_zdravlje", ""),
                "odnosi": request.form.get("win_odnosi", ""),
                "financije": request.form.get("win_financije", ""),
                "rast": request.form.get("win_rast", ""),
            }
            entry.evening_reflection = request.form.get("reflection")
            if not entry.evening_completed_at:
                entry.evening_completed_at = datetime.utcnow()

        db.session.commit()
        logger.info(f"Entry {entry_id} updated by user {current_user.id}")
        flash("Unos uspješno ažuriran!", "success")
        return redirect(url_for("main.feed"))

    return render_template("edit_entry.html", entry=entry)


@main_bp.route("/entry/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = DailyEntry.query.get_or_404(entry_id)

    # Provjeri da korisnik može brisati samo svoje unose
    if entry.user_id != current_user.id:
        flash("Nemate dozvolu za brisanje ovog unosa!", "error")
        return redirect(url_for("main.feed"))

    entry_date = entry.date
    db.session.delete(entry)
    db.session.commit()

    logger.info(f"Entry {entry_id} (date: {entry_date}) deleted by user {current_user.id}")
    flash(f"Unos za {entry_date.strftime('%d.%m.%Y')} je obrisan.", "success")
    return redirect(url_for("main.feed"))


@main_bp.route("/calendar")
@login_required
def calendar():
    """Calendar view sa heatmap vizualizacijom zadnjih 365 dana"""
    # Dohvati sve unose zadnjih 365 dana
    year_ago = date.today() - timedelta(days=365)

    entries = (
        DailyEntry.query.filter_by(user_id=current_user.id)
        .filter(DailyEntry.date >= year_ago)
        .all()
    )

    # Kreiraj dictionary za brzo traženje
    entries_by_date = {}
    for entry in entries:
        # Izračunaj "score" za dan (0-3)
        score = 0
        if entry.is_morning_complete:
            score += 1
        if entry.is_evening_complete:
            score += 1
        if entry.evening_wins:
            filled_wins = sum(1 for v in entry.evening_wins.values() if v and v.strip())
            if filled_wins >= 3:  # Bonus ako su popunjena bar 3 stupca
                score += 1

        entries_by_date[str(entry.date)] = {
            "score": min(score, 3),  # Max 3
            "morning_complete": entry.is_morning_complete,
            "evening_complete": entry.is_evening_complete,
            "morning_energy": entry.morning_energy,
        }

    # Izračunaj streaks
    streaks = calculate_streaks(current_user.id)

    # Statistika
    total_entries = len(entries)
    complete_days = sum(
        1 for e in entries if e.is_morning_complete and e.is_evening_complete
    )

    return render_template(
        "calendar.html",
        entries_by_date=entries_by_date,
        streaks=streaks,
        total_entries=total_entries,
        complete_days=complete_days,
    )
