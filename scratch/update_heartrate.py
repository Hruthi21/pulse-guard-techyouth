import re

with open('templates/heartrate.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Print and Modal Styles to the <style> block
report_styles = """
/* ── Medical Report & Clinical Feedback Modal Styles ─────────────── */
#clinicalReportModal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.88);
  backdrop-filter: blur(10px);
  z-index: 100000;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.report-modal-sheet {
  background: #0d0f17;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  max-width: 820px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.8);
  padding: 30px;
  color: #fff;
  position: relative;
}

.report-header-band {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 18px;
  margin-bottom: 20px;
}

.report-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin: 18px 0;
}

.report-kpi-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}

.report-rec-box {
  background: rgba(255, 255, 255, 0.02);
  border-left: 4px solid var(--primary);
  border-radius: 8px;
  padding: 14px 18px;
  margin: 16px 0;
  font-size: 13px;
  line-height: 1.6;
}

@media print {
  body * { visibility: hidden; }
  #clinicalReportModal, #clinicalReportModal * { visibility: visible; }
  #clinicalReportModal {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: auto;
    background: #fff !important;
    color: #000 !important;
    padding: 0;
  }
  .report-modal-sheet {
    background: #fff !important;
    color: #000 !important;
    border: none !important;
    box-shadow: none !important;
    padding: 20px;
    max-width: 100%;
  }
  .modal-actions-bar { display: none !important; }
}
"""

if "/* ── Medical Report & Clinical Feedback Modal Styles" not in html:
    html = html.replace('</style>', report_styles + '\n</style>')

# 2. Add the On-Page Medical Feedback Card right after FINGER PPG ROW
on_page_card = """
    <!-- ── ON-PAGE MEDICAL FEEDBACK CARD (Appears automatically after scan) ── -->
    <div class="card fade-in" id="onPageMedicalFeedback" style="display:none; margin-bottom:24px; border-left: 4px solid #2ecc71;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
        <h3 style="margin:0; font-size:18px; display:flex; align-items:center; gap:8px;">
          <i class="fas fa-notes-medical" style="color:#2ecc71;"></i> Clinical Medical Feedback & Interpretation
        </h3>
        <div style="display:flex; gap:10px;">
          <button onclick="reopenReportModal()" class="btn-primary" style="padding:6px 14px; font-size:12px; font-weight:700;">
            <i class="fas fa-file-medical-alt"></i> View Full Clinical Report
          </button>
        </div>
      </div>

      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:14px; margin-bottom:16px;">
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:12px; border-radius:10px;">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase; font-weight:700;">Cardiac Rhythm</div>
          <div style="font-size:16px; font-weight:800; margin-top:4px;" id="fb-rhythm-cat">Normal Sinus Rhythm</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:12px; border-radius:10px;">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase; font-weight:700;">Autonomic Tone</div>
          <div style="font-size:14px; font-weight:700; margin-top:4px;" id="fb-autonomic">Balanced Homeostasis</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:12px; border-radius:10px;">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase; font-weight:700;">Myocardial Workload</div>
          <div style="font-size:14px; font-weight:700; margin-top:4px;" id="fb-workload">Optimal Range</div>
        </div>
      </div>

      <div id="fb-summary-text" style="font-size:13.5px; color:#ccc; line-height:1.6; margin-bottom:14px; background:rgba(255,255,255,0.02); padding:12px 14px; border-radius:8px;"></div>
      
      <div style="font-size:12px; font-weight:700; color:var(--primary); margin-bottom:8px;">
        <i class="fas fa-stethoscope"></i> Actionable Medical Recommendations:
      </div>
      <ul id="fb-recs-list" style="margin:0; padding-left:20px; font-size:13px; color:#bbb; line-height:1.8;"></ul>
    </div>
"""

if "<!-- ── ON-PAGE MEDICAL FEEDBACK CARD" not in html:
    html = html.replace('<!-- FINGER PPG ROW -->', on_page_card + '\n    <!-- FINGER PPG ROW -->')

# 3. Add Clinical Report Modal HTML right before `</main>`
modal_html = """
  <!-- ── Comprehensive Clinical Screening Report Modal ──────────────── -->
  <div id="clinicalReportModal">
    <div class="report-modal-sheet">
      <!-- Header -->
      <div class="report-header-band">
        <div>
          <div style="font-size:11px; text-transform:uppercase; letter-spacing:1px; color:#2ecc71; font-weight:800;">
            PulseGuard AI &bull; Clinical Telecardiology
          </div>
          <h2 style="margin:4px 0 2px; font-size:22px;">Photoplethysmography (PPG) Screening Report</h2>
          <div style="font-size:12px; color:var(--muted);">Automated Hemodynamic & Autonomic Assessment</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:12px; color:#888;">Date: <strong style="color:#fff;" id="modal-report-date">--</strong></div>
          <div style="font-size:12px; color:#888;">Patient: <strong style="color:#fff;">{{ current_user.full_name }}</strong></div>
          <div style="font-size:11px; color:#888;">ID: PG-{{ current_user.id }} &bull; Source: <span id="modal-report-source">Camera PPG</span></div>
        </div>
      </div>

      <!-- Core Metrics Row -->
      <div class="report-kpi-grid">
        <div class="report-kpi-box">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase;">Heart Rate</div>
          <div style="font-size:24px; font-weight:800;" id="modal-bpm-val">-- <span style="font-size:12px;">BPM</span></div>
          <div style="font-size:11px;" id="modal-rhythm-badge">--</div>
        </div>
        <div class="report-kpi-box">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase;">Signal Quality (SQI)</div>
          <div style="font-size:20px; font-weight:800; color:#2ecc71;" id="modal-sqi-val">Good</div>
          <div style="font-size:11px; color:#888;">Photometric Variance</div>
        </div>
        <div class="report-kpi-box">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase;">Autonomic State</div>
          <div style="font-size:15px; font-weight:700; margin-top:4px;" id="modal-autonomic-val">Balanced</div>
          <div style="font-size:11px; color:#888;">Sympathovagal Ratio</div>
        </div>
        <div class="report-kpi-box">
          <div style="font-size:11px; color:var(--muted); text-transform:uppercase;">Cardiac Workload</div>
          <div style="font-size:15px; font-weight:700; margin-top:4px;" id="modal-workload-val">Normal</div>
          <div style="font-size:11px; color:#888;">Myocardial O2 Demand</div>
        </div>
      </div>

      <!-- Clinical Findings -->
      <div style="margin: 18px 0;">
        <h4 style="margin:0 0 8px; font-size:14px; text-transform:uppercase; letter-spacing:0.5px; color:#2ecc71;">
          <i class="fas fa-stethoscope"></i> Clinical Interpretation & Physiological Assessment
        </h4>
        <div id="modal-clinical-summary" style="font-size:13.5px; color:#ddd; line-height:1.6; background:rgba(255,255,255,0.03); padding:14px; border-radius:10px; border:1px solid rgba(255,255,255,0.05);">
        </div>
      </div>

      <!-- Actionable Medical Recommendations -->
      <div class="report-rec-box" id="modal-rec-box">
        <h4 style="margin:0 0 6px; font-size:13.5px; color:#fff;">
          <i class="fas fa-check-circle" style="color:#2ecc71;"></i> Actionable Medical Protocols:
        </h4>
        <ul id="modal-recs-list" style="margin:0; padding-left:20px;"></ul>
      </div>

      <!-- Red Flag Warning -->
      <div style="background:rgba(231,76,60,0.1); border:1px solid rgba(231,76,60,0.3); padding:12px 16px; border-radius:8px; font-size:12px; color:#e74c3c; line-height:1.5; margin-bottom:20px;">
        <strong>⚠️ Clinical Precaution:</strong> This automated analysis is generated from optical photoplethysmography and AI signal processing for cardiovascular screening. It is not an alternative to an in-person 12-lead ECG. If experiencing chest pain, pressure, lightheadedness, or shortness of breath, dial 112 immediately.
      </div>

      <!-- Modal Action Buttons Bar -->
      <div class="modal-actions-bar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; border-top:1px solid rgba(255,255,255,0.08); padding-top:16px;">
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <a href="/appointments" class="btn-primary" style="background:#2ecc71; color:#fff; text-decoration:none; padding:10px 18px; border-radius:8px; font-weight:700; font-size:13px; display:inline-flex; align-items:center; gap:6px;">
            <i class="fas fa-video"></i> Consult Cardiologist Now
          </a>
          <button onclick="window.print()" style="background:rgba(255,255,255,0.08); color:#fff; border:1px solid rgba(255,255,255,0.15); padding:10px 16px; border-radius:8px; font-weight:600; font-size:13px; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
            <i class="fas fa-print"></i> Print / PDF Report
          </button>
          <button onclick="emailReportToRelative()" style="background:#3498db; color:#fff; border:none; padding:10px 16px; border-radius:8px; font-weight:600; font-size:13px; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
            <i class="fas fa-envelope"></i> Email to Relative
          </button>
        </div>
        <button onclick="closeClinicalReport()" style="background:transparent; color:#888; border:1px solid #444; padding:8px 16px; border-radius:8px; font-size:13px; cursor:pointer;">
          Close
        </button>
      </div>
    </div>
  </div>
"""

if "<!-- ── Comprehensive Clinical Screening Report Modal" not in html:
    html = html.replace('</main>', modal_html + '\n</main>')

# 4. Add the JavaScript functions for medical feedback and report generation
js_code = """
// ── Comprehensive Medical Clinical Report Engine ───────────────────────────
let currentReportData = null;

function getClinicalInterpretation(bpm) {
    if (bpm < 60) {
        return {
            category: "Sinus Bradycardia (Low Resting Rate)",
            color: "#f39c12",
            tone: "Vagal Dominance / Parasympathetic High Output",
            workload: "Low Cardiac Demand",
            summary: "Your resting heart rate is below the 60 BPM baseline threshold. In endurance athletes, this is a physiological marker of superior stroke volume efficiency. In non-athletic adults, sustained bradycardia can reduce systemic perfusion if accompanied by fatigue or syncope.",
            recommendations: [
                "Drink 300ml water with electrolytes to maintain optimum vascular stroke volume.",
                "Rise slowly from recumbent positions to avoid orthostatic dizziness.",
                "If dizziness, visual darkness, or lightheadedness occurs, consult a physician."
            ],
            isAbnormal: true
        };
    } else if (bpm <= 100) {
        return {
            category: "Normal Sinus Rhythm (Optimal Resting Range)",
            color: "#2ecc71",
            tone: "Balanced Autonomic Homeostasis",
            workload: "Optimal Hemodynamic Equilibrium",
            summary: "Your heart rate is in the healthy physiological adult resting range (60 - 100 BPM). Sinoatrial nodal firing is in ideal equilibrium with myocardial oxygen demand.",
            recommendations: [
                "Maintain 150 minutes of moderate aerobic conditioning weekly.",
                "Preserve sleep hygiene to protect autonomic cardiovascular circadian stability.",
                "Maintain consistent hydration and a balanced Mediterranean-style diet."
            ],
            isAbnormal: false
        };
    } else if (bpm <= 139) {
        return {
            category: "Sinus Tachycardia (Elevated Cardiac Activity)",
            color: "#e67e22",
            tone: "Sympathetic Adrenergic Dominance",
            workload: "Elevated Myocardial Oxygen Consumption",
            summary: "Your heart rate is elevated above the 100 BPM resting limit. This indicates adrenergic sympathetic activation, psychological stress, dehydration, caffeine intake, or metabolic surge.",
            recommendations: [
                "Perform 4-7-8 Vagal Breathing: Inhale 4s, hold 7s, exhale 8s to stimulate the vagus nerve brake.",
                "Drink 300-500ml cold water immediately to support central blood volume.",
                "Sit with back supported, legs uncrossed, and rest quietly for 10 minutes.",
                "Avoid caffeine, tobacco, nicotine, and intense exertion for the next 2 hours."
            ],
            isAbnormal: true
        };
    } else {
        return {
            category: "Critical Tachycardia / Acute Arrhythmia Risk",
            color: "#e74c3c",
            tone: "Critical Adrenergic Surge / Tachyarrhythmia Risk",
            workload: "Critically High Myocardial Strain",
            summary: "Your heart rate is markedly elevated (>= 140 BPM). At this velocity, ventricular diastole filling time is significantly reduced, elevating myocardial wall tension.",
            recommendations: [
                "Cease all movement immediately and sit in a cool, supported posture.",
                "Connect with a cardiologist or emergency physician immediately for live video triage.",
                "RED FLAG: If accompanied by chest tightness, pressure, radiating jaw/arm pain, or dyspnea, call 112 immediately."
            ],
            isAbnormal: true
        };
    }
}

function showClinicalMedicalReport(bpm, source, quality, bp, risk) {
    const info = getClinicalInterpretation(bpm);
    const now = new Date();
    const dateStr = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();

    currentReportData = { bpm, source, quality, info, dateStr };

    // 1. Update On-Page Feedback Card
    const onPage = document.getElementById('onPageMedicalFeedback');
    if (onPage) {
        onPage.style.display = 'block';
        onPage.style.borderLeftColor = info.color;
        document.getElementById('fb-rhythm-cat').textContent = info.category;
        document.getElementById('fb-rhythm-cat').style.color = info.color;
        document.getElementById('fb-autonomic').textContent = info.tone;
        document.getElementById('fb-workload').textContent = info.workload;
        document.getElementById('fb-summary-text').innerHTML = `<strong>Physiological Analysis:</strong> ${info.summary}`;
        
        const recList = document.getElementById('fb-recs-list');
        recList.innerHTML = info.recommendations.map(r => `<li>${r}</li>`).join('');
    }

    // 2. Update Modal Fields
    document.getElementById('modal-report-date').textContent = dateStr;
    document.getElementById('modal-report-source').textContent = source || 'Smartphone PPG';
    document.getElementById('modal-bpm-val').innerHTML = `${bpm} <span style="font-size:12px; color:var(--muted);">BPM</span>`;
    document.getElementById('modal-bpm-val').style.color = info.color;
    
    document.getElementById('modal-rhythm-badge').textContent = info.category;
    document.getElementById('modal-rhythm-badge').style.color = info.color;
    
    document.getElementById('modal-sqi-val').textContent = quality || 'Good';
    document.getElementById('modal-autonomic-val').textContent = info.tone;
    document.getElementById('modal-workload-val').textContent = info.workload;
    
    document.getElementById('modal-clinical-summary').innerHTML = info.summary;
    
    const modalRecs = document.getElementById('modal-recs-list');
    modalRecs.innerHTML = info.recommendations.map(r => `<li style="margin-bottom:6px;">${r}</li>`).join('');
    
    // Show Modal
    const modal = document.getElementById('clinicalReportModal');
    if (modal) modal.style.display = 'flex';

    // Optional voice announcement
    if (typeof speak === 'function') {
        speak(`Scan complete. Heart rate is ${bpm} beats per minute. ${info.category}. Your clinical report is ready.`);
    }
}

function closeClinicalReport() {
    const modal = document.getElementById('clinicalReportModal');
    if (modal) modal.style.display = 'none';
}

function reopenReportModal() {
    const modal = document.getElementById('clinicalReportModal');
    if (modal) modal.style.display = 'flex';
}

function emailReportToRelative() {
    fetch('/api/health/share_card', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            alert(data.status === 'success' ? '✅ Clinical report link emailed to your relative!' : 'Notice: ' + (data.message || data.error));
        })
        .catch(() => alert('Error sending report email.'));
}
"""

if "function showClinicalMedicalReport" not in html:
    html = html.replace('// ── update UI ─────────────────────────────────────────────────────────────────', js_code + '\n// ── update UI ─────────────────────────────────────────────────────────────────')

# Hook into finishFingerPPG
html = html.replace("showToast(\"Measurement saved to your profile!\", \"success\");",
                    "showToast(\"Measurement saved to your profile!\", \"success\");\n        showClinicalMedicalReport(avgBpm, 'Finger Camera PPG', ppgQuality, null, null);")

# Hook into updateMetricsFromAPI
html = html.replace("updateMetricsFromAPI(data);",
                    "updateMetricsFromAPI(data);\n                if (data.bpm) showClinicalMedicalReport(Math.round(data.bpm), 'Face rPPG', 'Good', data.estimated_bp, data.risk_score);")

with open('templates/heartrate.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Successfully injected clinical medical report and feedback engine into heartrate.html")
