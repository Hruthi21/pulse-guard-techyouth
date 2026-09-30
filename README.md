# 🫀 PulseGuard AI (CardioSense.AI)
### *Autonomous Hardware-Free Telecardiology, Optical Arrhythmia Surveillance & Emergency Response Ecosystem*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Backend-Flask%202.3-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![XGBoost](https://img.shields.io/badge/ML%20Engine-XGBoost%202.0-orange.svg?logo=scikitlearn&logoColor=white)](https://xgboost.readthedocs.io/)
[![Computer Vision](https://img.shields.io/badge/Computer%20Vision-Optical%20PPG%20%26%20rPPG-red.svg)](https://en.wikipedia.org/wiki/Photoplethysmogram)
[![Telemedicine](https://img.shields.io/badge/Telehealth-Jitsi%20WebRTC%20Encrypted-green.svg?logo=webrtc&logoColor=white)](https://jitsi.org/)
[![Emergency Telecom](https://img.shields.io/badge/Emergency%20Dispatch-Twilio%20Voice%20%26%20SMS-F22F46.svg?logo=twilio&logoColor=white)](https://www.twilio.com/)
[![Generative AI](https://img.shields.io/badge/Conversational%20AI-Google%20Gemini%20Pro-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 Executive Overview

**PulseGuard AI** (formerly *CardioSense.AI*) is a clinical-grade, zero-hardware cardiovascular monitoring and autonomous telecardiology platform. Built to dismantle the economic and geographic barriers of preventive cardiology, PulseGuard AI transforms any standard smartphone camera or laptop webcam into an optical pulse sensor capable of extracting real-time heart rate, rhythm regularity, and hemodynamic metrics without requiring wearable smartwatches, chest straps, or proprietary medical hardware.

The platform bridges the critical gap between early symptom detection and immediate medical intervention by combining **optical photoplethysmography (PPG)**, **remote facial photoplethysmography (rPPG)**, **gradient-boosted clinical risk modeling (XGBoost 2.0)**, an **interactive hands-free clinical voice assistant**, and an **autonomous closed-loop telecardiology triage network** that automatically dispatches consultation requests and emergency protocols the instant cardiac abnormalities are detected.

---

## 🌍 The Problem: The Global Cardiovascular Crisis

According to the **World Health Organization (WHO)**, Cardiovascular Diseases (CVDs) remain the **#1 cause of death globally**, claiming an estimated **17.9 million lives each year**—representing 32% of all global deaths.

```
       ┌────────────────────────────────────────────────────────┐
       │   17.9M Global Deaths Annually (32% of All Deaths)     │
       └──────────────────────────┬─────────────────────────────┘
                                  │
         ┌────────────────────────┴─────────────────────────┐
         ▼                                                  ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       The Hardware Barrier      │       │      The "Golden Hour" Delay    │
│  Wearables (Apple Watch, etc.)  │       │ Patients delay seeking medical  │
│  cost $300 - $500+, excluding   │       │ care during acute arrhythmias;  │
│  low-income & rural populations.│       │ critical intervention window is │
│                                 │       │ missed before cardiac arrest.   │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

1. **The Cost & Wearable Barrier**: Leading consumer health wearables (Apple Watch, Whoop, Oura Ring) cost between \$300 and \$500+, leaving over 80% of the developing world without continuous cardiac surveillance.
2. **Silent Arrhythmias & Paroxysmal Events**: Dangerous rhythm anomalies such as paroxysmal atrial fibrillation, ventricular premature beats, and sinus tachycardia frequently occur intermittently and remain completely undetected during annual episodic hospital visits.
3. **Emergency Incapacitation**: When acute cardiac events strike, patients often experience dizziness, syncope, or motor trembling, preventing them from manually dialing emergency services or locating nearby medical facilities before losing consciousness.
4. **Physician Bottlenecks & Triage Delays**: Traditional healthcare infrastructure requires manual booking, physical travel, and long wait times, delaying time-to-treatment well beyond the critical "Golden Hour".

---

## 💡 The Solution: How PulseGuard AI Solves This

PulseGuard AI solves these systemic healthcare failures through a **democratized, browser-native cardiovascular defense platform**:

* **Zero-Hardware Vital Acquisition**: Users measure resting heart rate and autonomic tone anywhere in the world using nothing more than their existing mobile browser and rear camera flash.
* **Autonomous Abnormal Vital Triage**: When tachycardia ($\ge 100$ BPM), severe bradycardia ($< 50$ BPM), or rhythm anomalies are detected, the system does not merely display a number—it automatically schedules an encrypted video consultation with the cardiologist (**Dr. Jayanth Gowda**) and dispatches a clinical notification via Gmail SMTP.
* **Hands-Free Voice AI Emergency Triggering**: Patients suffering chest tightness, tremor, or physical distress can trigger optical scans, initiate emergency protocols, or contact their cardiologist completely hands-free via continuous Web Speech natural language commands.
* **Automated Multi-Channel SOS**: In acute distress, the emergency module pulls precise browser GPS coordinates, maps nearby hospitals, and triggers live Twilio voice calls and SMS alerts to designated family members and emergency responders.
* **Actionable Autonomic Recovery Guidance**: Delivers immediate, clinically validated parasympathetic stimulation protocols (4-7-8 vagal breathing coach, Valsalva maneuver, mammalian dive reflex) to safely lower elevated heart rate during panic or supraventricular episodes.

---

## ⚡ How PulseGuard AI Differs From Other Solutions

| Metric / Capability | Traditional Hospital ECG | Commercial Wearables (Apple / Whoop) | Typical AI / ML Demos | 🫀 **PulseGuard AI** |
| :--- | :--- | :--- | :--- | :--- |
| **Hardware Required** | 12-Lead Electrodes & Console | \$300–\$500 Proprietary Wearable | None (CSV upload only) | **Zero Hardware (Camera/Webcam Only)** |
| **Accessibility** | In-clinic visits only | High-income consumer demographic | Developer terminal only | **Instant Universal Web Browser Access** |
| **Sensing Technology** | Direct electrical myocardial signals | Photodiode array on wrist | Static form data only | **Dual Optical PPG (Finger) & rPPG (Face)** |
| **Cardiovascular Risk ML** | Manual physician assessment | Proprietary black-box fitness scores | Simple Logistic Regression | **XGBoost 2.0 (11 Multi-Organ Biomarkers)** |
| **Doctor Dispatch Loop** | Manual booking / referrals | User must call manually | None | **Automated Jitsi WebRTC + Email Dispatch** |
| **Hands-Free Voice AI** | None | Siri/Google (Generic web search) | None | **Medical Voice AI ("Take scan", "Trigger SOS")** |
| **Emergency Automation** | Manual ambulance call | Fall detection on high-end watches | None | **Twilio Voice Call + SMS + Live GPS Radar** |
| **Family Circle Sharing** | Paper printout | Apple Family Share (walled garden) | None | **Tokenized Secure Web Card (`/family/<token>`)** |
| **Cost to End User** | High (\$100–\$1,000+ per visit) | High (\$300+ upfront / subscription) | Free (unusable for patients) | **100% Free & Open-Source** |

---

## 🔥 Key Features & Modules

### 1. 🩻 Hardware-Free Optical PPG & Facial rPPG
* **Rear-Camera Contact PPG**: Users place their index finger over the smartphone camera and LED flash. PulseGuard AI captures red-channel photometric intensity changes as pulsating arterial blood absorbs light, computing pulse rate and rhythm regularity in real time.
* **Facial Remote PPG (rPPG)**: Employs computer vision to isolate regions of interest (ROI) across facial dermis, capturing subtle cardiac micro-blushes frame-by-frame via standard webcams.
* **Signal Quality Index (SQI)**: Real-time waveform rendering on HTML5 Canvas with automated signal-to-noise ratio validation to filter out motion artifacts and ambient light flicker.

### 2. 🩺 Autonomous Teleconsultation & Video Clinic
* **Direct Doctor Dispatch**: Pre-configured with **Dr. Jayanth Gowda** (`jayanthgowda1406@gmail.com`). When an abnormal heart rate scan is recorded, the backend automatically logs an appointment request and dispatches an immediate clinical alert email.
* **Encrypted WebRTC Telehealth**: Integrated with secure **Jitsi Meet** video conferencing rooms (`/videochat/<room_name>`), enabling end-to-end encrypted consultations directly inside the browser.
* **Dedicated Doctor Portal (`/doctor`)**: Clinical dashboard allowing healthcare providers to review incoming appointments, inspect patient vitals and arrhythmia histories, and launch teleconsultations with a single click.

### 3. 🎙️ Hands-Free Clinical Voice Assistant (`voice.js`)
* **Voice-Activated Workflows**:
  * `"take ppg scan"` / `"start heart rate"` $\to$ Automatically navigates to the monitor and starts the camera scan.
  * `"trigger emergency"` / `"sos"` $\to$ Instantly opens the emergency portal and dispatches alerts.
  * `"call doctor"` / `"book appointment"` $\to$ Schedules a consultation with Dr. Jayanth Gowda.
  * `"start breathing"` / `"help me calm down"` $\to$ Initiates the guided 4-7-8 vagal nerve stimulation audio pacer.
  * `"generate report"` $\to$ Compiles and opens the printable health report modal.
* **Trained Clinical Knowledge Base**: Responds to cardiovascular queries regarding tachycardia, bradycardia, angina symptoms, sodium reduction, and medication timing.

### 4. 🚨 GPS-Assisted Emergency SOS & Ambulance Radar
* **HTML5 Geolocation Radar**: Acquires real-time latitude, longitude, and accuracy radius directly from the patient's device browser.
* **Twilio Emergency Voice & SMS Broadcasting**: Automatically fires customized SMS notifications containing live Google Maps coordinates and dispatches automated voice calls to designated emergency contacts.
* **Real-time Hospital Routing**: Renders immediate emergency contact hotlines and calculates proximity routing to nearby trauma centers.

### 5. 🧠 XGBoost 2.0 Cardiovascular Risk Stratification
* **Predictive AI Engine**: High-performance gradient boosted decision tree classifier trained on over 70,000 patient records from the Kaggle Cardiovascular Disease dataset.
* **Multivariate Clinical Input Vector**: Evaluates 11 physiological parameters: Age, Gender, Systolic Blood Pressure (`ap_hi`), Diastolic Blood Pressure (`ap_lo`), Cholesterol (Normal/Above/High), Glucose (Normal/Above/High), Smoking status, Alcohol intake, Physical activity, and BMI.
* **Probabilistic Scoring**: Delivers both a binary risk diagnosis and a calibrated 0–100% cardiovascular disease risk percentage.

### 6. 🤖 24/7 AI Cardiologist Chatbot (`/chat`)
* Powered by Google's **Gemini Pro** generative AI engine, equipped with clinical safety guardrails.
* Provides real-time dietary guidance, medication education, symptom interpretation, and lifestyle modification advice.

### 7. 🥗 Heart-Healthy Diet & Lifestyle Architect (`/diet`, `/lifestyle`)
* **Personalized Nutrition Engine**: Generates customized Mediterranean and DASH diet regimes based on individual risk scores, blood pressure, and cholesterol levels.
* **Autonomic Lifestyle Coaching**: Exercise prescriptions, sleep hygiene recommendations, and daily stress mitigation tactics designed to lower resting sympathetic tone.

### 8. 📄 Automated Health Audits & Tokenized Family Portal
* **Background Scheduling Engine (APScheduler)**: Automatically compiles daily and weekly health digests tracking heart rate trends and risk trajectory.
* **Tokenized Family Health Card (`/family/<token>`)**: Generates secure, read-only dashboard links that patients can share with family members or primary care physicians without exposing account credentials.
* **One-Click Clinical Report Exporter**: Formats vital signs, arrhythmia records, and XGBoost predictions into a clean, printable medical report.

### 9. ⌚ PulseGuard Wear: 3D Interactive Studio & 9-Layer Teardown (`/wearable`)
* **Real-Time WebGL 3D Model**: Fully interactive Three.js rendered device simulating continuous PPG heart rate monitoring, motion classification (Resting vs. Brisk Walk vs. Workout vs. Resting Tachycardia), and one-press SOS triggering.
* **Customizable Hardware Aesthetics**: Switch between 44mm Watch and Slim Band form factors, customize case metals (Graphite, Silver, Titanium Gold), and change fluoroelastomer straps (Obsidian, Pulse Red, Sage, Sand, Glacier).
* **Scroll-Driven 9-Layer Engineering Teardown**: Scroll-activated exploded 3D view detailing all 9 physical layers (Sapphire Cover Glass, Capacitive Touch Grid, 1000-nit AMOLED, Aluminum Unibody Midframe, 8-layer HDI Logic Board, Li-ion Battery Cell, Optical PPG Sensor Module, Zirconia Ceramic Back, and Quick-Release Strap).

---

## 🔬 Mathematical, Algorithmic & Model Architecture

```
                                  PULSEGUARD AI DATAFLOW PIPELINE
                                  
  ┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
  │ Camera Feed      │       │ Red-Channel Photon   │       │ Dynamic Threshold    │
  │ (Finger on Flash │ ────► │ Volumetric Variance  │ ────► │ Peak Detection &     │
  │  or Face Video)  │       │ I(t) = I0 * e^(-εcd) │       │ Inter-Beat Intervals │
  └──────────────────┘       └──────────────────────┘       └──────────┬───────────┘
                                                                       │
                                                            Heart Rate (BPM) & SQI
                                                                       │
                                                                       ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                           AUTONOMIC CLASSIFICATION ENGINE                              │
  ├─────────────────────────────────┬──────────────────────────────────────────────────────┤
  │ Critical Tachycardia (≥140 BPM) │ Immediate Doctor Email Alert + Emergency SOS Trigger │
  │ Moderate Tachycardia (120-139)  │ Auto-Consultation Booking + Vagal 4-7-8 Breathing    │
  │ Mild Tachycardia (101-119 BPM)  │ Clinical Rest Protocol + Hydration Guidance          │
  │ Normal Sinus Rhythm (60-100)    │ Optimal Homeostasis Verified                         │
  │ Mild Bradycardia (50-59 BPM)    │ Athletic / Non-critical Monitoring Check             │
  │ Severe Bradycardia (<50 BPM)    │ Syncope Precaution + Clinical Telehealth Alert       │
  └─────────────────────────────────┴──────────────────────────────────────────────────────┘
                                                                       │
                                                                       ▼
  ┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
  │ Multivariate     │       │ XGBoost 2.0          │       │ Encrypted Telehealth │
  │ Clinical Patient │ ────► │ Gradient-Boosted     │ ────► │ & Twilio Emergency   │
  │ Indicators (11)  │       │ Decision Trees       │       │ Multi-Channel Relay  │
  └──────────────────┘       └──────────────────────┘       └──────────────────────┘
```

### 1. Photoplethysmography (PPG) Signal Processing
Optical pulse measurement relies on the **Beer-Lambert Law** of light absorption across biological tissue:

$$I(t) = I_0 \cdot e^{-\epsilon(\lambda) \cdot c \cdot d(t)}$$

Where:
* $I_0$ = Incident light intensity from device flash.
* $\epsilon(\lambda)$ = Extinction coefficient of oxygenated hemoglobin at wavelength $\lambda \approx 660\text{ nm}$ (red spectrum).
* $c$ = Concentration of hemoglobin in cutaneous capillaries.
* $d(t) = d_0 + \Delta d(t)$ = Time-varying arterial blood path length modulated by each cardiac ejection fraction.

**Algorithmic Peak Detection Pipeline**:
1. **Photometric Extraction**: Frames are sampled at 30 FPS. The raw mean intensity of the red color plane $R(t)$ is extracted across the sensor ROI.
2. **Bandpass Filtering**: A moving-average baseline filter removes low-frequency respiratory drift and baseline wander (0.5–3.5 Hz passband corresponding to 30–210 BPM).
3. **Dynamic Threshold Peak Identification**: Local maxima are detected where $R(t) > \mu_{window} + k \cdot \sigma_{window}$.
4. **Signal Quality Index (SQI)**: Calculated using the coefficient of variation of successive inter-beat ($R-R$) intervals:

$$SQI = 1 - \frac{\sigma_{RR}}{\mu_{RR}}$$

If $SQI \ge 0.70$, the measurement is validated as clinically representative.

### 2. XGBoost 2.0 Risk Classifier
* **Objective Function**: Binary Logistic Loss with $L_1$ and $L_2$ regularization:

$$\mathcal{L}(\theta) = \sum_{i=1}^n \left[ y_i \ln(1 + e^{-\hat{y}_i}) + (1 - y_i) \ln(1 + e^{\hat{y}_i}) \right] + \gamma T + \frac{1}{2} \lambda \sum_{j=1}^T w_j^2$$

* **Hyperparameters**:
  * Base Estimators: 300 Trees
  * Max Tree Depth: 6
  * Learning Rate ($\eta$): 0.05
  * Subsample Ratio: 0.85
  * Colsample by Tree: 0.80
* **Feature Importance Ranking**:
  1. Systolic Blood Pressure (`ap_hi`)
  2. Age (scaled in years)
  3. Diastolic Blood Pressure (`ap_lo`)
  4. Cholesterol Level
  5. Body Mass Index ($BMI = \frac{\text{weight}_{kg}}{\text{height}_m^2}$)
  6. Fasting Glucose Level

---

## 🗂️ Project Directory & File Structure

```
CardioSense.AI_Backend/
├── app.py                         # Primary Flask application: auth, routes, clinical engines
├── requirements.txt               # Pinned Python package dependencies
├── .env                           # Local environment secrets (SMTP, Twilio, Gemini)
├── xgboost2.0_model.pkl           # Pre-trained XGBoost 2.0 classification model
├── database.db                    # SQLite clinical database (Users, Measurements, Consults)
├── static/                        # Frontend assets, stylesheets, scripts & audio
│   ├── index.js                   # Client-side validation & risk form controllers
│   ├── ppg_engine.js              # Hardware-free optical PPG / rPPG computer vision engine
│   ├── voice.js                   # Hands-free Medical Voice AI & 4-7-8 breathing pacer
│   ├── pulseguard.css             # PulseGuard AI modern medical design system
│   ├── styles.css                 # Supplemental layout styling
│   └── images/                    # Icons, logos, and medical vector graphics
└── templates/                     # Jinja2 HTML templates
    ├── index.html                 # Hero landing page & capability showcase
    ├── dashboard.html             # Patient command center, vitals overview & analytics
    ├── heartrate.html             # Real-time Optical Finger PPG & rPPG scanner suite
    ├── appointments.html          # Doctor video consult scheduling & history
    ├── doctor_dashboard.html      # Physician triage portal for Dr. Jayanth Gowda
    ├── emergency.html             # GPS SOS radar, Twilio dispatch & hospital routing
    ├── reports.html               # Longitudinal medical reports & print generator
    ├── family_card.html           # Secure tokenized relative health card
    ├── chat.html                  # 24/7 Gemini-powered AI cardiology consultation
    ├── diet.html                  # Personalized DASH / Mediterranean meal planner
    ├── lifestyle.html             # Cardiovascular exercise & lifestyle habits coach
    ├── videochat.html             # Jitsi Meet encrypted WebRTC teleconsultation room
    ├── wearable.html              # PulseGuard Wear 3D interactive model & 9-layer teardown
    ├── login.html                 # Patient / physician authentication portal
    ├── register.html              # Account registration with baseline demographics
    └── newsletter.html            # Preventive heart health educational dispatch
```

---

## 🛠️ Tech Stack & Dependencies

| Layer | Technologies |
| :--- | :--- |
| **Core Backend** | Python 3.10+, Flask 2.3.3, Gunicorn 21.2 |
| **Machine Learning** | XGBoost 2.0.3, Scikit-Learn, NumPy, Pandas, Joblib |
| **Generative AI** | Google Gemini Pro (`google-generativeai` 0.8.6) |
| **Database & ORM** | SQLite, Flask-SQLAlchemy 3.1.1, Flask-Login, Flask-Bcrypt |
| **Computer Vision / Bio-Sensing** | HTML5 MediaDevices API, Canvas API, Real-time Optical PPG Filters |
| **Telehealth & Real-time Video** | Jitsi Meet WebRTC (End-to-End Encrypted) |
| **Telecommunications & SOS** | Twilio REST API (Programmable SMS & Voice Calls) |
| **Email Dispatch** | Flask-Mail 0.9.1 (Gmail SMTP Integration) |
| **Automated Job Scheduling** | APScheduler 3.10.4 (Background health audits & digests) |
| **Frontend Framework** | Semantic HTML5, CSS3 Custom Properties, JavaScript ES6+, Web Speech API |

---

## 🚀 Installation & Local Deployment Guide

### Prerequisites
* **Python 3.10 or higher** installed on your system.
* A device with a **webcam** or **smartphone camera with LED flashlight**.
* Modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari) with camera, microphone, and location permissions enabled.

### 1. Clone the Repository
```bash
git clone https://github.com/jayanthdr07/CardioSense.AI_Backend.git
cd CardioSense.AI_Backend
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and configure your service credentials:

```ini
# Flask Security
SECRET_KEY=your_super_secret_session_key

# Gmail SMTP Dispatch (Automated Doctor Alerts)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_gmail_address@gmail.com
MAIL_PASSWORD=your_gmail_app_password

# Twilio Emergency SOS (Live Voice Calls & SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1XXXXXXXXXX

# Emergency Responder Numbers (E.164 format)
EMERGENCY_CONTACT_1_NAME="Family Primary"
EMERGENCY_CONTACT_1_PHONE=+91XXXXXXXXXX
EMERGENCY_CONTACT_2_NAME="Emergency Driver"
EMERGENCY_CONTACT_2_PHONE=+91XXXXXXXXXX

# Google Gemini AI (Cardiology Assistant)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Initialize the Database & Run the Application
```bash
python app.py
```

The application will initialize the SQLite schema and start the local development server at:
👉 **`http://127.0.0.1:5000`**

> [!TIP]
> To access camera and microphone features from a secondary device (e.g., your smartphone on the same local Wi-Fi network), access the host computer's local IP (e.g. `http://192.168.1.X:5000`) or use an SSL reverse proxy (such as ngrok or cloudflare tunnel) to grant browser camera permissions over HTTPS.

---

## 🗣️ Voice Assistant Command Reference

PulseGuard AI features a continuous, trained clinical voice assistant. Click **"Voice AI"** in the bottom floating dock to toggle listening mode, or issue any of the following natural commands:

| Voice Command | Triggered Action |
| :--- | :--- |
| `"take ppg scan"` / `"start scan"` | Automatically opens the PPG monitor and activates camera pulse scanning |
| `"trigger emergency"` / `"sos"` / `"call ambulance"` | Launches emergency protocol, triggers GPS radar, and initiates Twilio alerts |
| `"call doctor"` / `"book consultation"` | Dispatches teleconsultation request to Dr. Jayanth Gowda |
| `"start breathing"` / `"help me calm down"` | Activates the interactive 4-7-8 parasympathetic vagal nerve breathing guide |
| `"generate report"` / `"print report"` | Opens the comprehensive clinical summary report ready for export |
| `"open dashboard"` / `"go to dashboard"` | Navigates directly to your personalized analytics center |
| `"tell me about tachycardia"` / `"is my heart rate bad?"` | Speaks clinically vetted arrhythmia definitions and guidance |

---

## ⚕️ Clinical Precaution & Medical Disclaimer

> [!WARNING]
> **PulseGuard AI is an investigational health technology and predictive triage aid.**
> 
> * It is designed for **early risk screening, home monitoring, and preventive lifestyle support**, and does **not** replace diagnostic 12-lead electrocardiography (ECG), clinical ultrasound, or direct physical examination by a licensed cardiologist.
> * If you experience severe crushing chest pain, radiating left arm numbness, acute shortness of breath, unexplained fainting (syncope), or cyanosis, immediately dial your local emergency services (**112 in India, 911 in North America, 999 in the UK**) or proceed to the nearest hospital emergency room.

---

## 👥 Contributors & Acknowledgements

* **Lead Architect & Developer**: Jayanth D R ([@jayanthdr07](https://github.com/jayanthdr07))
* **Consulting Telecardiologist**: Dr. Jayanth Gowda (`jayanthgowda1406@gmail.com`)
* **Core Research & Machine Learning**: Team Debuggers
* **Datasets & Reference Benchmarks**: Kaggle Cardiovascular Disease Dataset (70,000 anonymized clinical records)

---

## 📜 License
This project is distributed under the terms of the **MIT License**. See [LICENSE](LICENSE) for full details.
