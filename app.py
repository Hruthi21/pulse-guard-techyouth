from flask import Flask, request, jsonify, render_template
import joblib
from flask_mail import Mail, Message
import numpy as np
import pandas as pd
from flask_cors import CORS
import os
import json
import random
import math
import datetime
from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from apscheduler.schedulers.background import BackgroundScheduler


# ── Twilio ─────────────────────────────────────────────────────────────────
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# ── Gemini AI ───────────────────────────────────────────────────────────────
try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()

# ── Gemini client init ────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
gemini_client  = None
GEMINI_MODEL   = 'gemini-2.0-flash'
GEMINI_SYSTEM  = (
    "You are PulseGuard Health AI, a compassionate and knowledgeable medical AI assistant "
    "specializing in cardiovascular health, integrated into the PulseGuard AI platform. "
    "You help users understand: heart rate, HRV, blood pressure, cholesterol, diabetes, "
    "heart-healthy diets (Mediterranean, DASH), exercise recommendations, stress management, "
    "sleep hygiene, symptoms of heart disease, when to seek emergency care, and general preventive cardiology. "
    "Always: be empathetic, clear, and evidence-based. Use simple language. "
    "Recommend consulting a qualified doctor for serious or personalized medical concerns. "
    "You are NOT a replacement for professional medical advice. "
    "Format responses clearly using bullet points or short paragraphs when helpful. "
    "Keep responses concise but thorough."
)
if GEMINI_AVAILABLE and GEMINI_API_KEY and 'your_gemini' not in GEMINI_API_KEY:
    try:
        gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f'Gemini init error: {e}')
        gemini_client = None

# ── Twilio client init ─────────────────────────────────────────────────────
TWILIO_SID   = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM  = os.getenv('TWILIO_FROM_NUMBER', '')
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if (TWILIO_AVAILABLE and TWILIO_SID and 'your_twilio' not in TWILIO_SID) else None

# ── Emergency contacts from env (with fallback) ────────────────────────────
def get_emergency_contacts():
    contacts = []
    for i in range(1, 6):          # supports up to 5 contacts
        name  = os.getenv(f'EMERGENCY_CONTACT_{i}_NAME')
        phone = os.getenv(f'EMERGENCY_CONTACT_{i}_PHONE')
        if name and phone and 'XXXXXXX' not in phone:
            contacts.append({'name': name, 'phone': phone})
    # Fallback hard-coded if nothing configured
    if not contacts:
        contacts = [
            {'name': 'Family Member', 'phone': None},
            {'name': 'Dr. Ramesh Kumar', 'phone': None},
        ]
    return contacts

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'supersecretkey_pulseguard'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pulseguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    health_info = db.Column(db.Text)
    baseline_hr = db.Column(db.Float, default=70.0)
    relative_name = db.Column(db.String(100))
    relative_phone = db.Column(db.String(20))
    relative_email = db.Column(db.String(120))
    relative_relation = db.Column(db.String(50))
    measurements = db.relationship('HealthMeasurement', backref='user', lazy=True)
    reports = db.relationship('Report', backref='user', lazy=True)
    symptoms = db.relationship('SymptomLog', backref='user', lazy=True)

class HealthMeasurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bpm = db.Column(db.Float, nullable=False)
    signal_quality = db.Column(db.String(20))
    source = db.Column(db.String(20))
    is_abnormal = db.Column(db.Boolean, default=False)
    ai_analysis = db.Column(db.Text)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period = db.Column(db.String(20))
    generated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    avg_hr = db.Column(db.Float)
    abnormal_count = db.Column(db.Integer)
    summary_text = db.Column(db.Text)

class SymptomLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    symptom = db.Column(db.Text, nullable=False)
    nlp_context = db.Column(db.Text)

