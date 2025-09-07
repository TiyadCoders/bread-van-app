from App.database import db

class Stop (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer)
    street_name = db.Column(db.String(255), nullable=False)
    scheduled_date = db.Column(db.String(27), nullable=False)
    created_at = db.Column(db.String(27), nullable=False)
    is_complete = db.Column(db.Boolean, nullable=False, default=False)
