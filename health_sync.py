# health_sync.py — PulseGuard Health Connect Bridge
# ─────────────────────────────────────────────────
# Drop this file next to app.py, then in app.py add:
#   from health_sync import health_bp, init_health_db
#   app.register_blueprint(health_bp)
#   init_health_db()
#
# SESSION_USER_KEY must match whatever key your login sets in the Flask session.
# With Flask-Login the current_user is available; we read current_user.id directly.

import datetime
import secrets
import json

from flask import Blueprint, request, jsonify, render_template, session
from flask_login import current_user, login_required
from flask_sqlalchemy import SQLAlchemy

# ── Shared db instance — imported from app.py at init time ─────────────────
# We receive it via init_health_db(db_instance)
_db = None

health_bp = Blueprint("health_sync", __name__)

# ══════════════════════════════════════════════════════════════════════════════
#  MODELS
# ══════════════════════════════════════════════════════════════════════════════

class PhonePairing(_db.__class__ if _db else object):
    """Populated after init_health_db() resolves the real db."""
    pass


# We define models lazily so that the db instance is available.
_models_ready = False
StepsRecord = None
PhonePairing = None


def _define_models(db):
    global StepsRecord, PhonePairing, _models_ready

    class _PhonePairing(db.Model):
        __tablename__ = "phone_pairing"
        id          = db.Column(db.Integer, primary_key=True)
        user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
        pairing_code= db.Column(db.String(8), nullable=False)
        device_name = db.Column(db.String(100))
        paired_at   = db.Column(db.DateTime)
        last_sync   = db.Column(db.DateTime)
        server_url  = db.Column(db.String(200))

    class _StepsRecord(db.Model):
        __tablename__ = "steps_record"
        id          = db.Column(db.Integer, primary_key=True)
        user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        date        = db.Column(db.String(10), nullable=False)   # YYYY-MM-DD
        steps       = db.Column(db.Integer, nullable=False)
        calories    = db.Column(db.Float)
        heart_rate  = db.Column(db.Float)
        resting_hr  = db.Column(db.Float)
        distance_m  = db.Column(db.Float)
        synced_at   = db.Column(db.DateTime, default=datetime.datetime.utcnow)
        raw_json    = db.Column(db.Text)  # full payload from phone

        __table_args__ = (db.UniqueConstraint("user_id", "date", name="uq_user_date"),)

    StepsRecord  = _StepsRecord
    PhonePairing = _PhonePairing
    _models_ready = True


def init_health_db(db=None):
    """Call this from app.py after db is created:  init_health_db(db)"""
    global _db
    if db is None:
        try:
            from app import db as app_db
            db = app_db
        except ImportError:
            raise RuntimeError("Pass db instance to init_health_db(db)")
    _db = db
    _define_models(db)
    # Flask-SQLAlchemy 3.x: db.app is set when SQLAlchemy(app) was called
    flask_app = getattr(db, "app", None)
    if flask_app is not None:
        with flask_app.app_context():
            db.create_all()
    # If no app attribute (extension pattern), tables will be created
    # on first request inside an existing app_context.


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_or_create_pairing(user_id):
    pair = PhonePairing.query.filter_by(user_id=user_id).first()
    if not pair:
        pair = PhonePairing(
            user_id=user_id,
            pairing_code=secrets.token_hex(4).upper()   # 8-char hex
        )
        _db.session.add(pair)
        _db.session.commit()
    return pair


def _upsert_steps(user_id, date_str, payload):
    rec = StepsRecord.query.filter_by(user_id=user_id, date=date_str).first()
    if rec is None:
        rec = StepsRecord(user_id=user_id, date=date_str)
        _db.session.add(rec)
    rec.steps      = int(payload.get("steps", rec.steps or 0))
    rec.calories   = payload.get("calories")
    rec.heart_rate = payload.get("heart_rate")
    rec.resting_hr = payload.get("resting_hr")
    rec.distance_m = payload.get("distance_m")
    rec.synced_at  = datetime.datetime.utcnow()
    rec.raw_json   = json.dumps(payload)
    _db.session.commit()
    return rec


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTE
# ══════════════════════════════════════════════════════════════════════════════