class RiskPrediction(db.Model):
    """One saved XGBoost cardiovascular risk prediction (from /predict)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    prediction = db.Column(db.Integer, nullable=False)          # 0 = no CVD, 1 = CVD
    disease_probability = db.Column(db.Float, nullable=False)   # P(CVD), 0-1
    risk_level = db.Column(db.String(20), nullable=False)       # label shown on the prediction page
    inputs = db.Column(db.Text)                                  # JSON of the 11 model inputs

class DoctorAppointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    trigger_bpm = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed, cancelled
    doctor_name = db.Column(db.String(100), default='Dr. Ramesh Kumar')
    room_id = db.Column(db.String(50))
    notes = db.Column(db.Text)
    patient = db.relationship('User', backref='appointments')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# ── Health Connect phone sync blueprint ────────────────────────────────────
from health_sync import health_bp, init_health_db
app.register_blueprint(health_bp)
init_health_db(db)   # pass the shared db so models land in the same SQLite file

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()


# ── Mail config ────────────────────────────────────────────────────────────────
app.config['MAIL_SERVER']       = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT']         = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']      = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME']     = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD']     = (os.getenv('MAIL_PASSWORD') or '').replace(' ', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)

# ── ML Model ───────────────────────────────────────────────────────────────────
model = joblib.load("xgboost2.0_model.pkl")

# ── In-memory stores (replace with DB in production) ──────────────────────────
lifestyle_store      = {}
health_records_store = []
sleep_records        = []   # SleepRecord[]
calendar_events      = []   # CalendarEvent[]
travel_records       = []   # TravelRecord[]
emergency_contacts   = [
    {"name": "Dr. Ramesh Kumar", "phone": "+91-98765-43210", "relation": "Cardiologist"},
    {"name": "Priya (Family)",   "phone": "+91-87654-32109", "relation": "Spouse"},
    {"name": "Bengaluru Emergency", "phone": "112",           "relation": "Emergency Services"},
]

# ── Real Bengaluru hospital data ───────────────────────────────────────────────
HOSPITALS = [
    {"name": "Manipal Hospital (Old Airport Rd)", "lat": 12.9592, "lng": 77.6444, "phone": "080-2502-4444", "rating": 4.5},
    {"name": "Fortis Hospital (Bannerghatta)", "lat": 12.8918, "lng": 77.5972, "phone": "080-6621-4444", "rating": 4.4},
    {"name": "Narayana Health City", "lat": 12.8980, "lng": 77.6101, "phone": "080-7122-2200", "rating": 4.6},
    {"name": "Victoria Hospital", "lat": 12.9719, "lng": 77.5741, "phone": "080-2670-1150", "rating": 4.2},
    {"name": "St. John's Medical College", "lat": 12.9315, "lng": 77.6182, "phone": "080-2206-5000", "rating": 4.5},
]

# ── Ambulance starting positions (spread across Bengaluru) ─────────────────────
AMBULANCE_BASES = [
    {"id": "AMB-001", "lat": 12.9850, "lng": 77.5500, "zone": "North"},
    {"id": "AMB-002", "lat": 12.9200, "lng": 77.6700, "zone": "East"},
    {"id": "AMB-003", "lat": 12.8800, "lng": 77.5800, "zone": "South"},
    {"id": "AMB-004", "lat": 12.9600, "lng": 77.5200, "zone": "West"},
    {"id": "AMB-005", "lat": 12.9400, "lng": 77.6100, "zone": "Central"},
]

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── Authentication Routes ──────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        from flask import redirect, url_for, flash
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        relative_name = request.form.get('relative_name')
        relative_phone = request.form.get('relative_phone')
        relative_email = request.form.get('relative_email')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            full_name=full_name, phone=phone, email=email, password=hashed_pw,
            age=age, gender=gender, relative_name=relative_name, 
            relative_phone=relative_phone, relative_email=relative_email
        )
        db.session.add(user)
        try:
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return f"Error: {e}"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from flask import redirect, url_for, flash
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Login Unsuccessful. Please check email and password."
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    from flask import redirect, url_for
    logout_user()
    return redirect(url_for('login'))

# ── Health Measurements & Reports ──────────────────────────────────────────
@app.route('/api/health/save_reading', methods=['POST'])
@login_required
def save_reading():
    data = request.json
    bpm = data.get('bpm')
    source = data.get('source', 'Unknown')
    quality = data.get('quality', 'Good')
    is_abnormal = bpm < 50 or bpm > 100
    measurement = HealthMeasurement(user_id=current_user.id, bpm=bpm, source=source, signal_quality=quality, is_abnormal=is_abnormal)
    db.session.add(measurement)
    db.session.commit()

    appointment_created = False
    if is_abnormal:
        # Auto-schedule a doctor appointment
        import secrets
        room_id = f"pulseguard-{current_user.id}-{secrets.token_hex(4)}"
        appt = DoctorAppointment(
            user_id=current_user.id,
            trigger_bpm=bpm,
            status='pending',
            doctor_name='Dr. Jayanth Gowda',
            room_id=room_id,
            notes=f"Auto-scheduled: Abnormal HR {round(bpm)} BPM detected via {source} PPG."
        )
        db.session.add(appt)
        db.session.commit()
        appointment_created = True
        try:
            send_doctor_appointment_email(appt, current_user)
        except Exception as err:
            print("Failed to dispatch doctor email on PPG trigger:", err)

    return jsonify({"status": "success", "is_abnormal": is_abnormal, "appointment_created": appointment_created})

@app.route('/reports')
@login_required
def reports():
    measurements = HealthMeasurement.query.filter_by(user_id=current_user.id).order_by(HealthMeasurement.timestamp.desc()).limit(50).all()
    user_reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.generated_at.desc()).all()
    return render_template('reports.html', measurements=measurements, reports=user_reports)

@app.route('/family/<token>')
def family_card(token):
    user = User.query.get(int(token))
    if not user:
        return "Invalid link", 404
    latest = HealthMeasurement.query.filter_by(user_id=user.id).order_by(HealthMeasurement.timestamp.desc()).first()
    return render_template('family_card.html', user=user, latest=latest)


# ── Background Task: Daily/Weekly Reports ──────────────────────────────────
def generate_reports():
    with app.app_context():
        users = User.query.all()
        for user in users:
            measurements = HealthMeasurement.query.filter_by(user_id=user.id).all()
            if measurements:
                avg_hr = sum(m.bpm for m in measurements) / len(measurements)
                abnorms = sum(1 for m in measurements if m.is_abnormal)
                report = Report(user_id=user.id, period="Daily", avg_hr=avg_hr, abnormal_count=abnorms, summary_text="Daily summary generated automatically.")
                db.session.add(report)
                db.session.commit()
                # Email to relative
                if user.relative_email and app.config['MAIL_USERNAME']:
                    try:
                        share_url = f"http://127.0.0.1:5000/family/{user.id}"
                        msg = Message(f"PulseGuard Daily Report for {user.full_name}", recipients=[user.relative_email])
                        msg.body = f"Avg HR: {avg_hr:.1f} BPM. Abnormal Readings: {abnorms}. View live monitoring here: {share_url}"
                        mail.send(msg)
                    except Exception as e:
                        print("Email failed", e)

scheduler.add_job(func=generate_reports, trigger="interval", hours=24)

@app.route('/api/health/share_card', methods=['POST'])
@login_required
def share_card():
    user = current_user
    if user.relative_email and app.config.get('MAIL_USERNAME'):
        try:
            share_url = f"http://127.0.0.1:5000/family/{user.id}"
            msg = Message(f"PulseGuard Family Access for {user.full_name}", recipients=[user.relative_email])
            msg.body = f"Hello {user.relative_name},\n\nYou have been granted access to monitor {user.full_name}'s health via PulseGuard.\n\nAccess the live Family Health Card here: {share_url}"
            mail.send(msg)
            return jsonify({"status": "success", "message": "Email sent to relative!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return jsonify({"error": "Relative email not configured."}), 400
@app.route('/api/health/generate_report', methods=['POST'])
@login_required
def create_manual_report():
    measurements = HealthMeasurement.query.filter_by(user_id=current_user.id).all()
    if not measurements:
        return jsonify({"status": "error", "message": "No measurements recorded yet."}), 400
    avg_hr = sum(m.bpm for m in measurements) / len(measurements)
    abnorms = sum(1 for m in measurements if m.is_abnormal)
    summary = f"On-Demand Summary: Average heart rate is {avg_hr:.1f} BPM across {len(measurements)} screenings with {abnorms} flagged readings."
    report = Report(user_id=current_user.id, period="On-Demand", avg_hr=avg_hr, abnormal_count=abnorms, summary_text=summary)
    db.session.add(report)
    db.session.commit()
    
    if current_user.relative_email and app.config.get('MAIL_USERNAME'):
        try:
            share_url = f"http://127.0.0.1:5000/family/{current_user.id}"
            msg = Message(f"PulseGuard On-Demand Health Report for {current_user.full_name}", recipients=[current_user.relative_email])
            msg.body = f"Hello {current_user.relative_name},\n\nHere is an on-demand health summary for {current_user.full_name}:\n- Average Heart Rate: {avg_hr:.1f} BPM\n- Abnormal Readings: {abnorms}\n- Total Screenings: {len(measurements)}\n\nLive Family Card: {share_url}"
            mail.send(msg)
        except Exception as e:
            print("Failed to dispatch report email:", e)
    return jsonify({"status": "success", "message": "On-demand report generated and emailed to your relative!"})



@app.route('/api/me/last-prediction')
@login_required
def last_prediction():
    latest = HealthMeasurement.query.filter_by(user_id=current_user.id).order_by(HealthMeasurement.timestamp.desc()).first()
    if latest:
        level = "Normal"
        if latest.bpm < 50 or latest.bpm > 100:
            level = "Abnormal"
        return jsonify({
            "score": round(latest.bpm),
            "level": level,
            "date": latest.timestamp.strftime('%Y-%m-%d %H:%M'),
            "quality": latest.signal_quality
        })
    return jsonify({"score": None, "level": None, "date": None})

# ── Doctor Appointment Email & Video Auto-Join ─────────────────────────────
DOCTOR_NOTIFICATION_EMAIL = "jayanthgowda1406@gmail.com"

def get_lan_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def send_doctor_appointment_email(appt, user):
    doctor_email = DOCTOR_NOTIFICATION_EMAIL
    if not app.config.get('MAIL_USERNAME'):
        print("Mail username not configured, cannot send appointment email")
        return False
    try:
        lan_ip = get_lan_ip()
        # Direct Jitsi URL: works on ANY smartphone, iPhone, Android, or laptop worldwide (no localhost needed!)
        direct_video_url = f"https://meet.jit.si/{appt.room_id}#config.prejoinConfig.enabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&config.requireDisplayName=false&userInfo.displayName=Dr.%20Jayanth%20Gowda"
        # Local Wi-Fi accept URL: works for devices on the same Wi-Fi network
        lan_accept_url = f"http://{lan_ip}:5000/doctor/accept_and_join/{appt.room_id}"
        localhost_accept_url = f"http://127.0.0.1:5000/doctor/accept_and_join/{appt.room_id}"
        
        msg = Message(
            subject=f"🚨 URGENT: Doctor Appointment Request - Patient {user.full_name} ({round(appt.trigger_bpm)} BPM)",
            recipients=[doctor_email]
        )
        msg.body = (
            f"Dear Doctor,\n\n"
            f"A patient has requested an urgent cardiology video consultation via PulseGuard AI.\n\n"
            f"Patient Details:\n"
            f"- Name: {user.full_name}\n"
            f"- Age: {user.age} | Gender: {user.gender}\n"
            f"- Phone: {user.phone}\n"
            f"- Heart Rate: {round(appt.trigger_bpm)} BPM (Abnormal Reading)\n"
            f"- Time: {appt.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- Clinical Note: {appt.notes}\n\n"
            f"👉 CLICK TO JOIN VIDEO CALL FROM ANY PHONE OR COMPUTER (CAMERA & MIC AUTO-ON):\n"
            f"{direct_video_url}\n\n"
            f"If you are on the same Wi-Fi as the host machine, you can also use:\n"
            f"{lan_accept_url}\n"
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0b0c10; color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #1f2833;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #e74c3c; margin: 0; font-size: 22px;">🚨 URGENT: Patient Video Consultation Request</h2>
                <p style="color: #888888; font-size: 13px; margin-top: 5px;">PulseGuard AI &bull; Telecardiology Network</p>
            </div>
            
            <div style="background: rgba(255,255,255,0.06); padding: 18px; border-radius: 10px; margin-bottom: 24px; border-left: 4px solid #e74c3c;">
                <p style="margin: 6px 0; font-size: 15px;"><strong>Patient Name:</strong> {user.full_name}</p>
                <p style="margin: 6px 0; font-size: 14px; color: #cccccc;"><strong>Age / Gender:</strong> {user.age} yrs &bull; {user.gender}</p>
                <p style="margin: 6px 0; font-size: 14px; color: #cccccc;"><strong>Phone Number:</strong> {user.phone}</p>
                <p style="margin: 8px 0 6px; font-size: 16px;"><strong>Detected Heart Rate:</strong> <span style="color: #e74c3c; font-weight: bold; font-size: 18px;">{round(appt.trigger_bpm)} BPM</span></p>
                <p style="margin: 6px 0; font-size: 13px; color: #aaaaaa;"><strong>Timestamp:</strong> {appt.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p style="margin: 6px 0; font-size: 13px; color: #aaaaaa;"><strong>Clinical Note:</strong> {appt.notes}</p>
            </div>

            <!-- PRIMARY BUTTON: Universal Link that works on ANY mobile device, phone, or laptop -->
            <div style="text-align: center; margin: 25px 0;">
                <a href="{direct_video_url}" style="background: #2ecc71; color: #ffffff; padding: 18px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 20px rgba(46,204,113,0.5);">
                    📹 JOIN LIVE VIDEO CALL NOW<br>
                    <span style="font-size: 12px; font-weight: normal; opacity: 0.9;">(Works on ANY Mobile Phone, Tablet, or PC)</span>
                </a>
            </div>

            <div style="background: rgba(46,204,113,0.1); border: 1px solid rgba(46,204,113,0.3); padding: 12px; border-radius: 8px; font-size: 12px; color: #2ecc71; text-align: center; margin-bottom: 20px;">
                ⚡ <strong>Instant Video:</strong> Camera and microphone will activate automatically upon connecting. No app installation required!
            </div>

            <!-- ALTERNATIVE LINKS -->
            <div style="border-top: 1px solid #222; padding-top: 15px; font-size: 12px; color: #888888; text-align: left;">
                <p style="margin: 4px 0;"><strong>Alternative Access Links:</strong></p>
                <p style="margin: 4px 0;">&bull; On Same Wi-Fi Network: <a href="{lan_accept_url}" style="color: #3498db;">{lan_accept_url}</a></p>
                <p style="margin: 4px 0;">&bull; On Host Laptop: <a href="{localhost_accept_url}" style="color: #3498db;">{localhost_accept_url}</a></p>
            </div>
        </div>
        """
        mail.send(msg)
        print(f"Appointment request email sent successfully to {doctor_email}")
        return True
    except Exception as e:
        print(f"Error sending doctor appointment email: {e}")
        return False

@app.route('/doctor/accept_and_join/<room_id>')
def doctor_accept_and_join(room_id):
    from flask import redirect
    appt = DoctorAppointment.query.filter_by(room_id=room_id).first()
    if appt:
        appt.status = 'accepted'
        db.session.commit()
    return redirect(f"/videochat/{room_id}?role=doctor")

@app.route('/api/appointments/request_doctor', methods=['POST'])
@login_required
def request_doctor_appointment():
    import secrets
    data = request.json or {}
    bpm = data.get('bpm')
    if not bpm:
        latest = HealthMeasurement.query.filter_by(user_id=current_user.id).order_by(HealthMeasurement.timestamp.desc()).first()
        bpm = latest.bpm if latest else 78.0
    
    room_id = f"pulseguard-{current_user.id}-{secrets.token_hex(4)}"
    appt = DoctorAppointment(
        user_id=current_user.id,
        trigger_bpm=float(bpm),
        status='pending',
        doctor_name='Dr. Jayanth Gowda',
        room_id=room_id,
        notes=f"Consultation requested by {current_user.full_name}. HR: {round(float(bpm))} BPM."
    )
    db.session.add(appt)
    db.session.commit()
    
    email_sent = send_doctor_appointment_email(appt, current_user)
    doctor_url = f"http://127.0.0.1:5000/doctor/accept_and_join/{room_id}"
    mailto_url = f"mailto:{DOCTOR_NOTIFICATION_EMAIL}?subject=Urgent%20Cardiology%20Consultation%20Request%20-%20Patient%20{current_user.full_name}&body=Please%20accept%20and%20join%20the%20live%20video%20call%20here:%20{doctor_url}"

    return jsonify({
        "status": "success",
        "appointment_id": appt.id,
        "room_id": room_id,
        "doctor_url": doctor_url,
        "mailto_url": mailto_url,
        "email_sent": email_sent,
        "message": f"Appointment request dispatched to {DOCTOR_NOTIFICATION_EMAIL}!" if email_sent else "Appointment created! (Email could not be sent via SMTP due to invalid Gmail App Password)."
    })

# ── Appointments & Video Chat ──────────────────────────────────────────────
@app.route('/appointments')
@login_required
def appointments_page():
    appts = DoctorAppointment.query.filter_by(user_id=current_user.id).order_by(DoctorAppointment.created_at.desc()).all()
    return render_template('appointments.html', appointments=appts)

