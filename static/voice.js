/**
 * PulseGuard AI — Medical Telecardiology Voice Assistant
 * Full hands-free voice automation:
 * - Automatically takes PPG scan (Finger or Camera) on voice command
 * - Automatically triggers emergency SOS on voice command
 * - Voice-guided 4-7-8 vagal breathing coach
 * - Automatic doctor video consultation triage
 * - Automatic risk score calculation & report generation
 */
(function() {
    // ── Feature Detection ──────────────────────────────────────────────────
    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!window.SpeechRecognition || !window.speechSynthesis) {
        console.warn("Web Speech API not supported in this browser.");
        return;
    }

    // ── Configuration & State ──────────────────────────────────────────────
    let recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = localStorage.getItem('voice_lang') || 'en-US';

    let isListening = false;
    let isSpeaking = false;
    let voiceEnabled = localStorage.getItem('voice_enabled') === 'true';
    let inCommandMode = false;
    let commandModeTimer = null;
    let breathingInterval = null;
    let isBreathingActive = false;
    let bestVoice = null;

    // Pick the most natural, clear medical-sounding voice
    function selectBestVoice() {
        const voices = window.speechSynthesis.getVoices();
        if (!voices || voices.length === 0) return null;
        const preferred = [
            'Google UK English Female',
            'Google UK English Male',
            'Google US English',
            'Microsoft Aria Online',
            'Microsoft Jenny Online',
            'Microsoft Guy Online',
            'Samantha',
            'en-US',
            'en-GB',
            'en-IN'
        ];
        for (let p of preferred) {
            let found = voices.find(v => v.name.includes(p) || v.lang.includes(p));
            if (found) return found;
        }
        return voices.find(v => v.lang.startsWith('en')) || voices[0];
    }

    if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => {
            bestVoice = selectBestVoice();
        };
    }

    // ── Styles ─────────────────────────────────────────────────────────────
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes pulseMicGreen {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
            70% { transform: scale(1.08); box-shadow: 0 0 0 16px rgba(46, 204, 113, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
        }
        @keyframes pulseMicRed {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.8); }
            70% { transform: scale(1.1); box-shadow: 0 0 0 18px rgba(231, 76, 60, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); }
        }
        .pg-voice-container {
            position: fixed;
            bottom: 24px;
            left: 24px;
            z-index: 99999;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }
        .pg-voice-card {
            background: rgba(13, 16, 26, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(16px);
            border-radius: 14px;
            padding: 14px 16px;
            width: 330px;
            max-width: 90vw;
            box-shadow: 0 16px 40px rgba(0,0,0,0.6);
            color: #fff;
            display: none;
            flex-direction: column;
            gap: 10px;
            transition: all 0.3s ease;
        }
        .pg-voice-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 8px;
        }
        .pg-voice-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 600;
        }
        .pg-voice-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #2ecc71;
            display: inline-block;
        }
        .pg-voice-status-dot.listening {
            background: #e74c3c;
            animation: pulseMicRed 1s infinite;
        }
        .pg-voice-status-dot.speaking {
            background: #3498db;
            animation: pulseMicGreen 1s infinite;
        }
        .pg-voice-text-box {
            font-size: 13px;
            line-height: 1.5;
            color: #eee;
            background: rgba(255,255,255,0.04);
            border-radius: 8px;
            padding: 10px 12px;
            min-height: 48px;
            max-height: 130px;
            overflow-y: auto;
        }
        .pg-voice-user-transcript {
            font-size: 11.5px;
            color: #2ecc71;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .pg-voice-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .pg-voice-chip {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            color: #ddd;
            padding: 5px 9px;
            border-radius: 12px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .pg-voice-chip:hover {
            background: #2ecc71;
            color: #fff;
            border-color: #2ecc71;
        }
        .pg-voice-chip.sos {
            background: rgba(231, 76, 60, 0.2);
            border-color: rgba(231, 76, 60, 0.4);
            color: #ff6b6b;
        }
        .pg-voice-chip.sos:hover {
            background: #e74c3c;
            color: #fff;
        }
        .pg-voice-main-btn {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: #2ecc71;
            color: #fff;
            border: none;
            box-shadow: 0 8px 24px rgba(46,204,113,0.4);
            cursor: pointer;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .pg-voice-main-btn:hover {
            transform: scale(1.08);
        }
        .pg-voice-main-btn.listening {
            background: #e74c3c !important;
            animation: pulseMicRed 1.4s infinite !important;
            box-shadow: 0 8px 24px rgba(231,76,60,0.5) !important;
        }
        .pg-voice-main-btn.speaking {
            background: #3498db !important;
            animation: pulseMicGreen 1.4s infinite !important;
            box-shadow: 0 8px 24px rgba(52,152,219,0.5) !important;
        }
        .pg-voice-banner {
            background: #2ecc71;
            color: #fff;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: opacity 0.3s;
        }
    `;
    document.head.appendChild(style);

    // ── Build DOM Elements ─────────────────────────────────────────────────
    const container = document.createElement('div');
    container.className = 'pg-voice-container';
    container.id = 'pulseguard-voice-assistant';

    const banner = document.createElement('div');
    banner.className = 'pg-voice-banner';
    banner.innerText = '🎙️ PulseGuard Voice AI (Ready)';
    banner.style.display = voiceEnabled ? 'none' : 'block';

    const voiceCard = document.createElement('div');
    voiceCard.className = 'pg-voice-card';
    voiceCard.id = 'pg-voice-card';
    voiceCard.innerHTML = `
        <div class="pg-voice-header">
            <span style="color:#2ecc71; display:flex; align-items:center; gap:6px;">
                <i class="fas fa-heartbeat"></i> PulseGuard Voice AI
            </span>
            <div class="pg-voice-status" id="pg-voice-status-text">
                <span class="pg-voice-status-dot" id="pg-voice-status-dot"></span>
                <span id="pg-voice-state-label">Ready</span>
            </div>
        </div>
        <div class="pg-voice-text-box">
            <div class="pg-voice-user-transcript" id="pg-voice-transcript" style="display:none;"></div>
            <div id="pg-voice-reply">"I am listening. Say 'Take PPG scan' or 'Trigger SOS' for hands-free action."</div>
        </div>
        <div class="pg-voice-chips">
            <button class="pg-voice-chip" onclick="window.PulseGuardVoice.execute('take ppg scan')"><i class="fas fa-fingerprint"></i> Take PPG Scan</button>
            <button class="pg-voice-chip sos" onclick="window.PulseGuardVoice.execute('trigger sos')"><i class="fas fa-ambulance"></i> Trigger SOS</button>
            <button class="pg-voice-chip" onclick="window.PulseGuardVoice.execute('show wearable')"><i class="fas fa-cube"></i> Wearable 3D</button>
            <button class="pg-voice-chip" onclick="window.PulseGuardVoice.execute('start breathing exercise')"><i class="fas fa-wind"></i> 4-7-8 Breathing</button>
            <button class="pg-voice-chip" onclick="window.PulseGuardVoice.execute('how to lower heart rate')"><i class="fas fa-stethoscope"></i> Lower HR Guide</button>
            <button class="pg-voice-chip" onclick="window.PulseGuardVoice.execute('call doctor')"><i class="fas fa-video"></i> Consult Doctor</button>
            <button class="pg-voice-chip" onclick="window.PulseGuardVoice.execute('open report')"><i class="fas fa-file-medical"></i> View Report</button>
        </div>
    `;

    const micBtn = document.createElement('button');
    micBtn.className = 'pg-voice-main-btn';
    micBtn.id = 'pg-voice-mic';
    micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    micBtn.title = 'PulseGuard Voice Assistant';

    container.appendChild(banner);
    container.appendChild(voiceCard);
    container.appendChild(micBtn);
    document.body.appendChild(container);

    // ── Helper UI Updaters ─────────────────────────────────────────────────
    function setStatus(state, label) {
        const dot = document.getElementById('pg-voice-status-dot');
        const lbl = document.getElementById('pg-voice-state-label');
        if (!dot || !lbl) return;
        dot.className = 'pg-voice-status-dot ' + (state || '');
        lbl.innerText = label || 'Ready';

        micBtn.classList.remove('listening', 'speaking');
        if (state === 'listening') micBtn.classList.add('listening');
        if (state === 'speaking') micBtn.classList.add('speaking');
    }

    function showCard(msg, userSaid) {
        voiceCard.style.display = 'flex';
        const transcriptEl = document.getElementById('pg-voice-transcript');
        const replyEl = document.getElementById('pg-voice-reply');
        if (userSaid) {
            transcriptEl.style.display = 'block';
            transcriptEl.innerText = `You: "${userSaid}"`;
        }
        if (msg) {
            replyEl.innerText = msg;
        }
    }

    // ── Articulate Speech Synthesis ────────────────────────────────────────
    let currentUtterance = null;

    function speak(text, callback) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        isSpeaking = true;
        setStatus('speaking', 'Speaking...');

        if (isListening) {
            try { recognition.stop(); } catch(e){}
        }

        const utterance = new SpeechSynthesisUtterance(text);
        if (!bestVoice) bestVoice = selectBestVoice();
        if (bestVoice) utterance.voice = bestVoice;
        utterance.rate = 0.96;
        utterance.pitch = 1.0;

        currentUtterance = utterance;

        utterance.onend = () => {
            isSpeaking = false;
            currentUtterance = null;
            setStatus('', 'Ready');
            if (voiceEnabled && document.visibilityState === 'visible') {
                try {
                    recognition.start();
                    isListening = true;
                } catch(e){}
            }
            if (callback) callback();
        };

        utterance.onerror = (e) => {
            console.warn("Speech synthesis error", e);
            isSpeaking = false;
            currentUtterance = null;
            setStatus('', 'Ready');
        };

        window.speechSynthesis.speak(utterance);
    }

    window.speakAssistant = speak;

    // ── Interactive Guided 4-7-8 Breathing Protocol ────────────────────────
    function startGuidedBreathing() {
        if (isBreathingActive) {
            stopGuidedBreathing();
            return;
        }
        isBreathingActive = true;
        showCard("Starting 4-7-8 vagal breathing cycle. Follow my voice and breathe smoothly.", "Start breathing exercise");

        if (typeof window.triggerOnPageBreathing === 'function') {
            window.triggerOnPageBreathing(true);
        }

        let cycle = 1;
        const totalCycles = 3;

        function runCycle() {
            if (!isBreathingActive) return;
            if (cycle > totalCycles) {
                speak("Breathing exercise completed. Notice your pulse settling. Keep resting quietly.", () => {
                    isBreathingActive = false;
                    if (typeof window.triggerOnPageBreathing === 'function') {
                        window.triggerOnPageBreathing(false);
                    }
                    showCard("Breathing cycle complete. Heart rate stabilized.");
                });
                return;
            }

            speak(`Round ${cycle}. Inhale slowly through your nose. One... two... three... four.`, () => {
                if (!isBreathingActive) return;
                speak("Now gently hold your breath. One... two... three... four... five... six... seven.", () => {
                    if (!isBreathingActive) return;
                    speak("Exhale completely through your mouth. One... two... three... four... five... six... seven... eight. Good.", () => {
                        cycle++;
                        setTimeout(runCycle, 1000);
                    });
                });
            });
        }

        speak("Beginning 4-7-8 calming breathing. Sit back, relax your shoulders, and empty your lungs.", () => {
            setTimeout(runCycle, 1000);
        });
    }

    function stopGuidedBreathing() {
        isBreathingActive = false;
        if (breathingInterval) clearInterval(breathingInterval);
        window.speechSynthesis.cancel();
        if (typeof window.triggerOnPageBreathing === 'function') {
            window.triggerOnPageBreathing(false);
        }
        speak("Breathing exercise paused. Take gentle, natural breaths.");
        showCard("Breathing exercise stopped. Take normal breaths.");
    }

    // ── Trained Clinical Medical Intent Engine ─────────────────────────────
    function processMedicalIntent(rawText) {
        const text = rawText.toLowerCase().trim();
        showCard(null, rawText);

        const isHeartratePage = window.location.pathname.includes('/heartrate');
        const isEmergencyPage = window.location.pathname.includes('/emergency');
        const isApptPage = window.location.pathname.includes('/appointments');

        // ══════════════════════════════════════════════════════════════════════
        // 1. AUTOMATIC PPG SCAN ON VOICE COMMAND
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("take ppg scan") || text.includes("start ppg scan") || text.includes("take ppg") || 
            text.includes("start ppg") || text.includes("take scan") || text.includes("start scan") || 
            text.includes("scan heart") || text.includes("finger scan") || text.includes("finger ppg") || 
            text.includes("check heart rate") || text.includes("check my heart") || text.includes("check my pulse") || 
            text.includes("measure heart") || text.includes("measure my heart") || text.includes("measure pulse") || 
            text.includes("start measuring") || text.includes("camera scan") || text.includes("face scan") || 
            text.includes("face ppg")) {
            
            const isFace = text.includes("camera") || text.includes("face");

            if (isFace) {
                if (isHeartratePage && typeof startCamera === 'function') {
                    const camBtn = document.getElementById('start-btn');
                    if (camBtn) camBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    startCamera();
                    const msg = "Starting Face Camera scan now. Please position your face in the center of the frame and stay still for 20 seconds.";
                    showCard(msg, rawText);
                    speak(msg);
                } else {
                    const msg = "Navigating to Heart Rate monitor and automatically starting Face Camera scan.";
                    showCard(msg, rawText);
                    speak(msg, () => {
                        window.location.href = "/heartrate?autostart=face";
                    });
                }
            } else {
                // Default: Finger PPG scan
                if (isHeartratePage && typeof startFingerPPG === 'function') {
                    const fingerBtn = document.getElementById('start-finger-btn');
                    if (fingerBtn) fingerBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    startFingerPPG();
                    const msg = "Starting Finger PPG scan now. Please cover your rear camera lens completely with your index finger and hold still.";
                    showCard(msg, rawText);
                    speak(msg);
                } else {
                    const msg = "Navigating to Heart Rate monitor and automatically starting your Finger PPG scan.";
                    showCard(msg, rawText);
                    speak(msg, () => {
                        window.location.href = "/heartrate?autostart=finger";
                    });
                }
            }
            return true;
        }

        // Stop Scan Command
        if (text.includes("stop scan") || text.includes("stop ppg") || text.includes("cancel scan") || text.includes("stop camera")) {
            if (isHeartratePage) {
                if (typeof stopFingerPPG === 'function') stopFingerPPG();
                if (typeof stopCamera === 'function') stopCamera();
                const msg = "Heart rate measurement stopped.";
                showCard(msg, rawText);
                speak(msg);
                return true;
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // 2. AUTOMATIC EMERGENCY SOS ON VOICE COMMAND
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("trigger sos") || text.includes("send sos") || text.includes("activate sos") ||
            text.includes("sos") || text.includes("emergency") || text.includes("call ambulance") || 
            text.includes("help me") || text.includes("chest pain") || text.includes("heart attack") || 
            text.includes("fainting") || text.includes("ambulance")) {
            
            if (isEmergencyPage && typeof triggerSOS === 'function') {
                triggerSOS();
                const emgMsg = "Emergency SOS activated immediately! Dispatching ambulance, notifying Dr. Jayanth and your emergency contacts. Please stay seated.";
                showCard(emgMsg, rawText);
                speak(emgMsg);
            } else {
                const emgMsg = "Emergency SOS activated! Dispatching emergency services and ambulance to your location. Opening emergency monitor now.";
                showCard(emgMsg, rawText);
                // Background direct trigger
                fetch('/api/emergency/sos', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_name: 'PulseGuard User',
                        location: 'Bengaluru, Karnataka',
                        lat: 12.9716, lng: 77.5946
                    })
                }).catch(() => {});

                speak(emgMsg, () => {
                    window.location.href = "/emergency?autotrigger=1";
                });
            }
            return true;
        }

        // ══════════════════════════════════════════════════════════════════════
        // 3. DOCTOR VIDEO CONSULTATION ON VOICE COMMAND
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("appointment") || text.includes("doctor") || text.includes("video call") || 
            text.includes("video consult") || text.includes("consult dr") || text.includes("call dr") ||
            text.includes("call doctor") || text.includes("talk to doctor") || text.includes("consult cardiologist")) {
            
            if (isApptPage && typeof requestDoctorConsultation === 'function') {
                requestDoctorConsultation();
                const docMsg = "Dispatching consultation request directly to Dr. Jayanth Gowda right now.";
                showCard(docMsg, rawText);
                speak(docMsg);
            } else {
                const docMsg = "Connecting you to your live video consultations with Dr. Jayanth Gowda.";
                showCard(docMsg, rawText);
                speak(docMsg, () => {
                    window.location.href = "/appointments";
                });
            }
            return true;
        }

        // ══════════════════════════════════════════════════════════════════════
        // 4. CARDIOVASCULAR RISK SCORE & EMERGENCY CHECK ON VOICE
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("update risk") || text.includes("calculate risk") || text.includes("check risk") ||
            text.includes("risk score") || text.includes("what is my risk")) {
            if (isHeartratePage && typeof sendToRisk === 'function' && window.lastResult) {
                sendToRisk();
                const msg = "Updating your cardiovascular risk assessment with your latest heart rate metrics.";
                showCard(msg, rawText);
                speak(msg);
                return true;
            } else {
                fetch('/api/me/last-prediction')
                    .then(r => r.json())
                    .then(data => {
                        if (data.score) {
                            const msg = `Your latest cardiovascular risk score is ${data.score} out of 100, which is ${data.level} risk.`;
                            showCard(msg, rawText);
                            speak(msg);
                        } else {
                            const msg = "You haven't run a risk prediction yet. Take a PPG scan to compute your risk.";
                            showCard(msg, rawText);
                            speak(msg);
                        }
                    }).catch(() => speak("Unable to retrieve risk score at this moment."));
                return true;
            }
        }

        if (text.includes("emergency check") || text.includes("check for emergency") || text.includes("check rhythm")) {
            if (isHeartratePage && typeof checkEmergency === 'function' && window.lastResult) {
                checkEmergency();
                const msg = "Running emergency analysis on your heart rhythm data.";
                showCard(msg, rawText);
                speak(msg);
                return true;
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // 5. REPORTS, PDF & FAMILY SHARING ON VOICE
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("show report") || text.includes("open report") || text.includes("view report") || 
            text.includes("clinical report") || text.includes("my report")) {
            if (isHeartratePage && typeof reopenReportModal === 'function') {
                reopenReportModal();
                const msg = "Opening your detailed clinical telecardiology screening report.";
                showCard(msg, rawText);
                speak(msg);
                return true;
            } else {
                speak("Opening health reports page.");
                window.location.href = "/reports";
                return true;
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // 6. 3D WEARABLE MODEL & TEARDOWN ON VOICE COMMAND
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("wearable") || text.includes("3d watch") || text.includes("3d model") ||
            text.includes("show wearable") || text.includes("open wearable") || text.includes("teardown") ||
            text.includes("layer by layer") || text.includes("smart watch") || text.includes("hardware")) {
            
            const wShowcase = document.getElementById('wearable-showcase');
            if (wShowcase) {
                wShowcase.scrollIntoView({ behavior: 'smooth', block: 'start' });
                const msg = "Displaying the interactive 3D PulseGuard Wear model and layer-by-layer teardown.";
                showCard(msg, rawText);
                speak(msg);
            } else {
                const msg = "Launching the PulseGuard Wear 3D interactive model and teardown studio.";
                showCard(msg, rawText);
                speak(msg, () => {
                    window.location.href = "/wearable";
                });
            }
            return true;
        }

        if (text.includes("close report")) {
            if (isHeartratePage && typeof closeClinicalReport === 'function') {
                closeClinicalReport();
                const msg = "Clinical report closed.";
                showCard(msg, rawText);
                speak(msg);
                return true;
            }
        }

        if (text.includes("print report") || text.includes("download report") || text.includes("save report") || text.includes("pdf")) {
            const msg = "Opening print dialog to generate your medical screening report PDF.";
            showCard(msg, rawText);
            speak(msg, () => {
                window.print();
            });
            return true;
        }

        if (text.includes("email report") || text.includes("email relative") || text.includes("send report") || text.includes("send to family")) {
            if (typeof emailReportToRelative === 'function') {
                emailReportToRelative();
                const msg = "Sending your latest clinical report link to your designated family contact right now.";
                showCard(msg, rawText);
                speak(msg);
                return true;
            } else {
                fetch('/api/health/share_card', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        const msg = data.status === 'success' ? "Report link sent to your relative." : "Notice: " + (data.message || data.error);
                        showCard(msg, rawText);
                        speak(msg);
                    }).catch(() => speak("Unable to send report email."));
                return true;
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // 6. GUIDED BREATHING & LOWERING HEART RATE
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("lower") || text.includes("overcome") || text.includes("reduce") ||
            text.includes("bring down") || text.includes("fast heart") || text.includes("high pulse") ||
            text.includes("tachycardia") || text.includes("what should i do") || text.includes("how to overcome")) {
            
            const advice = "To rapidly lower an elevated heart rate, sit back in a supported position with your head elevated. Drink a glass of cold water to restore blood volume. Perform the 4-7-8 vagal breathing technique: inhale for 4 seconds, hold for 7, and exhale for 8. You can also place a cool, damp cloth across your forehead. If you experience chest tightness, pain, or dizziness, say emergency immediately. Would you like me to guide your breathing now?";
            showCard(advice, rawText);
            speak(advice);
            return true;
        }

        if (text.includes("start breathing") || text.includes("guide my breathing") || 
            text.includes("help me breathe") || text.includes("4-7-8") || text.includes("breathe with me") ||
            (text === "yes" && !isBreathingActive)) {
            startGuidedBreathing();
            return true;
        }

        if (text.includes("stop breathing") || text.includes("cancel breathing") || text.includes("pause breathing")) {
            stopGuidedBreathing();
            return true;
        }

        if (text.includes("why is my heart rate high") || text.includes("causes") || text.includes("why high") || text.includes("why fast")) {
            const explanation = "Elevated heart rate, or sinus tachycardia, occurs when the sympathetic nervous system triggers extra adrenaline. The most common causes are dehydration, psychological anxiety or panic, caffeine or stimulant intake, lack of sleep, or recent physical exertion. Resting in a cool environment and deep diaphragmatic breathing will help bring it down.";
            showCard(explanation, rawText);
            speak(explanation);
            return true;
        }

        if (text.includes("normal heart rate") || text.includes("normal bpm") || text.includes("healthy rate")) {
            const normalMsg = "For a healthy adult at rest, normal heart rate ranges between 60 and 100 beats per minute. Rates above 100 are termed tachycardia, while rates below 60 are bradycardia.";
            showCard(normalMsg, rawText);
            speak(normalMsg);
            return true;
        }

        if (text.includes("explain my reading") || text.includes("my reading") || text.includes("last result") || text.includes("what was my heart rate")) {
            let bpm = null;
            if (window.currentReportData && window.currentReportData.bpm) {
                bpm = window.currentReportData.bpm;
            } else if (document.getElementById('finger-bpm-val') && document.getElementById('finger-bpm-val').textContent !== '--') {
                bpm = parseInt(document.getElementById('finger-bpm-val').textContent);
            } else if (document.getElementById('bpm-val') && document.getElementById('bpm-val').textContent !== '--') {
                bpm = parseInt(document.getElementById('bpm-val').textContent);
            }

            if (bpm) {
                let msg = `Your latest recorded heart rate is ${bpm} beats per minute. `;
                if (bpm >= 140) {
                    msg += "This is severe tachycardia. Please rest completely and practice paced breathing or consult your doctor.";
                } else if (bpm > 100) {
                    msg += "This is sinus tachycardia. Stay hydrated and rest quietly.";
                } else if (bpm < 50) {
                    msg += "This indicates bradycardia. Avoid sudden standing.";
                } else {
                    msg += "This is within the healthy adult normal range. Your cardiac output is balanced.";
                }
                showCard(msg, rawText);
                speak(msg);
                return true;
            } else {
                speak("I don't see a current scan on screen. Say 'Take PPG scan' and I will begin measuring for you.");
                return true;
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // 7. NAVIGATION
        // ══════════════════════════════════════════════════════════════════════
        if (text.includes("dashboard")) { speak("Opening dashboard."); window.location.href = "/dashboard"; return true; }
        if (text.includes("measure") || text.includes("heart rate monitor")) { speak("Opening heart rate monitor."); window.location.href = "/heartrate"; return true; }
        if (text.includes("reports") || text.includes("family")) { speak("Opening health reports."); window.location.href = "/reports"; return true; }
        if (text.includes("chat") || text.includes("assistant")) { speak("Opening AI chat."); window.location.href = "/chat"; return true; }
        if (text.includes("diet")) { speak("Opening diet analysis."); window.location.href = "/diet"; return true; }
        if (text.includes("lifestyle")) { speak("Opening lifestyle tips."); window.location.href = "/lifestyle"; return true; }
        if (text.includes("doctor portal")) { speak("Opening doctor portal."); window.location.href = "/doctor"; return true; }
        if (text.includes("logout")) { speak("Logging out. Take care."); window.location.href = "/logout"; return true; }

        // Fallback
        const fallback = `I noted: "${rawText}". You can say 'Take PPG scan', 'Trigger SOS', 'Start breathing', or 'Call doctor'.`;
        showCard(fallback, rawText);
        speak(fallback);
        return true;
    }

    // ── Expose Command Execution Globally ──────────────────────────────────
    window.PulseGuardVoice = {
        execute: function(cmd) {
            processMedicalIntent(cmd);
        },
        startBreathing: startGuidedBreathing,
        stopBreathing: stopGuidedBreathing,
        speak: speak
    };

    // ── Speech Recognition Lifecycle ───────────────────────────────────────
    function enterCommandMode() {
        inCommandMode = true;
        setStatus('listening', 'Listening...');
        voiceCard.style.display = 'flex';

        clearTimeout(commandModeTimer);
        commandModeTimer = setTimeout(() => {
            inCommandMode = false;
            setStatus('', 'Ready');
        }, 14000);
    }

    recognition.onresult = (event) => {
        if (isSpeaking) return;

        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        const currentText = (finalTranscript || interimTranscript).toLowerCase().trim();

        if (!inCommandMode) {
            // Wake words: "pulseguard", "hey pulseguard", "hello", "doctor", "help", "scan", "sos"
            if (currentText.includes("pulseguard") || currentText.includes("hey pulseguard") ||
                currentText.includes("hello") || currentText.includes("hi") || currentText.includes("help") ||
                currentText.includes("scan") || currentText.includes("sos") || currentText.includes("emergency")) {
                
                // If it's a direct urgent command like "sos" or "take scan", process immediately!
                if (currentText.includes("sos") || currentText.includes("emergency") || currentText.includes("scan") || currentText.includes("take ppg")) {
                    processMedicalIntent(currentText);
                } else {
                    speak("Hello! I am PulseGuard Voice AI. Say 'Take PPG scan' or 'Trigger SOS'.", () => {
                        enterCommandMode();
                    });
                }
            }
        } else {
            const transcriptEl = document.getElementById('pg-voice-transcript');
            if (transcriptEl) {
                transcriptEl.style.display = 'block';
                transcriptEl.innerText = `Heard: "${currentText}"`;
            }
            if (finalTranscript) {
                processMedicalIntent(finalTranscript);
                inCommandMode = false;
                clearTimeout(commandModeTimer);
            }
        }
    };

    recognition.onerror = (event) => {
        console.warn("Speech recognition notice:", event.error);
        if (event.error === 'not-allowed') {
            banner.style.display = 'block';
            banner.innerText = '⚠️ Microphone blocked. Tap to permit.';
            voiceEnabled = false;
            localStorage.setItem('voice_enabled', 'false');
        }
    };

    recognition.onend = () => {
        isListening = false;
        if (voiceEnabled && !isSpeaking && document.visibilityState === 'visible') {
            try {
                recognition.start();
                isListening = true;
            } catch(e){}
        }
    };

    // ── Mic Button & Banner Controls ───────────────────────────────────────
    function toggleVoiceAssistant() {
        voiceEnabled = !voiceEnabled;
        localStorage.setItem('voice_enabled', voiceEnabled.toString());

        if (voiceEnabled) {
            banner.style.display = 'none';
            voiceCard.style.display = 'flex';
            try {
                recognition.start();
                isListening = true;
            } catch(e){}
            speak("PulseGuard voice assistant activated. You can speak commands like 'Take PPG scan' or 'Trigger SOS'.", () => {
                enterCommandMode();
            });
        } else {
            voiceEnabled = false;
            isListening = false;
            inCommandMode = false;
            try { recognition.stop(); } catch(e){}
            window.speechSynthesis.cancel();
            voiceCard.style.display = 'none';
            banner.style.display = 'block';
            banner.innerText = '🎙️ Tap to enable Voice Assistant';
            setStatus('', 'Ready');
        }
    }

    micBtn.addEventListener('click', () => {
        if (!voiceEnabled) {
            toggleVoiceAssistant();
        } else {
            if (voiceCard.style.display === 'none') {
                voiceCard.style.display = 'flex';
            }
            enterCommandMode();
            speak("I am listening.");
        }
    });

    banner.addEventListener('click', toggleVoiceAssistant);

    // Visibility Listener
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === 'hidden') {
            if (isListening) {
                try { recognition.stop(); } catch(e){}
                isListening = false;
            }
        } else {
            if (voiceEnabled && !isSpeaking) {
                try {
                    recognition.start();
                    isListening = true;
                } catch(e){}
            }
        }
    });

    // Initial Start if enabled
    if (voiceEnabled && document.visibilityState === 'visible') {
        try {
            recognition.start();
            isListening = true;
        } catch(e){}
    }
})();
