# cat > app / routes / main.py << "EOF"
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import DailyEntry

main_bp = Blueprint("main", __name__)


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

        if not entry:
            entry = DailyEntry(user_id=current_user.id, date=today)

        entry.morning_energy = energy
        entry.morning_intent = intent
        entry.morning_completed_at = datetime.utcnow()

        db.session.add(entry)
        db.session.commit()

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

        if not entry:
            entry = DailyEntry(user_id=current_user.id, date=today)

        entry.evening_wins = wins
        entry.evening_reflection = reflection
        entry.evening_completed_at = datetime.utcnow()

        db.session.add(entry)
        db.session.commit()

        flash("Večernji ritual završen! 🌙", "success")
        return redirect(url_for("main.feed"))

    return render_template("evening.html")


@main_bp.route("/feed")
@login_required
def feed():
    entries = (
        DailyEntry.query.filter_by(user_id=current_user.id)
        .order_by(DailyEntry.date.desc())
        .limit(30)
        .all()
    )

    return render_template("feed.html", entries=entries)


@main_bp.route("/insights")
@login_required
def insights():
    from datetime import timedelta
    from sqlalchemy import func

    # Zadnjih 7 dana
    week_ago = date.today() - timedelta(days=7)

    entries = DailyEntry.query.filter(
        DailyEntry.user_id == current_user.id, DailyEntry.date >= week_ago
    ).all()

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

    return render_template(
        "insights.html",
        total_days=total_days,
        avg_energy=round(avg_energy, 1),
        pillar_counts=pillar_counts,
    )


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