@health_bp.route("/connect-phone")
@login_required
def connect_phone_page():
    pair = _get_or_create_pairing(current_user.id)
    return render_template("connect_phone.html", pairing=pair)


# ══════════════════════════════════════════════════════════════════════════════
#  API — called by the Android app
# ══════════════════════════════════════════════════════════════════════════════

@health_bp.route("/api/phone/pair", methods=["POST"])
def phone_pair():
    """Android sends pairing code + device name to register itself."""
    d    = request.json or {}
    code = (d.get("pairing_code") or "").strip().upper()
    if not code:
        return jsonify({"error": "pairing_code required"}), 400

    pair = PhonePairing.query.filter_by(pairing_code=code).first()
    if not pair:
        return jsonify({"error": "Invalid pairing code"}), 403

    pair.device_name = d.get("device_name", "Android Phone")
    pair.paired_at   = datetime.datetime.utcnow()
    _db.session.commit()
    return jsonify({"status": "paired", "user_id": pair.user_id})


@health_bp.route("/api/phone/sync", methods=["POST"])
def phone_sync():
    """Android POSTs health data. Auth via pairing_code in header or body."""
    code = (request.headers.get("X-Pairing-Code")
            or (request.json or {}).get("pairing_code", "")).strip().upper()

    pair = PhonePairing.query.filter_by(pairing_code=code).first()
    if not pair:
        return jsonify({"error": "Unauthorised — invalid pairing code"}), 403

    d        = request.json or {}
    date_str = d.get("date") or datetime.date.today().isoformat()
    rec      = _upsert_steps(pair.user_id, date_str, d)

    pair.last_sync = datetime.datetime.utcnow()
    _db.session.commit()

    return jsonify({
        "status":   "ok",
        "date":     rec.date,
        "steps":    rec.steps,
        "calories": rec.calories,
        "synced_at": rec.synced_at.isoformat()
    })


# ══════════════════════════════════════════════════════════════════════════════
#  API — called by the browser dashboard
# ══════════════════════════════════════════════════════════════════════════════

@health_bp.route("/api/steps/today")
@login_required
def steps_today():
    today = datetime.date.today().isoformat()
    rec   = StepsRecord.query.filter_by(user_id=current_user.id, date=today).first()
    pair  = PhonePairing.query.filter_by(user_id=current_user.id).first()
    return jsonify({
        "date":       today,
        "steps":      rec.steps      if rec else None,
        "calories":   rec.calories   if rec else None,
        "heart_rate": rec.heart_rate if rec else None,
        "resting_hr": rec.resting_hr if rec else None,
        "distance_m": rec.distance_m if rec else None,
        "synced_at":  rec.synced_at.isoformat() if rec else None,
        "paired":     pair is not None and pair.paired_at is not None,
        "last_sync":  pair.last_sync.isoformat() if (pair and pair.last_sync) else None,
    })


@health_bp.route("/api/steps/week")
@login_required
def steps_week():
    today  = datetime.date.today()
    days   = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    recs   = {r.date: r for r in StepsRecord.query.filter(
                  StepsRecord.user_id == current_user.id,
                  StepsRecord.date.in_(days)
              ).all()}
    result = []
    for d in days:
        r = recs.get(d)
        result.append({
            "date":  d,
            "steps": r.steps if r else 0,
            "day":   datetime.date.fromisoformat(d).strftime("%a")
        })
    return jsonify({"week": result})


@health_bp.route("/api/phone/status")
@login_required
def phone_status():
    pair = PhonePairing.query.filter_by(user_id=current_user.id).first()
    if not pair:
        return jsonify({"paired": False})
    return jsonify({
        "paired":      pair.paired_at is not None,
        "device_name": pair.device_name,
        "paired_at":   pair.paired_at.isoformat() if pair.paired_at else None,
        "last_sync":   pair.last_sync.isoformat()  if pair.last_sync  else None,
        "pairing_code": pair.pairing_code,
    })
