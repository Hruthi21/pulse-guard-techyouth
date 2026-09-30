/**
 * PulseGuard AI — High-Accuracy PPG Signal Processing Engine v2
 * Finger-based photoplethysmography with strict signal validation
 * PRINCIPLE: Better NO result than WRONG result
 */
class PPGEngine {
  constructor() {
    this.SAMPLE_RATE    = 30;          // fps
    this.BUFFER_SEC     = 25;          // rolling window
    this.MAX_BUF        = this.SAMPLE_RATE * this.BUFFER_SEC;
    this.MIN_PEAKS      = 10;          // must have ≥10 valid peaks before output
    this.MIN_FRAMES     = this.SAMPLE_RATE * 8;  // 8 s warm-up

    // Signal buffers
    this.rawSignal      = [];
    this.filtSignal     = [];
    this.timestamps     = [];

    // Biquad states — HP 0.7 Hz then LP 4.0 Hz @ 30 fps (Butterworth 2nd-order)
    this.hp = { b0:0.9014, b1:-1.8029, b2:0.9014, a1:-1.7932, a2:0.8126,
                x1:0, x2:0, y1:0, y2:0 };
    this.lp = { b0:0.1084, b1:0.2169,  b2:0.1084, a1:-0.8773, a2:0.3111,
                x1:0, x2:0, y1:0, y2:0 };

    // State
    this.bpm            = 0;
    this.hrv            = 0;
    this.sqi            = 0;
    this.confidence     = 0;
    this.stableArr      = [];    // rolling BPM history for stability check
    this.prevRaw        = null;
    this.motionFlag     = false;
    this._motionCount   = 0;
    this._flatCount     = 0;     // consecutive flat frames
    this.fingerPresent  = false;
    this.lastBrightness = null;
  }

  /* ─── Biquad IIR filter ─────────────────────────────────────────────────── */
  _biquad(f, x) {
    const y = f.b0*x + f.b1*f.x1 + f.b2*f.x2 - f.a1*f.y1 - f.a2*f.y2;
    f.x2=f.x1; f.x1=x; f.y2=f.y1; f.y1=y;
    return y;
  }

  /* ─── Moving-average smoother ───────────────────────────────────────────── */
  _movingAvg(arr, window=5) {
    return arr.map((_, i) => {
      const start = Math.max(0, i - window + 1);
      const slice = arr.slice(start, i + 1);
      return slice.reduce((a,b)=>a+b,0)/slice.length;
    });
  }

  /* ─── Finger detection (strict) ─────────────────────────────────────────── */
  fingerDetected(r, g, b) {
    const brightness = (r + g + b) / 3;
    const redDom     = r / (g + 1);
    const saturation = (Math.max(r,g,b) - Math.min(r,g,b)) / (Math.max(r,g,b)+1);
    // Require: high brightness, red dominance, saturated (not white light)
    const ok = brightness > 90 && redDom > 1.5 && r > 140 && saturation > 0.15;
    this.fingerPresent = ok;
    return ok;
  }

  /* ─── Brightness-spike / blur rejection ─────────────────────────────────── */
  frameValid(r, g, b) {
    const brightness = (r + g + b) / 3;
    let ok = true;
    if (this.lastBrightness !== null) {
      const delta = Math.abs(brightness - this.lastBrightness);
      if (delta > 40) ok = false;   // sudden flash or shadow → reject
    }
    this.lastBrightness = brightness;
    return ok;
  }

  /* ─── Motion artifact detection (hysteresis) ────────────────────────────── */
  motionDetected(r, g, b) {
    if (this.prevRaw === null) { this.prevRaw = {r,g,b}; return false; }
    const dr = Math.abs(r - this.prevRaw.r);
    const dg = Math.abs(g - this.prevRaw.g);
    const db = Math.abs(b - this.prevRaw.b);
    this.prevRaw = {r,g,b};
    const motion = (dr + dg + db) > 85;
    this._motionCount = motion ? (this._motionCount||0)+1 : 0;
    this.motionFlag   = this._motionCount >= 2;
    return this.motionFlag;
  }

  /* ─── Flat-signal detector ───────────────────────────────────────────────── */
  _isSignalFlat() {
    if (this.filtSignal.length < 30) return false;
    const last = this.filtSignal.slice(-30);
    const mn   = Math.min(...last), mx = Math.max(...last);
    return (mx - mn) < 0.8;   // amplitude too small → flat/dead signal
  }

  /* ─── Add one frame ─────────────────────────────────────────────────────── */
  addFrame(r, g, b, flashOn) {
    if (!this.frameValid(r,g,b)) return null;
    if (this.motionDetected(r,g,b)) return null;

    // Use GREEN channel (best SNR without flash); RED with flash
    const raw      = flashOn ? r : g;
    const hpOut    = this._biquad(this.hp, raw);
    const filtered = this._biquad(this.lp, hpOut);

    this.rawSignal.push(raw);
    this.filtSignal.push(filtered);
    this.timestamps.push(Date.now());

    // Rolling window
    if (this.rawSignal.length > this.MAX_BUF) {
      this.rawSignal.shift(); this.filtSignal.shift(); this.timestamps.shift();
    }

    // Flat signal → auto-reset buffers
    if (this._isSignalFlat()) {
      this._flatCount++;
      if (this._flatCount > 60) { this._resetBuffers(); this._flatCount=0; }
    } else {
      this._flatCount = 0;
    }

    return filtered;
  }

  _resetBuffers() {
    this.rawSignal=[]; this.filtSignal=[]; this.timestamps=[];
    this.hp.x1=this.hp.x2=this.hp.y1=this.hp.y2=0;
    this.lp.x1=this.lp.x2=this.lp.y1=this.lp.y2=0;
  }