@app.route('/api/appointments', methods=['GET'])
@login_required
def get_appointments():
    appts = DoctorAppointment.query.filter_by(user_id=current_user.id).order_by(DoctorAppointment.created_at.desc()).all()
    return jsonify([{
        "id": a.id, "status": a.status, "doctor": a.doctor_name,
        "bpm": a.trigger_bpm, "room_id": a.room_id,
        "created": a.created_at.strftime('%Y-%m-%d %H:%M'), "notes": a.notes
    } for a in appts])

@app.route('/api/appointments/<int:appt_id>/accept', methods=['POST'])
def accept_appointment(appt_id):
    appt = DoctorAppointment.query.get_or_404(appt_id)
    appt.status = 'accepted'
    db.session.commit()
    return jsonify({"status": "accepted", "room_id": appt.room_id})

@app.route('/api/appointments/<int:appt_id>/complete', methods=['POST'])
@login_required
def complete_appointment(appt_id):
    appt = DoctorAppointment.query.get_or_404(appt_id)
    appt.status = 'completed'
    db.session.commit()
    return jsonify({"status": "completed"})

@app.route('/api/appointments/<int:appt_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    appt = DoctorAppointment.query.get_or_404(appt_id)
    appt.status = 'cancelled'
    db.session.commit()
    return jsonify({"status": "cancelled"})

@app.route('/api/appointments/<int:appt_id>/delete', methods=['POST'])
@login_required
def delete_appointment(appt_id):
    appt = DoctorAppointment.query.get_or_404(appt_id)
    if appt.user_id == current_user.id:
        db.session.delete(appt)
        db.session.commit()
    return jsonify({"status": "deleted"})

@app.route('/api/appointments/clear_history', methods=['POST'])
@login_required
def clear_appointment_history():
    DoctorAppointment.query.filter(DoctorAppointment.user_id == current_user.id, DoctorAppointment.status.in_(['completed', 'cancelled'])).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})

@app.route('/videochat/<room_id>')
def videochat(room_id):
    appt = DoctorAppointment.query.filter_by(room_id=room_id).first()
    return render_template('videochat.html', room_id=room_id, appointment=appt)

@app.route('/doctor')
def doctor_dashboard():
    pending = DoctorAppointment.query.filter_by(status='pending').order_by(DoctorAppointment.created_at.desc()).all()
    accepted = DoctorAppointment.query.filter_by(status='accepted').order_by(DoctorAppointment.created_at.desc()).all()
    return render_template('doctor_dashboard.html', pending=pending, accepted=accepted)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/wearable")
def wearable():
    return render_template("wearable.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/lifestyle")
@login_required
def lifestyle():
    return render_template("lifestyle.html")

@app.route("/diet")
@login_required
def diet():
    return render_template("diet.html")

@app.route("/emergency")
@login_required
def emergency():
    user_contacts = []
    # Real saved relative contact from DB
    if current_user.relative_name:
        user_contacts.append({
            "name": current_user.relative_name,
            "phone": current_user.relative_phone or "Not provided",
            "relation": current_user.relative_relation or "Designated Relative",
            "icon": "fa-user-shield",
            "is_user_saved": True
        })
    # Real user phone
    if current_user.phone:
        user_contacts.append({
            "name": f"{current_user.full_name} (Patient)",
            "phone": current_user.phone,
            "relation": "Self / Registered Patient",
            "icon": "fa-user",
            "is_user_saved": True
        })
    # Doctor contact
    user_contacts.append({
        "name": "Dr. Jayanth Gowda",
        "phone": "+91-7406282982",
        "relation": "Cardiologist (On-Call)",
        "icon": "fa-user-md",
        "is_user_saved": False
    })
    # 112 National Emergency
    user_contacts.append({
        "name": "National Emergency Response Support",
        "phone": "112",
        "relation": "National Police & Medical Helpline",
        "icon": "fa-ambulance",
        "is_user_saved": False
    })
    return render_template("emergency.html", contacts=user_contacts)

@app.route("/heartrate")
@login_required
def heartrate():
    return render_template("heartrate.html")

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/lifeplanner")
def lifeplanner():
    return render_template("lifeplanner.html")

# ══════════════════════════════════════════════════════════════════════════════
#  PREDICTION  (existing)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        age               = int(data["age"])
        gender            = int(data["gender"])
        bmi               = float(data["bmi"])
        smoking           = int(data["smoking"])
        alcohol_intake    = int(data["alcohol_intake"])
        physical_activity = int(data["physical_activity"])
        sleep_level       = int(data["sleep_level"])
        cholesterol_level = int(data["cholesterol_level"])
        hypertension      = int(data["hypertension"])
        diabetes          = int(data["diabetes"])
        family_history    = int(data["family_history"])

        input_data = np.array([[age, gender, bmi, smoking, alcohol_intake,
                                 physical_activity, sleep_level, cholesterol_level,
                                 hypertension, diabetes, family_history]])

        prediction  = int(model.predict(input_data)[0])
        probability = float(max(model.predict_proba(input_data)[0]))

        if prediction == 0:
            risk_level = "No Risk"
        elif probability < 0.40:
            risk_level = "Low Risk"
        elif 0.40 <= probability < 0.75:
            risk_level = "Moderate Risk"
        else:
            risk_level = "High Risk"

        result = "Has Cardiovascular Disease" if prediction == 1 else "No Cardiovascular Disease"

        # Save the result for signed-in users so other pages (e.g. Diet) can use it
        saved = False
        if current_user.is_authenticated:
            try:
                disease_prob = float(model.predict_proba(input_data)[0][1])
                db.session.add(RiskPrediction(
                    user_id=current_user.id, prediction=prediction,
                    disease_probability=disease_prob, risk_level=risk_level,
                    inputs=json.dumps({k: data.get(k) for k in (
                        "age", "gender", "bmi", "smoking", "alcohol_intake", "physical_activity",
                        "sleep_level", "cholesterol_level", "hypertension", "diabetes", "family_history")})))
                db.session.commit()
                saved = True
            except Exception as err:
                db.session.rollback()
                print("Failed to save risk prediction:", err)

        return jsonify({"prediction": result, "probability": round(probability, 2),
                        "risk_level": risk_level, "saved": saved})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ══════════════════════════════════════════════════════════════════════════════
