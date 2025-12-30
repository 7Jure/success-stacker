# cat > app / models / entry.py << "EOF"
from datetime import datetime, date
from app import db


class DailyEntry(db.Model):
    __tablename__ = "daily_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    # Morning
    morning_energy = db.Column(db.Integer)
    morning_intent = db.Column(db.Text)
    morning_completed_at = db.Column(db.DateTime)

    # Evening
    evening_wins = db.Column(db.JSON, default={})
    evening_reflection = db.Column(db.Text)
    evening_completed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "date", name="unique_user_date"),)

    @property
    def is_morning_complete(self):
        return self.morning_completed_at is not None

    @property
    def is_evening_complete(self):
        return self.evening_completed_at is not None


# EOF