  /* ─── Adaptive peak detection ───────────────────────────────────────────── */
  _detectPeaks(sig) {
    if (sig.length < 12) return [];
    const smoothed = this._movingAvg(sig, 3);
    const mean = smoothed.reduce((a,b)=>a+b,0)/smoothed.length;
    const std  = Math.sqrt(smoothed.reduce((s,x)=>s+(x-mean)**2,0)/smoothed.length);
    // Adaptive threshold: mean + 0.3σ (more robust than fixed)
    const thr  = mean + 0.3 * std;
    const minD = Math.floor(this.SAMPLE_RATE * 0.30);  // ≥300 ms between peaks

    const peaks = [];
    let last = -minD;
    for (let i=1; i<smoothed.length-1; i++) {
      if (smoothed[i]>smoothed[i-1] && smoothed[i]>smoothed[i+1]
          && smoothed[i]>thr && (i-last)>=minD) {
        peaks.push(i); last=i;
      }
    }
    return peaks;
  }

  /* ─── Outlier rejection from RR array ───────────────────────────────────── */
  _filterRR(rr) {
    if (rr.length < 3) return rr;
    const med = [...rr].sort((a,b)=>a-b)[Math.floor(rr.length/2)];
    return rr.filter(v => Math.abs(v-med)/med < 0.25);  // ±25% of median
  }

  /* ─── Compute all metrics (returns null if not stable) ──────────────────── */
  compute() {
    if (this.filtSignal.length < this.MIN_FRAMES) return null;

    const window = Math.min(this.filtSignal.length, this.SAMPLE_RATE * 20);
    const sig  = this.filtSignal.slice(-window);
    const ts   = this.timestamps.slice(-window);
    const peaks = this._detectPeaks(sig);

    if (peaks.length < this.MIN_PEAKS) return { status: 'measuring', bpm:null, sqi:0, confidence:0 };

    // RR intervals (seconds) — physiological range 0.27–2.0 s → 30–220 BPM
    let rr = [];
    for (let i=1; i<peaks.length; i++) {
      const dt = (ts[peaks[i]] - ts[peaks[i-1]]) / 1000;
      if (dt >= 0.27 && dt <= 2.0) rr.push(dt);
    }
    if (rr.length < 4) return { status: 'measuring', bpm:null, sqi:0, confidence:0 };

    // Reject outliers
    rr = this._filterRR(rr);
    if (rr.length < 3) return { status: 'poor_signal', bpm:null, sqi:0, confidence:0 };

    const meanRR = rr.reduce((a,b)=>a+b,0)/rr.length;
    const bpm    = Math.round(60/meanRR);
    if (bpm < 30 || bpm > 220) return { status: 'poor_signal', bpm:null, sqi:0, confidence:0 };

    // HRV — RMSSD (ms)
    let ssD = 0;
    for (let i=1; i<rr.length; i++) ssD += ((rr[i]-rr[i-1])*1000)**2;
    const hrv = Math.round(Math.sqrt(ssD/Math.max(1,rr.length-1)));

    // SQI — coefficient of variation (lower CV = cleaner signal)
    const rrStd = Math.sqrt(rr.reduce((s,x)=>s+(x-meanRR)**2,0)/rr.length);
    const cv    = rrStd / meanRR;
    const sqi   = Math.round(Math.max(0, Math.min(100, (1 - cv*3.5)*100)));

    // Stability — rolling BPM spread must be small
    this.stableArr.push(bpm);
    if (this.stableArr.length > 12) this.stableArr.shift();
    const spread    = this.stableArr.length >= 5
      ? Math.max(...this.stableArr) - Math.min(...this.stableArr) : 999;
    const stability = Math.max(0, 1 - spread/15);

    // STRICT stability gate: spread must be ≤ 8 BPM and ≥10 peaks
    const isStable = spread <= 8 && peaks.length >= this.MIN_PEAKS && sqi >= 30;

    // Confidence composite
    const peakScore = Math.min(1, peaks.length/15);
    const conf      = Math.round(sqi*0.45 + peakScore*100*0.3 + stability*100*0.25);
    const confClamped = Math.min(100, Math.max(0, conf));

    // Irregular beat check
    let irregular = false;
    if (rr.length >= 5) {
      const diffs = rr.slice(1).map((v,i)=>Math.abs(v-rr[i]));
      irregular   = diffs.filter(d=>d>0.12).length > rr.length*0.3;
    }

    // Stress label
    const stress = hrv < 20 ? 'High Stress' : hrv < 40 ? 'Moderate' : 'Relaxed';

    // Only output BPM if stable enough
    if (!isStable) {
      return { status:'measuring', bpm:null, sqi, confidence:confClamped,
               signal_quality: sqi>=60?'high':sqi>=30?'medium':'low' };
    }

    return {
      bpm,
      hrv,
      sqi,
      confidence     : confClamped,
      signal_quality : sqi>=60?'high':sqi>=30?'medium':'low',
      stress,
      irregular,
      peaks,
      filteredSignal : sig,
      rrIntervals    : rr,
      status         : confClamped >= 70 ? 'stable' : 'measuring'
    };
  }

  /* ─── Full reset ─────────────────────────────────────────────────────────── */
  reset() {
    this._resetBuffers();
    this.stableArr=[]; this.prevRaw=null; this.bpm=0;
    this.motionFlag=false; this._motionCount=0; this._flatCount=0;
    this.lastBrightness=null; this.fingerPresent=false;
  }
}

window.PPGEngine = PPGEngine;