#  RISK SCORE ENGINE  (weighted scoring)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/risk-score', methods=['POST'])
def risk_score():
    try:
        d = request.json
        score = 0

        age = int(d.get("age", 30))
        if age > 60: score += 20
        elif age > 45: score += 12
        elif age > 35: score += 6

        bmi = float(d.get("bmi", 22))
        if bmi > 30: score += 15
        elif bmi > 25: score += 8

        if int(d.get("smoking", 0)) == 2: score += 15
        elif int(d.get("smoking", 0)) == 1: score += 7

        if int(d.get("alcohol", 0)) == 2: score += 10
        elif int(d.get("alcohol", 0)) == 1: score += 4

        ch = int(d.get("cholesterol", 0))
        if ch == 2: score += 15
        elif ch == 1: score += 8

        if int(d.get("hypertension", 0)) == 1: score += 12
        if int(d.get("diabetes", 0)) == 1: score += 10
        if int(d.get("family_history", 0)) == 1: score += 8

        pa = int(d.get("physical_activity", 1))
        if pa == 0: score += 8
        elif pa == 2: score -= 5

        sl = int(d.get("sleep", 1))
        if sl == 0: score += 5

        score = max(0, min(100, score))

        if score < 30:
            level = "LOW"; color = "#1db954"
        elif score <= 60:
            level = "MEDIUM"; color = "#f39c12"
        else:
            level = "HIGH"; color = "#e74c3c"

        factors = []
        if age > 45: factors.append("Age above 45")
        if bmi > 25: factors.append(f"Elevated BMI ({bmi:.1f})")
        if int(d.get("smoking", 0)) > 0: factors.append("Smoking habit")
        if int(d.get("hypertension", 0)): factors.append("Hypertension")
        if int(d.get("diabetes", 0)): factors.append("Diabetes")
        if int(d.get("cholesterol", 0)) > 0: factors.append("High cholesterol")
        if int(d.get("family_history", 0)): factors.append("Family history of CVD")

        recommendations = []
        if level == "LOW":
            recommendations = ["Maintain current healthy habits", "Annual check-up recommended",
                                "Continue regular exercise", "Monitor BP monthly"]
        elif level == "MEDIUM":
            recommendations = ["Consult a cardiologist within 3 months", "Reduce sodium intake",
                                "30 min brisk walk daily", "Quit/reduce smoking",
                                "Monitor BP weekly", "Reduce alcohol consumption"]
        else:
            recommendations = ["⚠️ Seek medical attention immediately", "Contact your cardiologist today",
                                "Strict medication adherence required", "Avoid strenuous activity",
                                "Monitor vitals twice daily", "Emergency contacts should be notified"]

        return jsonify({
            "score": score, "level": level, "color": color,
            "factors": factors, "recommendations": recommendations,
            "health_score": max(0, 100 - score)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ══════════════════════════════════════════════════════════════════════════════
#  LIFESTYLE API
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/lifestyle', methods=['POST'])
def save_lifestyle():
    try:
        d = request.json
        user_id = d.get("user_id", "default")

        score = 100
        if int(d.get("smoking", 0)) == 2: score -= 20
        elif int(d.get("smoking", 0)) == 1: score -= 10
        if int(d.get("alcohol", 0)) == 2: score -= 15
        elif int(d.get("alcohol", 0)) == 1: score -= 7
        if int(d.get("activity", 1)) == 0: score -= 15
        elif int(d.get("activity", 1)) == 2: score += 5
        if int(d.get("sleep_hours", 7)) < 6: score -= 10
        if int(d.get("stress", 3)) > 7: score -= 15
        if int(d.get("meetings", 4)) > 8: score -= 10
        score = max(0, min(100, score))

        lifestyle_store[user_id] = {**d, "lifestyle_score": score}
        return jsonify({"lifestyle_score": score, "message": "Lifestyle data saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ══════════════════════════════════════════════════════════════════════════════
#  DIET ANALYSIS API
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/diet-analyze', methods=['POST'])
@login_required
def diet_analyze():
    """Mock food classification — returns realistic results based on food name input."""
    try:
        d = request.json
        food_name = d.get("food_name", "").lower().strip()

        junk_keywords    = ["pizza", "burger", "fries", "chips", "fried", "soda", "cola", "candy", "donut", "cake", "samosa", "pakoda"]
        healthy_keywords = ["salad", "fruit", "apple", "banana", "grapes", "oats", "yogurt", "dal", "rice", "roti", "sabzi", "vegetable", "soup", "idli", "dosa"]
        high_fat_keywords= ["butter", "cheese", "cream", "paneer", "egg", "chicken", "mutton", "fish", "ghee", "oil"]

        if any(k in food_name for k in junk_keywords):
            category = "Junk Food"
            calories = random.randint(350, 700)
            feedback = "⚠️ High in sodium, trans fats, and refined sugar. Avoid regularly."
            color = "#e74c3c"
            heart_impact = "Negative"
        elif any(k in food_name for k in high_fat_keywords):
            category = "High Fat"
            calories = random.randint(200, 450)
            feedback = "🟡 Moderate saturated fat content. Consume in limited portions."
            color = "#f39c12"
            heart_impact = "Moderate"
        elif any(k in food_name for k in healthy_keywords):
            category = "Balanced / Healthy"
            calories = random.randint(80, 250)
            feedback = "✅ Good nutritional profile. Excellent for heart health."
            color = "#1db954"
            heart_impact = "Positive"
        else:
            category = "Unknown / Mixed"
            calories = random.randint(150, 400)
            feedback = "ℹ️ Unable to classify precisely. Eat mindfully."
            color = "#3498db"
            heart_impact = "Neutral"

        heart_tip = (
            "Opt for whole grains, fruits, vegetables, and lean proteins."
            if heart_impact != "Positive"
            else "Great choice! Keep up the heart-healthy eating."
        )

        return jsonify({
            "food": food_name or "Unknown food",
            "category": category,
            "calories_estimate": f"{calories} kcal",
            "feedback": feedback,
            "color": color,
            "heart_impact": heart_impact,
            "heart_tip": heart_tip
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ══════════════════════════════════════════════════════════════════════════════
#  RISK-TIERED MEAL PLAN API  (linked to XGBoost score)
# ══════════════════════════════════════════════════════════════════════════════

# Full meal-plan database keyed by risk tier
MEAL_PLANS = {
    "LOW": {
        "tier": "LOW",
        "label": "Low Cardiac Risk",
        "color": "#1db954",
        "gradient": "linear-gradient(135deg,#1db95422,#0b0c10)",
        "icon": "fa-shield-heart",
        "tagline": "You're doing great — maintain your heart-healthy momentum.",
        "daily_calories": "1800–2200 kcal",
        "key_principle": "Mediterranean-style eating with balanced macros",
        "meals": {
            "breakfast": {
                "emoji": "🌅",
                "label": "Breakfast",
                "items": [
                    "Rolled oats with mixed berries & chia seeds",
                    "2 boiled / poached eggs",
                    "Green tea or black coffee (no sugar)",
                    "1 banana or seasonal fruit"
                ],
                "avoid": ["Packaged cereals", "White bread toast"],
                "note": "High-fiber start keeps LDL in check."
            },
            "lunch": {
                "emoji": "☀️",
                "label": "Lunch",
                "items": [
                    "Brown rice or jowar roti (2–3 pieces)",
                    "Dal / rajma / chana (½ cup)",
                    "Mixed seasonal sabzi (low oil)",
                    "Low-fat buttermilk or curd"
                ],
                "avoid": ["White rice in excess", "Creamy gravies"],
                "note": "Complex carbs sustain energy without glycaemic spikes."
            },
            "snack": {
                "emoji": "🌤️",
                "label": "Snack",
                "items": [
                    "Handful of walnuts or almonds",
                    "Fresh fruit salad",
                    "Sprouts chaat with lemon",
                    "Herbal / green tea"
                ],
                "avoid": ["Biscuits", "Namkeen / chips"],
                "note": "Omega-3 from walnuts actively lowers triglycerides."
            },
            "dinner": {
                "emoji": "🌙",
                "label": "Dinner",
                "items": [
                    "2 whole-wheat rotis",
                    "Grilled fish or paneer tikka",
                    "Salad with olive oil & lemon dressing",
                    "Warm low-fat milk (optional)"
                ],
                "avoid": ["Heavy desserts", "Fried sides"],
                "note": "Light dinner ≥ 2 hrs before sleep supports cardiac recovery."
            }
        },
        "superfoods": ["Walnuts", "Salmon/Rohu", "Blueberries", "Olive oil", "Spinach", "Oats", "Lentils", "Garlic", "Avocado", "Dark chocolate (70%+)"],
        "strict_avoid": ["Trans fats", "Processed meats", "Deep-fried snacks"],
        "hydration": "8–10 glasses of water daily",
        "weekly_tip": "One cheat meal per week is fine — enjoy mindfully."
    },
    "MEDIUM": {
        "tier": "MEDIUM",
        "label": "Moderate Cardiac Risk",
        "color": "#f39c12",
        "gradient": "linear-gradient(135deg,#f39c1222,#0b0c10)",
        "icon": "fa-triangle-exclamation",
        "tagline": "Time to be more intentional — targeted diet changes cut your risk significantly.",
        "daily_calories": "1600–2000 kcal",
        "key_principle": "DASH diet — low sodium, high potassium, plant-forward",
        "meals": {
            "breakfast": {
                "emoji": "🌅",
                "label": "Breakfast",
                "items": [
                    "Steel-cut oats with flaxseeds & cinnamon (no sugar)",
                    "1 egg white omelette with spinach",
                    "Unsweetened green tea",
                    "Small apple or pear"
                ],
                "avoid": ["Whole eggs daily", "Paratha with butter", "Sugary juices"],
                "note": "Cinnamon + flaxseeds help moderate blood pressure and LDL."
            },
            "lunch": {
                "emoji": "☀️",
                "label": "Lunch",
                "items": [
                    "1–2 multigrain rotis (no ghee)",
                    "Moong dal or masoor dal (low salt)",
                    "Steamed / dry-cooked vegetables",
                    "Cucumber-tomato salad"
                ],
                "avoid": ["Rice at lunch", "High-sodium pickles", "Paneer butter masala"],
                "note": "Limit sodium to <1500 mg/day — crucial for BP control at moderate risk."
            },
            "snack": {
                "emoji": "🌤️",
                "label": "Snack",
                "items": [
                    "10–12 almonds + 2 walnuts",
                    "Roasted makhana (fox nuts)",
                    "Vegetable soup (no cream, low salt)",
                    "Coconut water (natural)"
                ],
                "avoid": ["Vada / samosa", "Packaged energy bars", "Fruit juices"],
                "note": "Makhana is low-calorie, high-magnesium — supports heart rhythm."
            },
            "dinner": {
                "emoji": "🌙",
                "label": "Dinner",
                "items": [
                    "1 whole-wheat roti or small bowl of khichdi",
                    "Steamed or baked fish (2×/week) or tofu",
                    "Large salad: leafy greens, beets, carrots",
                    "Warm turmeric milk (skimmed)"
                ],
                "avoid": ["Meat at dinner", "Heavy curries", "Desserts"],
                "note": "Early, light dinner (by 7:30 PM) reduces nocturnal cardiac strain."
            }
        },
        "superfoods": ["Flaxseeds", "Beetroot", "Pomegranate", "Turmeric", "Makhana", "Tofu", "Green leafy veg", "Berries", "Amla (Indian gooseberry)", "Dark lentils"],
        "strict_avoid": ["Table salt / extra salt", "Red meat", "Butter & ghee", "White bread & maida", "Sugary drinks", "Alcohol", "Full-fat dairy"],
        "hydration": "10–12 glasses; add lemon / cucumber for electrolytes",
        "weekly_tip": "Cheat meals not recommended. If craving, choose baked over fried."
    },
    "HIGH": {
        "tier": "HIGH",
        "label": "High Cardiac Risk",
        "color": "#e74c3c",
        "gradient": "linear-gradient(135deg,#e74c3c22,#0b0c10)",
        "icon": "fa-heart-circle-exclamation",
        "tagline": "⚠️ Your diet is now a clinical tool — strict adherence is non-negotiable.",
        "daily_calories": "1400–1800 kcal (doctor-supervised)",
        "key_principle": "Therapeutic cardiac diet — low sodium, low saturated fat, anti-inflammatory",
        "meals": {
            "breakfast": {
                "emoji": "🌅",
                "label": "Breakfast",
                "items": [
                    "Plain oats with only flaxseeds & berries (no honey/sugar)",
                    "Egg whites only (2–3) — NO yolk",
                    "Warm water with lemon (no caffeine if BP-driven)",
                    "Half a banana"
                ],
                "avoid": ["Any fried item", "Dairy except skimmed", "Caffeinated beverages", "Fruit juices"],
                "note": "Removing egg yolk eliminates ~186 mg dietary cholesterol per egg."
            },
            "lunch": {
                "emoji": "☀️",
                "label": "Lunch",
                "items": [
                    "1 multigrain roti (no oil/ghee)",
                    "Boiled moong / masoor dal (minimal salt)",
                    "Stir-fried vegetables (½ tsp olive oil only)",
                    "Thin curd (skimmed)"
                ],
                "avoid": ["Rice", "Any added salt", "Paneer", "Chicken / mutton", "Cooking oils except olive"],
                "note": "Sodium < 1000 mg/day is the clinical target for high-risk CVD patients."
            },
            "snack": {
                "emoji": "🌤️",
                "label": "Snack",
                "items": [
                    "5–6 soaked almonds only",
                    "Cucumber / carrot sticks",
                    "Herbal tea (hibiscus or tulsi — both cardioprotective)",
                    "Amla (Indian gooseberry) — 1–2 fresh"
                ],
                "avoid": ["ALL packaged snacks", "Nuts beyond recommended", "Any sweetened drink"],
                "note": "Hibiscus tea clinically shown to lower systolic BP by 7–10 mmHg."
            },
            "dinner": {
                "emoji": "🌙",
                "label": "Dinner",
                "items": [
                    "Vegetable khichdi (rice + moong dal, minimal salt)",
                    "Steamed fish (2–3×/week) — no frying",
                    "Boiled / steamed mixed vegetables",
                    "Warm skimmed milk with turmeric"
                ],
                "avoid": ["ALL meat except lean fish", "Dairy fat", "Any dessert", "Late dinner (after 7 PM)"],
                "note": "Omega-3 in fish (EPA/DHA) is the single most evidence-backed dietary intervention for CHD."
            }
        },
        "superfoods": ["Amla", "Hibiscus tea", "Flaxseeds", "Fatty fish (Rohu/Salmon)", "Garlic (raw)", "Pomegranate", "Beets", "Dark leafy greens", "Turmeric + black pepper", "Berries"],
        "strict_avoid": ["Salt shakers", "ALL processed & packaged foods", "Red & processed meats", "Butter, ghee, coconut oil", "Full-fat dairy", "Sugar & sweets", "Alcohol", "Smoking"],
        "hydration": "12+ glasses; herbal teas count. Avoid caffeinated drinks if hypertensive.",
        "weekly_tip": "Consult a registered dietitian. Your diet is as important as your medication."
    }
}

@app.route('/api/diet/risk-profile')
@login_required
def diet_risk_profile():
    """Return the user's diet risk tier from their last saved XGBoost prediction.
    If they have never run a prediction, has_prediction is False and no score is given."""
    try:
        user = current_user
        latest_m = HealthMeasurement.query.filter_by(user_id=user.id)\
                       .order_by(HealthMeasurement.timestamp.desc()).first()
        bpm = latest_m.bpm if latest_m else None
        bpm_flag = bool(bpm and (bpm < 50 or bpm > 100))
        base = {
            "bpm": round(bpm, 1) if bpm else None,
            "bpm_abnormal": bpm_flag,
            "age": user.age,
        }

        pred = RiskPrediction.query.filter_by(user_id=user.id)\
                   .order_by(RiskPrediction.timestamp.desc()).first()
        if not pred:
            return jsonify({**base, "has_prediction": False, "score": None, "tier": None})

        # Tier follows the label the prediction page showed the user
        tier = PREDICTION_LEVEL_TO_TIER.get(pred.risk_level, "LOW")
        return jsonify({
            **base,
            "has_prediction": True,
            "source": "XGBoost 2.0",
            "score": round(pred.disease_probability * 100),   # P(CVD) as 0-100
            "tier": tier,
            "color": MEAL_PLANS[tier]["color"],
            "risk_level": pred.risk_level,
            "predicted_at": pred.timestamp.strftime('%Y-%m-%d %H:%M'),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# XGBoost prediction label -> meal-plan tier
PREDICTION_LEVEL_TO_TIER = {
    "No Risk": "LOW", "Low Risk": "LOW",
    "Moderate Risk": "MEDIUM", "High Risk": "HIGH",
}
# Accepted spellings for the meal-plan API
TIER_ALIASES = {"LOW": "LOW", "MEDIUM": "MEDIUM", "MODERATE": "MEDIUM", "HIGH": "HIGH"}


@app.route('/api/diet/meal-plan', methods=['POST'])
@login_required
def diet_meal_plan():
    """Return the risk-tiered meal plan matching the given tier (LOW/MEDIUM/HIGH).
    Frontend passes the tier; backend validates and returns the full structured plan."""
    try:
        d = request.get_json(silent=True) or {}
        raw = str(d.get("tier") or "").strip().upper()
        tier = TIER_ALIASES.get(raw)
        if not tier:
            return jsonify({"error": f"Unknown risk tier '{d.get('tier')}'. "
                                     "Use LOW, MEDIUM (or MODERATE) or HIGH."}), 400
        plan = MEAL_PLANS[tier]
        return jsonify({"plan": plan, "status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ══════════════════════════════════════════════════════════════════════════════
#  EMERGENCY API
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/emergency/sos', methods=['POST'])
@login_required
def emergency_sos():
    try:
        d = request.json
        user_name = current_user.full_name if current_user.is_authenticated else "PulseGuard User"
        location  = d.get("location", "Bengaluru, Karnataka")
        lat       = d.get("lat", 12.9716)
        lng       = d.get("lng", 77.5946)
        maps_link = f"https://maps.google.com/?q={lat},{lng}"

        sms_body = (
            f"🚨 EMERGENCY SOS — PulseGuard AI\n"
            f"Patient: {user_name}\n"
            f"Location: {location}\n"
            f"GPS: {maps_link}\n"
            f"Please respond IMMEDIATELY or call 112."
        )

        latest_bpm = "Unknown"
        if current_user.is_authenticated:
            latest_m = HealthMeasurement.query.filter_by(user_id=current_user.id).order_by(HealthMeasurement.timestamp.desc()).first()
            if latest_m:
                latest_bpm = str(round(latest_m.bpm))
        twiml_say = (
            f"Emergency alert from {user_name}. Pulse Guard detected a critical S O S event indicating a possible heart attack. "
            f"The latest recorded heart rate was {latest_bpm} beats per minute. "
            f"The user's last known location is {location}. "
            f"Please contact the user immediately and seek emergency medical assistance."
        )


        
        if current_user.is_authenticated and current_user.relative_phone:
            contacts = [{'name': current_user.relative_name, 'phone': current_user.relative_phone}]
        else:
            contacts = get_emergency_contacts()

        sms_results  = []
        call_results = []

        # ── Real Twilio SMS + Voice Call ───────────────────────────────────
        if twilio_client:
            for contact in contacts:
                if not contact.get('phone'):
                    continue
                
                phone_num = contact['phone'].strip()
                if not phone_num.startswith('+'):
                    # Default to India +91 if not specified
                    phone_num = '+91' + phone_num
                
                # SMS
                try:
                    msg = twilio_client.messages.create(
                        body=sms_body,
                        from_=TWILIO_FROM,
                        to=phone_num
                    )
                    sms_results.append({'name': contact['name'], 'status': 'sent', 'sid': msg.sid})
                except Exception as sms_err:
                    sms_results.append({'name': contact['name'], 'status': 'failed', 'error': str(sms_err)})

                # Voice Call (TwiML)
                try:
                    call = twilio_client.calls.create(
                        twiml=f'<Response><Say voice="alice" language="en-IN">{twiml_say}</Say><Pause length="1"/><Say voice="alice" language="en-IN">{twiml_say}</Say></Response>',
                        from_=TWILIO_FROM,
                        to=phone_num
                    )
                    call_results.append({'name': contact['name'], 'status': 'called', 'sid': call.sid})
                except Exception as call_err:
                    call_results.append({'name': contact['name'], 'status': 'call_failed', 'error': str(call_err)})

        # ── Email alert ────────────────────────────────────────────────────
        email_sent = False
        try:
            notify_email = os.getenv('MAIL_USERNAME')
            if notify_email:
                msg = Message(
                    subject=f"🚨 SOS ALERT — {user_name} needs help!",
                    recipients=[notify_email],
                    html=f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#e74c3c;color:#fff;padding:20px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;">🚨 EMERGENCY SOS ALERT</h1>
    <p style="margin:4px 0 0;">PulseGuard AI — Immediate Action Required</p>
  </div>
  <div style="background:#1a1a2e;color:#e0e0e0;padding:24px;border-radius:0 0 8px 8px;">
    <p><b>Patient:</b> {user_name}</p>
    <p><b>Location:</b> {location}</p>
    <p><b>Coordinates:</b> {lat}, {lng}</p>
    <p><a href="{maps_link}" style="color:#e74c3c;">📍 Open in Google Maps</a></p>
    <hr style="border-color:#333;"/>
    <p style="color:#aaa;font-size:12px;">This is an automated emergency alert from PulseGuard AI.<br/>Please respond immediately or call 112.</p>
  </div>
</div>""",
                    body=f"SOS ALERT\nPatient: {user_name}\nLocation: {location}\nGPS: {maps_link}\nCall 112 immediately."
                )
                mail.send(msg)
                email_sent = True
        except Exception:
            email_sent = False

        nearest  = min(HOSPITALS, key=lambda h: math.sqrt((h["lat"]-lat)**2 + (h["lng"]-lng)**2))
        distance = math.sqrt((nearest["lat"]-lat)**2 + (nearest["lng"]-lng)**2) * 111

        contacts_notified = len([r for r in sms_results if r['status'] == 'sent'])
        calls_made        = len([r for r in call_results if r['status'] == 'called'])

        return jsonify({
            "status": "SOS_TRIGGERED",
            "message": f"Emergency alert sent! Nearest hospital: {nearest['name']}",
            "nearest_hospital": nearest,
            "distance_km": round(distance, 2),
            "eta_minutes": round(distance / 0.5),
            "email_sent": email_sent,
            "sms_results": sms_results,
            "call_results": call_results,
            "contacts_notified": contacts_notified if twilio_client else len(contacts),
            "calls_made": calls_made,
            "twilio_active": twilio_client is not None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/ambulances', methods=['GET'])
def get_ambulances():
    """Return mock ambulance positions with small random drift to simulate movement."""
    ambulances = []
    for amb in AMBULANCE_BASES:
        ambulances.append({
            "id": amb["id"],
            "zone": amb["zone"],
            "lat": amb["lat"] + random.uniform(-0.005, 0.005),
            "lng": amb["lng"] + random.uniform(-0.005, 0.005),
            "status": random.choice(["Available", "Available", "Available", "En Route"]),
            "driver": f"Driver {amb['id'][-1]}",
            "eta": random.randint(3, 15)
        })
    return jsonify({"ambulances": ambulances, "hospitals": HOSPITALS})

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    return jsonify({"hospitals": HOSPITALS})

# ══════════════════════════════════════════════════════════════════════════════
#  HEART RATE ANALYSIS API (FACE-BASED rPPG)
# ══════════════════════════════════════════════════════════════════════════════

# ── Separate log for rejected readings ───────────────────────────────────────
rejected_readings_log = []

# ── Signal validation constants ───────────────────────────────────────────────
HR_MIN_VALID   = 50    # BPM lower bound for safe acceptance
HR_MAX_VALID   = 120   # BPM upper bound for safe acceptance
HR_MIN_PHYSICS = 40    # absolute physiological minimum
HR_MAX_PHYSICS = 180   # absolute physiological maximum
CONF_THRESHOLD = 0.7   # minimum confidence to accept any reading

def estimate_hr_from_face(video_input, api_key=None, method="VITALLENS"):
    """Run VitalLens inference and return raw vitals WITHOUT validation."""
    try:
        from vitallens import VitalLens

        method_str = "vitallens" if method == "VITALLENS" else method
        kwargs = {"method": method_str}
        if api_key and method_str == "vitallens":
            kwargs["api_key"] = api_key
        elif method_str == "vitallens":
            kwargs["method"] = "pos"   # local fallback

        vl = VitalLens(**kwargs)
        results = vl(video_input)

        if not results or len(results) == 0:
            return {"error": "No face detected or video too short"}

        vitals = results[0].get('vitals', {})
        face   = results[0].get('face',   {})

        if 'heart_rate' not in vitals:
            return {"error": "Heart rate could not be extracted from face signal"}

        hr_data    = vitals.get('heart_rate', {})
        bpm        = hr_data.get('value', 0)
        confidence = hr_data.get('confidence', face.get('confidence', 0.0))
        waveform   = hr_data.get('waveform', [])

        return {
            "bpm"       : round(float(bpm), 2),
            "confidence": round(float(confidence), 4),
            "waveform"  : waveform,
            "timestamp" : datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": f"Inference failed: {str(e)}"}


def validate_hr_signal(bpm, confidence):
    """
    Strict two-stage validation.
    Returns (is_valid: bool, rejection_reason: str | None)
    Stage-1: absolute physiological bounds  (40–180 BPM)
    Stage-2: safe clinical range + confidence gate  (50–120 BPM, conf ≥ 0.7)
    """
    if confidence < CONF_THRESHOLD:
        return False, f"Signal confidence too low ({confidence:.2f} < {CONF_THRESHOLD}). Ensure good lighting and stay still."
    if bpm < HR_MIN_PHYSICS:
        return False, f"BPM {bpm} is below the physiological minimum ({HR_MIN_PHYSICS}). Signal likely noise."
    if bpm > HR_MAX_PHYSICS:
        return False, f"BPM {bpm} exceeds the physiological maximum ({HR_MAX_PHYSICS}). Signal likely noise."
    if bpm < HR_MIN_VALID:
        return False, f"BPM {bpm} is outside the safe measurement range ({HR_MIN_VALID}–{HR_MAX_VALID}). Please retry."
    if bpm > HR_MAX_VALID:
        return False, f"BPM {bpm} is outside the safe measurement range ({HR_MIN_VALID}–{HR_MAX_VALID}). Please retry."
    return True, None

def estimate_blood_pressure(hr):
    systolic = 100 + (hr * 0.5)
    diastolic = 60 + (hr * 0.2)
    
    systolic = max(90, min(180, systolic))
    diastolic = max(60, min(120, diastolic))
    
    return {"systolic": round(systolic), "diastolic": round(diastolic)}

def calculate_cv_risk(hr, bp_sys, bp_dia, confidence, trend="stable"):
    if confidence < 0.7:
        return 0
        
    risk_score = 0
    if hr > 120: risk_score += 40
    elif hr > 100: risk_score += 25
    elif hr < 50: risk_score += 30
    
    if bp_sys > 160 or bp_dia > 100: risk_score += 40
    elif bp_sys > 140 or bp_dia > 90: risk_score += 25
    
    if trend == "rising": risk_score += 15
    elif trend == "stable": risk_score -= 10
    
    return max(0, min(100, risk_score))

@app.route('/api/hr/from_face', methods=['POST'])
@login_required
def api_hr_from_face():
    """
    STRICT flow:
      raw_inference → validate → (valid) compute BP + risk + store
                              → (invalid) log + return error
    """
    tmp_file = None
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided", "stored": False}), 400

        video_file = request.files['video']
        tmp_file   = f"temp_video_{random.randint(10000, 99999)}.webm"
        video_file.save(tmp_file)

        api_key = os.getenv('VITALLENS_API_KEY')
        method  = "VITALLENS" if api_key else "pos"

        # ── Step 1: Raw inference ──────────────────────────────────────────────
        raw = estimate_hr_from_face(tmp_file, api_key=api_key, method=method)

        # ── Always clean up temp file ──────────────────────────────────────────
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
            tmp_file = None

        if "error" in raw:
            # Inference itself failed — log and return
            rejected_readings_log.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "reason"   : raw["error"],
                "stage"    : "inference"
            })
            return jsonify({"error": raw["error"], "stored": False,
                            "message": "⚠️ Unstable signal. Please stay still and ensure good lighting."}), 422

        bpm        = raw["bpm"]
        confidence = raw["confidence"]
        waveform   = raw.get("waveform", [])
        timestamp  = raw["timestamp"]

        # ── Step 2: Strict signal validation ──────────────────────────────────
        is_valid, rejection_reason = validate_hr_signal(bpm, confidence)

        if not is_valid:
            rejected_readings_log.append({
                "timestamp" : timestamp,
                "bpm"       : bpm,
                "confidence": confidence,
                "reason"    : rejection_reason,
                "stage"     : "validation"
            })
            return jsonify({
                "error"  : rejection_reason,
                "stored" : False,
                "bpm"    : None,
                "estimated_bp": "--/-- (Waiting for stable HR)",
                "message": "⚠️ Unstable signal. Please stay still and ensure good lighting."
            }), 422

        # ── Step 3: BP estimation — ONLY for valid HR ─────────────────────────
        bp         = estimate_blood_pressure(bpm)
        risk_score = calculate_cv_risk(bpm, bp["systolic"], bp["diastolic"], confidence)

        # ── Step 4: Determine status ───────────────────────────────────────────
        alert_sent = False
        if bpm > 120 or bpm < 45 or bp["systolic"] > 160 or bp["diastolic"] > 100:
            status = "critical"
            alert_sent = True
            if twilio_client:
                try:
                    for contact in get_emergency_contacts():
                        if contact.get('phone'):
                            twilio_client.messages.create(
                                body=(
                                    f"🚨 Emergency Alert:\n"
                                    f"Heart rate: {bpm} BPM  |  BP (est.): {bp['systolic']}/{bp['diastolic']}\n"
                                    f"Immediate attention required.\n"
                                    f"Location: https://maps.google.com/?q=12.9716,77.5946"
                                ),
                                from_=TWILIO_FROM,
                                to=phone_num
                            )
                except Exception as sms_e:
                    print("Twilio alert failed:", sms_e)
        elif bpm >= 100:
            status = "warning"
        else:
            status = "normal"

        # ── Step 5: Store ONLY valid reading ──────────────────────────────────
        record = {
            "user_id"     : "default_user",
            "timestamp"   : timestamp,
            "heart_rate"  : bpm,
            "confidence"  : confidence,
            "estimated_bp": {"systolic": bp["systolic"], "diastolic": bp["diastolic"]},
            "risk_score"  : risk_score,
            "status"      : status
        }
        health_records_store.append(record)

        return jsonify({
            "bpm"         : bpm,
            "confidence"  : confidence,
            "estimated_bp": f"{bp['systolic']}/{bp['diastolic']}",
            "risk_score"  : risk_score,
            "status"      : status,
            "alert_sent"  : alert_sent,
            "stored"      : True,
            "waveform"    : waveform,
            "timestamp"   : timestamp,
            "label"       : "ESTIMATED"
        })

    except Exception as e:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)
        return jsonify({"error": str(e), "stored": False}), 500


@app.route('/api/hr/records', methods=['GET'])
def get_hr_records():
    """Return stored health records, optionally filtered by hours."""
    hours = int(request.args.get('hours', 24))
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
    filtered = [
        r for r in health_records_store
        if datetime.datetime.fromisoformat(r['timestamp']) >= cutoff
    ]
    return jsonify({
        "records"         : filtered,
        "total"           : len(filtered),
        "rejected_total"  : len(rejected_readings_log),
        "hours_window"    : hours
    })

# ══════════════════════════════════════════════════════════════════════════════
#  HEART RATE ANALYSIS API (EXISTING)
# ══════════════════════════════════════════════════════════════════════════════

def score_bpm_risk(bpm, irregular=False, hrv=0):
    """Clinical cardiovascular risk engine for a single heart-rate reading.
    Returns (risk_score 5-100, risk_level LOW/MODERATE/HIGH, category, alert)."""
    risk_score = 0
    alert = None
    category = "Normal Sinus Rhythm"

    if bpm >= 160:
        risk_score = 90
        alert = f'Extreme Tachycardia / Acute Arrhythmia Risk ({bpm} BPM) — immediate clinical triage required'
        category = "Extreme Tachycardia"
    elif bpm >= 140:
        risk_score = 75
        alert = f'Severe Tachycardia detected ({bpm} BPM) — immediate rest and doctor consult advised'
        category = "Severe Sinus Tachycardia"
    elif bpm >= 120:
        risk_score = 55
        alert = f'Moderate Tachycardia detected ({bpm} BPM) — resting recovery & vagal breathing advised'
        category = "Moderate Sinus Tachycardia"
    elif bpm > 100:
        risk_score = 35
        alert = f'Mild Tachycardia detected ({bpm} BPM) — hydrate and rest'
        category = "Mild Tachycardia"
    elif bpm < 45:
        risk_score = 75
        alert = f'Severe Bradycardia detected ({bpm} BPM) — clinical evaluation required'
        category = "Severe Bradycardia"
    elif bpm < 60:
        risk_score = 25
        alert = f'Sinus Bradycardia detected ({bpm} BPM) — monitor for dizziness'
        category = "Sinus Bradycardia"
    else:
        risk_score = 10
        category = "Normal Sinus Rhythm"

    if irregular:
        risk_score = min(100, risk_score + 20)
        alert = (alert + ' + Irregular Rhythm') if alert else 'Irregular rhythm pattern detected'

    if 0 < hrv < 20:
        risk_score = min(100, risk_score + 10)

    risk_score = min(100, max(5, risk_score))

    if risk_score < 30:
        risk_level = 'LOW'
    elif risk_score < 60:
        risk_level = 'MODERATE'
    else:
        risk_level = 'HIGH'

    return risk_score, risk_level, category, alert


@app.route('/api/me/wearable')
def wearable_data():
    """Real data for the /wearable 3D watch: the user's last scan and a 7-day trend."""
    if not current_user.is_authenticated:
        return jsonify({"has_data": False, "reason": "login_required"})

    latest = (HealthMeasurement.query.filter_by(user_id=current_user.id)
              .order_by(HealthMeasurement.timestamp.desc()).first())
    if not latest:
        return jsonify({"has_data": False, "reason": "no_scans"})

    bpm = int(round(latest.bpm))
    risk_score, risk_level, category, _ = score_bpm_risk(bpm)
    sqi_map = {"good": 0.95, "high": 0.95, "fair": 0.70, "medium": 0.70, "poor": 0.40, "low": 0.40}
    sqi = sqi_map.get((latest.signal_quality or "").strip().lower())

    # 7 calendar days ending on the day of the latest scan, daily averages (None = no scan)
    end_day = latest.timestamp.date()
    start_day = end_day - datetime.timedelta(days=6)
    week = (HealthMeasurement.query
            .filter(HealthMeasurement.user_id == current_user.id,
                    HealthMeasurement.timestamp >= datetime.datetime.combine(start_day, datetime.time.min))
            .all())
    buckets = {}
    for m in week:
        buckets.setdefault(m.timestamp.date(), []).append(m.bpm)
    trend = []
    for i in range(7):
        day = start_day + datetime.timedelta(days=i)
        vals = buckets.get(day)
        trend.append({"day": day.strftime('%a')[0],
                      "bpm": round(sum(vals) / len(vals)) if vals else None})
    week_bpms = [m.bpm for m in week]

    return jsonify({
        "has_data": True,
        "bpm": bpm,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "category": category,
        "is_abnormal": bool(latest.is_abnormal),
        "sqi": sqi,
        "source": latest.source,
        "timestamp": latest.timestamp.strftime('%Y-%m-%d %H:%M'),
        "trend": trend,
        "week_count": len(week_bpms),
        "week_peak": round(max(week_bpms)) if week_bpms else None,
    })


@app.route('/api/heartrate/analyze', methods=['POST'])
def heartrate_analyze():
    try:
        d = request.json or {}
        bpm        = int(float(d.get('bpm', 0)))
        hrv        = int(float(d.get('hrv', 0)))
        sqi        = int(float(d.get('sqi', 0)))
        confidence = int(float(d.get('confidence', 0)))
        sig_qual   = d.get('signal_quality', 'low')
        stress     = d.get('stress', 'Normal')
        irregular  = bool(d.get('irregular', False))
        status     = d.get('status', 'measuring')

        risk_score, risk_level, category, alert = score_bpm_risk(bpm, irregular, hrv)

        # Auto SOS trigger for critical thresholds
        auto_sos = bpm >= 160 or bpm < 40 or (bpm >= 140 and irregular)

        return jsonify({
            'bpm': bpm, 'hrv': hrv, 'sqi': sqi,
            'confidence': confidence, 'signal_quality': sig_qual,
            'stress': stress, 'irregular': irregular,
            'risk_score': risk_score, 'risk_level': risk_level,
            'category': category,
            'alert': alert, 'auto_sos': auto_sos,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ══════════════════════════════════════════════════════════════════════════════
#  AI HEALTH ASSISTANT CHAT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        d       = request.json
        message = d.get('message', '').strip()
        history = d.get('history', [])   # [{role, content}, ...]

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # ── Gemini path ────────────────────────────────────────────────────────
        if gemini_model:
            # Build chat history for multi-turn context
            chat_history = []
            for h in history[:-1]:   # exclude current message (already in message)
                role    = 'user' if h['role'] == 'user' else 'model'
                chat_history.append({'role': role, 'parts': [h['content']]})

            chat  = gemini_model.start_chat(history=chat_history)
            reply = chat.send_message(message)
            return jsonify({'reply': reply.text, 'source': 'gemini'})

        # ── Fallback: rule-based health Q&A when API key not set ──────────────
        reply = _fallback_health_qa(message.lower())
        return jsonify({'reply': reply, 'source': 'fallback'})

    except Exception as e:
        err = str(e)
        if 'API_KEY' in err or 'api key' in err.lower():
            return jsonify({'error': 'API key invalid or not configured. Please set GEMINI_API_KEY in .env'}), 401
        return jsonify({'error': err}), 500


def _fallback_health_qa(q):
    """Rule-based fallback when Gemini is not configured."""
    if any(w in q for w in ['heart rate', 'bpm', 'pulse', 'normal heart']):
        return ("**Normal Heart Rate Ranges:**\n\n"
                "- **Adults (resting):** 60–100 BPM\n"
                "- **Athletes:** 40–60 BPM (lower = fitter heart)\n"
                "- **During exercise:** up to 200 BPM depending on age\n\n"
                "A resting HR consistently above 100 (tachycardia) or below 40 (bradycardia) "
                "should be evaluated by a doctor.\n\n"
                "💡 *To get more detailed answers, configure your Gemini API key in `.env`.*")
    if any(w in q for w in ['hrv', 'heart rate variability']):
        return ("**Heart Rate Variability (HRV):**\n\n"
                "HRV measures the variation in time between heartbeats. Higher HRV generally indicates:\n\n"
                "- Better cardiovascular fitness\n- Lower stress levels\n- Good autonomic nervous system balance\n\n"
                "**Typical RMSSD values:**\n- < 20 ms: High stress / poor recovery\n"
                "- 20–50 ms: Moderate\n- > 50 ms: Excellent (athletes)\n\n"
                "💡 *Configure Gemini API key for full AI-powered answers.*")
    if any(w in q for w in ['blood pressure', 'hypertension', 'bp']):
        return ("**Blood Pressure Guide:**\n\n"
                "| Category | Systolic | Diastolic |\n"
                "|---|---|---|\n"
                "| Normal | < 120 | < 80 |\n"
                "| Elevated | 120–129 | < 80 |\n"
                "| High Stage 1 | 130–139 | 80–89 |\n"
                "| High Stage 2 | ≥ 140 | ≥ 90 |\n\n"
                "To lower BP naturally: reduce sodium, exercise regularly, manage stress, limit alcohol.\n\n"
                "💡 *Configure Gemini API key for personalized AI guidance.*")
    if any(w in q for w in ['diet', 'food', 'eat', 'nutrition', 'cholesterol']):
        return ("**Heart-Healthy Diet Tips:**\n\n"
                "- 🐟 Eat fatty fish (salmon, mackerel) 2x/week — rich in omega-3\n"
                "- 🥦 Load up on vegetables & fruits (aim for 5+ servings/day)\n"
                "- 🌾 Choose whole grains over refined carbs\n"
                "- 🫒 Use olive oil instead of butter\n"
                "- 🚫 Limit saturated fats, trans fats, and added sugar\n"
                "- 🧂 Reduce sodium (< 2300 mg/day)\n\n"
                "The **Mediterranean diet** and **DASH diet** are the most evidence-backed for heart health.\n\n"
                "💡 *Configure Gemini API key for personalized meal planning.*")
    if any(w in q for w in ['exercise', 'workout', 'physical', 'activity']):
        return ("**Exercise for Heart Health:**\n\n"
                "- **Cardio:** 150 min/week moderate (brisk walk, cycling, swimming)\n"
                "- **Vigorous:** 75 min/week (jogging, HIIT)\n"
                "- **Strength training:** 2x/week\n\n"
                "**Target HR during exercise:** 50–85% of max HR\n"
                "Max HR ≈ 220 − your age\n\n"
                "Start slow if you're new to exercise. Always warm up and cool down.\n\n"
                "💡 *Configure Gemini API key for personalized exercise plans.*")
    if any(w in q for w in ['heart attack', 'chest pain', 'symptom', 'emergency', 'stroke']):
        return ("**⚠️ Heart Attack Warning Signs:**\n\n"
                "- Chest pain, pressure, or tightness\n"
                "- Pain radiating to arm, jaw, neck, or back\n"
                "- Shortness of breath\n"
                "- Cold sweat, nausea, or lightheadedness\n\n"
                "**🚨 Call 112 immediately if you experience these symptoms.**\n\n"
                "Use the **SOS Emergency** button in PulseGuard AI to alert family and dispatch help.\n\n"
                "💡 *Configure Gemini API key for comprehensive medical guidance.*")
    if any(w in q for w in ['stress', 'anxiety', 'sleep', 'rest']):
        return ("**Stress & Sleep for Heart Health:**\n\n"
                "- **Sleep:** Aim for 7–9 hours/night — poor sleep raises BP and inflammation\n"
                "- **Stress management:** Deep breathing, meditation, yoga proven to lower HR and BP\n"
                "- **HRV** improves significantly with regular relaxation practices\n"
                "- Chronic stress raises cortisol → increases cardiovascular risk\n\n"
                "💡 *Configure Gemini API key for personalized stress management plans.*")
    # Generic fallback
    return ("I'm your **PulseGuard AI Health Assistant**! 🤖\n\n"
            "I can answer questions about:\n"
            "- ❤️ Heart rate & cardiovascular health\n"
            "- 🥗 Heart-healthy diet & nutrition\n"
            "- 🏃 Exercise recommendations\n"
            "- 📊 HRV, blood pressure, cholesterol\n"
            "- ⚕️ Symptoms & when to seek care\n\n"
            "**To unlock full AI-powered responses**, add your free Gemini API key to `.env`:\n"
            "`GEMINI_API_KEY=your_key_here`\n\n"
            "Get a free key at [makersuite.google.com](https://makersuite.google.com/app/apikey)")


# ══════════════════════════════════════════════════════════════════════════════
#  NEWSLETTER  (existing)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    try:
        data  = request.json
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email address is required'}), 400
        send_confirmation_email(email)
        return jsonify({'message': 'Successfully subscribed to the newsletter!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_confirmation_email(email):
    with app.app_context():
        subject      = "Welcome to PulseGuard AI!"
        html_message = render_template('confirmation_email.html', email=email)
        msg = Message(subject, recipients=[email],
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      html=html_message,
                      body="Thank you for subscribing!")
        mail.send(msg)

# ══════════════════════════════════════════════════════════════════════════════
#  LIFE MANAGEMENT SYSTEM — HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_recent_sleep(days=7):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    return [r for r in sleep_records if datetime.datetime.fromisoformat(r['sleep_start']) >= cutoff]

def _get_recent_hr(hours=24):
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
    return [r for r in health_records_store if datetime.datetime.fromisoformat(r['timestamp']) >= cutoff]

def _get_recent_events(days=7):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    return [e for e in calendar_events if datetime.datetime.fromisoformat(e['start_time']) >= cutoff]

def _sleep_quality(hours):
    if hours < 5: return 'poor'
    if hours < 7: return 'average'
    if hours <= 9: return 'good'
    return 'average'

def _calc_work_hours(events):
    total = 0.0
    for e in events:
        if e.get('type') in ('work', 'meeting'):
            try:
                s  = datetime.datetime.fromisoformat(e['start_time'])
                en = datetime.datetime.fromisoformat(e['end_time'])
                total += max(0, (en - s).total_seconds() / 3600)
            except Exception:
                pass
    return round(total, 2)

def _energy_level(avg_sleep, avg_hr):
    if avg_sleep >= 7 and avg_hr <= 85:   return 'high'
    if avg_sleep >= 5 and avg_hr <= 100:  return 'medium'
    return 'low'

def _burnout_score(avg_sleep, avg_work_hrs, avg_hr, poor_days):
    s = 0
    if avg_sleep < 5:      s += 35
    elif avg_sleep < 6:    s += 20
    if avg_work_hrs > 10:  s += 30
    elif avg_work_hrs > 8: s += 15
    if avg_hr > 100:       s += 25
    elif avg_hr > 90:      s += 10
    s += min(10, poor_days * 5)
    return min(100, s)

# ══════════════════════════════════════════════════════════════════════════════
#  SLEEP TRACKING
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/sleep', methods=['POST'])
def log_sleep():
    try:
        d = request.json
        ss, se = d.get('sleep_start'), d.get('sleep_end')
        if not ss or not se:
            return jsonify({'error': 'sleep_start and sleep_end required'}), 400
        s, en = datetime.datetime.fromisoformat(ss), datetime.datetime.fromisoformat(se)
        hours = round((en - s).total_seconds() / 3600, 2)
        if not (0 < hours <= 24):
            return jsonify({'error': 'Invalid sleep duration'}), 400
        rec = {'id': random.randint(100000,999999), 'user_id': d.get('user_id','default_user'),
               'sleep_start': ss, 'sleep_end': se, 'duration': hours,
               'quality': _sleep_quality(hours), 'logged_at': datetime.datetime.now().isoformat()}
        sleep_records.append(rec)
        return jsonify({'message': 'Sleep logged', 'record': rec})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sleep', methods=['GET'])
def get_sleep():
    days = int(request.args.get('days', 7))
    recs = _get_recent_sleep(days)
    avg  = round(sum(r['duration'] for r in recs)/len(recs), 2) if recs else 0
    return jsonify({'records': recs, 'avg_hours': avg,
                    'poor_days': sum(1 for r in recs if r['quality']=='poor'), 'total': len(recs)})

# ══════════════════════════════════════════════════════════════════════════════
#  CALENDAR
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/calendar/event', methods=['POST'])
def add_event():
    try:
        d = request.json
        for f in ['title','start_time','end_time','type']:
            if f not in d: return jsonify({'error': f'{f} required'}), 400
        if d['type'] not in ('work','meeting','rest','sleep','travel','other'):
            return jsonify({'error': 'Invalid event type'}), 400
        event = {'id': random.randint(100000,999999), 'user_id': d.get('user_id','default_user'),
                 'title': d['title'], 'start_time': d['start_time'], 'end_time': d['end_time'],
                 'type': d['type'], 'notes': d.get('notes',''),
                 'created_at': datetime.datetime.now().isoformat()}
        calendar_events.append(event)
        return jsonify({'message': 'Event added', 'event': event})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/calendar/events', methods=['GET'])
def get_events():
    days = int(request.args.get('days', 7))
    evts = _get_recent_events(days)
    return jsonify({'events': evts, 'total': len(evts),
                    'work_hours': _calc_work_hours(evts),
                    'meetings': sum(1 for e in evts if e['type']=='meeting')})

@app.route('/api/calendar/event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    global calendar_events
    before = len(calendar_events)
    calendar_events = [e for e in calendar_events if e['id'] != event_id]
    return jsonify({'message': 'Deleted'} if len(calendar_events) < before else {'error': 'Not found'}), \
           (200 if len(calendar_events) < before else 404)

# ══════════════════════════════════════════════════════════════════════════════
#  ENERGY & BURNOUT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/energy', methods=['GET'])
def energy_status():
    try:
        sr = _get_recent_sleep(1); hr = _get_recent_hr(24)
        avg_s = round(sum(r['duration'] for r in sr)/len(sr),2) if sr else None
        avg_h = round(sum(r['heart_rate'] for r in hr)/len(hr),1) if hr else None
        if avg_s is None or avg_h is None:
            return jsonify({'energy_level':'unknown','message':'Log sleep and measure HR first.'})
        level = _energy_level(avg_s, avg_h)
        tips = {'high':['Schedule deep work now.','Great time for complex tasks.'],
                'medium':['Light tasks recommended.','Break every 45 min.'],
                'low':['Rest recommended.','Avoid strenuous activity.','Hydrate.']}
        return jsonify({'energy_level':level,'avg_sleep_hrs':avg_s,'avg_hr_bpm':avg_h,'suggestions':tips[level]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/burnout', methods=['GET'])
def burnout_check():
    try:
        days = int(request.args.get('days',7))
        sr = _get_recent_sleep(days); hr = _get_recent_hr(days*24); evts = _get_recent_events(days)
        if not sr: return jsonify({'burnout_score':None,'message':'No sleep data available.'})
        avg_s = sum(r['duration'] for r in sr)/len(sr)
        avg_w = _calc_work_hours(evts)/max(1,days)
        avg_h = sum(r['heart_rate'] for r in hr)/len(hr) if hr else 70
        poor  = sum(1 for r in sr if r['quality']=='poor')
        score = _burnout_score(avg_s, avg_w, avg_h, poor)
        level = 'critical' if score>=70 else 'high' if score>=50 else 'moderate' if score>=30 else 'low'
        alerts = []
        if avg_s < 5:  alerts.append('⚠️ Severe sleep deprivation')
        if avg_w > 10: alerts.append('⚠️ Overworking (>10 hrs/day)')
        if avg_h > 100: alerts.append('⚠️ Elevated HR — chronic stress')
        return jsonify({'burnout_score':score,'burnout_level':level,'avg_sleep_hrs':round(avg_s,2),
                        'avg_work_hrs':round(avg_w,2),'avg_hr':round(avg_h,1),
                        'poor_sleep_days':poor,'alerts':alerts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
#  TRAVEL RISK INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/travel/assess', methods=['POST'])
def travel_assess():
    try:
        d = request.json
        dest = d.get('destination','Unknown')
        sr = _get_recent_sleep(7); hr = _get_recent_hr(168); evts = _get_recent_events(7)
        if not sr:
            return jsonify({'travel_status':'UNKNOWN','message':'Log at least 2 days of sleep first.'})
        avg_s = sum(r['duration'] for r in sr)/len(sr)
        poor  = sum(1 for r in sr if r['quality']=='poor')
        avg_h = sum(r['heart_rate'] for r in hr)/len(hr) if hr else 70
        avg_w = _calc_work_hours(evts)/7
        snap  = _burnout_score(avg_s, avg_w, avg_h, poor)
        risky = poor>=2 or avg_s<5 or avg_w>10 or avg_h>100 or snap>70
        status  = 'RISKY' if risky else 'SAFE'
        message = ('⚠️ Travel Risk: High stress/fatigue detected. Rest before travelling.'
                   if risky else '✅ You are fit to travel. Vitals look balanced.')
        tips = (['Rest 1–2 days before travel','Improve sleep quality','Reduce workload']
                if risky else ['Stay hydrated','Carry medications','Monitor HR if unwell'])
        rec = {'user_id':d.get('user_id','default_user'),'destination':dest,
               'travel_date':d.get('travel_date',''),'decision':status,
               'risk_score_snapshot':snap,'assessed_at':datetime.datetime.now().isoformat()}
        travel_records.append(rec)
        return jsonify({'travel_status':status,'message':message,'risk_score':snap,
                        'avg_sleep_hrs':round(avg_s,2),'poor_sleep_days':poor,
                        'avg_hr':round(avg_h,1),'avg_work_hrs_daily':round(avg_w,2),
                        'tips':tips,'record':rec})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
#  AI INSIGHTS + WEEKLY REPORT + LIFE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/insights', methods=['GET'])
def ai_insights():
    try:
        sr=_get_recent_sleep(7); hr=_get_recent_hr(168); evts=_get_recent_events(7)
        if not sr and not hr:
            return jsonify({'insights':[],'message':'Log sleep and HR data first.'})
        avg_s = sum(r['duration'] for r in sr)/len(sr) if sr else None
        avg_h = sum(r['heart_rate'] for r in hr)/len(hr) if hr else None
        avg_w = _calc_work_hours(evts)/7
        poor  = sum(1 for r in sr if r['quality']=='poor') if sr else 0
        insights=[]; alerts=[]
        if avg_s is not None:
            if avg_s<5: insights.append({'type':'warning','msg':'🔴 Critical sleep deprivation (<5 hrs/night).'}); alerts.append('⚠️ Sleep deprivation detected')
            elif avg_s<7: insights.append({'type':'caution','msg':'🟡 Sleep below optimal. Aim 7–9 hrs.'})
            else: insights.append({'type':'good','msg':'🟢 Sleep quality healthy.'})
        if avg_h is not None:
            if avg_h>100: insights.append({'type':'warning','msg':f'🔴 Elevated HR ({avg_h:.0f} BPM avg).'}); alerts.append(f'⚠️ High HR ({avg_h:.0f} BPM)')
            elif avg_h>90: insights.append({'type':'caution','msg':f'🟡 HR trending high ({avg_h:.0f} BPM).'})
            else: insights.append({'type':'good','msg':f'🟢 HR normal ({avg_h:.0f} BPM).'})
        if avg_w>10: insights.append({'type':'warning','msg':f'🔴 Overworking ({avg_w:.1f} hrs/day). Burnout risk HIGH.'})
        elif avg_w>8: insights.append({'type':'caution','msg':f'🟡 Long hours ({avg_w:.1f} hrs/day). Take breaks.'})
        if poor>=3: insights.append({'type':'warning','msg':f'🔴 {poor} nights poor sleep this week.'})
        energy = _energy_level(avg_s or 6, avg_h or 75)
        recovery = max(0,min(100,int(((avg_s or 6)/8)*50+(1-min(1,((avg_h or 75)-60)/60))*50)))
        insights.append({'type':'info','msg':f'⚡ Energy level: {energy.upper()}.'})
        insights.append({'type':'info','msg':f'💊 Recovery score: {recovery}/100.'})
        return jsonify({'insights':insights,'alerts':alerts,'energy_level':energy,
                        'recovery_score':recovery,'avg_sleep_hrs':round(avg_s,2) if avg_s else None,
                        'avg_hr':round(avg_h,1) if avg_h else None,
                        'avg_work_hrs_daily':round(avg_w,2),'disclaimer':'Not for medical diagnosis'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report/weekly', methods=['GET'])
def weekly_report():
    try:
        sr=_get_recent_sleep(7); hr=_get_recent_hr(168); evts=_get_recent_events(7)
        avg_s = round(sum(r['duration'] for r in sr)/len(sr),2) if sr else 0
        avg_h = round(sum(r['heart_rate'] for r in hr)/len(hr),1) if hr else 0
        wh    = _calc_work_hours(evts)
        poor  = sum(1 for r in sr if r['quality']=='poor') if sr else 0
        return jsonify({'period':'7 days','sleep_avg_hrs':avg_s,'poor_sleep_days':poor,
                        'hr_avg_bpm':avg_h,'hr_records':len(hr),'total_work_hours':wh,
                        'meetings':sum(1 for e in evts if e['type']=='meeting'),
                        'energy_level':_energy_level(avg_s,avg_h),
                        'burnout_score':_burnout_score(avg_s,wh/7,avg_h,poor),
                        'recovery_score':max(0,min(100,int((avg_s/8)*50+(1-min(1,(avg_h-60)/60))*50))) if avg_h else 0,
                        'travel_assessments':travel_records[-5:],'health_records':health_records_store[-10:],
                        'generated_at':datetime.datetime.now().isoformat(),'disclaimer':'Not for medical diagnosis'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/life/summary', methods=['GET'])
def life_summary():
    try:
        sr=_get_recent_sleep(1); hr=_get_recent_hr(24); evts=_get_recent_events(1)
        avg_s = round(sum(r['duration'] for r in sr)/len(sr),2) if sr else None
        avg_h = round(sum(r['heart_rate'] for r in hr)/len(hr),1) if hr else None
        wh    = round(_calc_work_hours(evts),2)
        energy = _energy_level(avg_s or 6, avg_h or 75)
        alerts = []
        if avg_s is not None and avg_s<5: alerts.append('⚠️ Less than 5 hrs sleep.')
        if avg_h is not None and avg_h>100: alerts.append(f'⚠️ Elevated HR ({avg_h} BPM).')
        if wh>10: alerts.append('⚠️ Over 10 hrs work today.')
        return jsonify({'sleep_hours':avg_s,'sleep_quality':_sleep_quality(avg_s) if avg_s else None,
                        'heart_rate_avg':avg_h,'latest_reading':hr[-1] if hr else None,
                        'work_hours':wh,'meetings_today':sum(1 for e in evts if e['type']=='meeting'),
                        'energy_level':energy,'alerts':alerts,'disclaimer':'Not for medical diagnosis'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
