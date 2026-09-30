html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>PulseGuard AI - Life Planner</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
<link rel="stylesheet" href="/static/pulseguard.css"/>
<style>
.lp-tabs{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap}
.lp-tab{padding:8px 18px;border-radius:20px;border:1px solid var(--card-border);background:var(--card-bg);color:var(--muted);cursor:pointer;font-size:13px;font-weight:600;transition:all .2s}
.lp-tab.active{background:var(--primary);color:#000;border-color:var(--primary)}
.lp-panel{display:none}.lp-panel.active{display:block}
.sc{background:var(--card-bg);border:1px solid var(--card-border);border-radius:14px;padding:18px;text-align:center}
.sv{font-size:28px;font-weight:800;color:var(--primary)}.sl{font-size:11px;color:var(--muted);margin-top:4px}
.bg{background:rgba(29,185,84,.2);color:#1db954;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;display:inline-block}
.bw{background:rgba(243,156,18,.2);color:#f39c12;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;display:inline-block}
.bb{background:rgba(231,76,60,.2);color:#e74c3c;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;display:inline-block}
.ii{padding:12px 16px;border-radius:10px;margin-bottom:8px;font-size:13px}
.ig{background:rgba(29,185,84,.1);border:1px solid rgba(29,185,84,.3)}
.iw{background:rgba(243,156,18,.1);border:1px solid rgba(243,156,18,.3)}
.ib{background:rgba(231,76,60,.1);border:1px solid rgba(231,76,60,.3)}
.in{background:rgba(52,152,219,.1);border:1px solid rgba(52,152,219,.3)}
.ep{display:inline-block;padding:2px 8px;border-radius:8px;font-size:10px;font-weight:700}
.ew{background:rgba(52,152,219,.2);color:#3498db}.em{background:rgba(231,76,60,.2);color:#e74c3c}
.er{background:rgba(29,185,84,.2);color:#1db954}.et{background:rgba(243,156,18,.2);color:#f39c12}
.es{background:rgba(155,89,182,.2);color:#9b59b6}.eo{background:rgba(149,165,166,.2);color:#95a5a6}
.fr{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
@media(max-width:600px){.fr{grid-template-columns:1fr}}
.li{background:var(--card-bg,#0d0d1a);border:1px solid var(--card-border);color:#fff;border-radius:8px;padding:10px 14px;font-size:13px;width:100%}
.ts{padding:20px;border-radius:12px;text-align:center}
.ts-s{background:rgba(29,185,84,.1);border:2px solid #1db954}
.ts-r{background:rgba(231,76,60,.1);border:2px solid #e74c3c}
</style>
</head>
<body>
<aside class="pg-sidebar" id="sidebar">
  <div class="sidebar-logo"><i class="fas fa-heartbeat logo-icon"></i><span class="logo-text">PulseGuard AI</span></div>
  <nav class="sidebar-nav">
    <a href="/" class="nav-item"><i class="fas fa-home"></i><span>Home</span></a>
    <a href="/dashboard" class="nav-item"><i class="fas fa-chart-line"></i><span>Dashboard</span></a>
    <a href="/heartrate" class="nav-item"><i class="fas fa-heartbeat"></i><span>Heart Rate</span></a>
    <a href="/lifeplanner" class="nav-item active"><i class="fas fa-brain"></i><span>Life Planner</span></a>
    <a href="/lifestyle" class="nav-item"><i class="fas fa-running"></i><span>Lifestyle</span></a>
    <a href="/diet" class="nav-item"><i class="fas fa-apple-alt"></i><span>Diet</span></a>
    <a href="/emergency" class="nav-item"><i class="fas fa-ambulance"></i><span>Emergency</span></a>
    <a href="/chat" class="nav-item"><i class="fas fa-robot"></i><span>AI Chat</span></a>
  </nav>
  <a href="/emergency" class="sidebar-sos"><i class="fas fa-exclamation-triangle"></i><span>SOS Emergency</span></a>
</aside>
<main class="pg-main">
  <header class="pg-header">
    <div>
      <h1>&#129504; AI Life Planner</h1>
      <div class="header-sub">Sleep &middot; Calendar &middot; Energy &middot; Burnout &middot; Travel Risk &nbsp;|&nbsp; <small style="color:#e74c3c">Not for medical diagnosis</small></div>
    </div>
    <div style="display:flex;gap:12px;align-items:center">
      <span class="status-badge" id="sys-status"><i class="fas fa-circle" style="font-size:8px"></i> Ready</span>
      <a href="/dashboard" style="color:var(--muted);text-decoration:none;font-size:13px"><i class="fas fa-arrow-left"></i> Dashboard</a>
    </div>
  </header>
  <div class="pg-content">

    <div class="grid-4 fade-in" style="margin-bottom:24px">
      <div class="sc"><div class="sv" id="sc-sleep">--</div><div class="sl">Sleep Hours</div><div style="margin-top:6px"><span id="sc-slq" class="bw">--</span></div></div>
      <div class="sc"><div class="sv" id="sc-hr">--</div><div class="sl">Avg HR (BPM)</div></div>
      <div class="sc"><div class="sv" id="sc-work">--</div><div class="sl">Work Hours Today</div></div>
      <div class="sc"><div class="sv" id="sc-nrg">--</div><div class="sl">Energy Level</div><div style="margin-top:6px"><span id="sc-nrb" class="bg">--</span></div></div>
    </div>

    <div id="alert-bar" style="margin-bottom:16px"></div>

    <div class="lp-tabs">
      <button class="lp-tab active" onclick="tab('sleep')"><i class="fas fa-moon"></i> Sleep</button>
      <button class="lp-tab" onclick="tab('calendar')"><i class="fas fa-calendar-alt"></i> Calendar</button>
      <button class="lp-tab" onclick="tab('burnout')"><i class="fas fa-fire"></i> Burnout</button>
      <button class="lp-tab" onclick="tab('travel')"><i class="fas fa-plane"></i> Travel Risk</button>
      <button class="lp-tab" onclick="tab('insights')"><i class="fas fa-lightbulb"></i> AI Insights</button>
      <button class="lp-tab" onclick="tab('report')"><i class="fas fa-chart-bar"></i> Weekly Report</button>
    </div>

    <!-- SLEEP -->
    <div id="panel-sleep" class="lp-panel active">
      <div class="grid-2">
        <div class="card">
          <div class="card-title"><i class="fas fa-plus-circle" style="color:var(--primary)"></i> Log Sleep</div>
          <div class="fr">
            <div><label style="font-size:11px;color:var(--muted)">Sleep Start</label><input type="datetime-local" id="sl-s" class="li" style="margin-top:4px"/></div>
            <div><label style="font-size:11px;color:var(--muted)">Sleep End</label><input type="datetime-local" id="sl-e" class="li" style="margin-top:4px"/></div>
          </div>
          <button class="btn-primary" onclick="logSleep()"><i class="fas fa-save"></i> Save Sleep Record</button>
        </div>
        <div class="card">
          <div class="card-title"><i class="fas fa-history" style="color:var(--primary)"></i> Sleep History (14 days)</div>
          <div id="sleep-list" style="max-height:300px;overflow-y:auto"><div style="color:var(--muted);font-size:13px;text-align:center;padding:20px">No records yet.</div></div>
        </div>
      </div>
    </div>

    <!-- CALENDAR -->
    <div id="panel-calendar" class="lp-panel">
      <div class="grid-2">
        <div class="card">
          <div class="card-title"><i class="fas fa-calendar-plus" style="color:var(--primary)"></i> Add Event</div>
          <input type="text" id="ev-t" placeholder="Event title..." class="li" style="margin-bottom:10px"/>
          <div class="fr">
            <div><label style="font-size:11px;color:var(--muted)">Start</label><input type="datetime-local" id="ev-s" class="li" style="margin-top:4px"/></div>
            <div><label style="font-size:11px;color:var(--muted)">End</label><input type="datetime-local" id="ev-e" class="li" style="margin-top:4px"/></div>
          </div>
          <select id="ev-tp" class="li" style="margin-bottom:10px">
            <option value="work">Work</option><option value="meeting">Meeting</option>
            <option value="rest">Rest</option><option value="sleep">Sleep</option>
            <option value="travel">Travel</option><option value="other">Other</option>
          </select>
          <input type="text" id="ev-n" placeholder="Notes (optional)" class="li" style="margin-bottom:10px"/>
          <button class="btn-primary" onclick="addEvent()"><i class="fas fa-plus"></i> Add Event</button>
        </div>
        <div class="card">
          <div class="card-title"><i class="fas fa-list" style="color:var(--primary)"></i> Events <span id="ev-stat" style="font-size:11px;color:var(--muted);font-weight:400"></span></div>
          <div id="events-list" style="max-height:350px;overflow-y:auto"><div style="color:var(--muted);font-size:13px;text-align:center;padding:20px">No events yet.</div></div>
        </div>
      </div>
    </div>

    <!-- BURNOUT -->
    <div id="panel-burnout" class="lp-panel">
      <div class="card">
        <div class="card-title"><i class="fas fa-fire" style="color:#e74c3c"></i> Burnout and Stress Analysis</div>
        <div class="grid-3" style="gap:12px;margin-bottom:16px">
          <div class="sc"><div class="sv" id="bo-s">--</div><div class="sl">Burnout Score</div></div>
          <div class="sc"><div class="sv" id="bo-sl">--</div><div class="sl">Avg Sleep (7d)</div></div>
          <div class="sc"><div class="sv" id="bo-w">--</div><div class="sl">Avg Work Hrs</div></div>
        </div>
        <div id="bo-alerts" style="margin-bottom:12px"></div>
        <div id="bo-lv" style="text-align:center;padding:16px;margin-bottom:16px"></div>
        <button class="btn-primary" onclick="loadBurnout()"><i class="fas fa-sync"></i> Analyse Now</button>
      </div>
    </div>

    <!-- TRAVEL -->
    <div id="panel-travel" class="lp-panel">
      <div class="card">
        <div class="card-title"><i class="fas fa-plane-departure" style="color:#f39c12"></i> Travel Safety Assessment</div>
        <div class="fr">
          <div><label style="font-size:11px;color:var(--muted)">Destination</label><input type="text" id="tr-d" placeholder="e.g. Mumbai" class="li" style="margin-top:4px"/></div>
          <div><label style="font-size:11px;color:var(--muted)">Travel Date</label><input type="date" id="tr-dt" class="li" style="margin-top:4px"/></div>
        </div>
        <div style="margin-bottom:12px"><label style="font-size:11px;color:var(--muted)">Duration (days)</label><input type="number" id="tr-dur" min="1" max="90" value="3" class="li" style="margin-top:4px"/></div>
        <button class="btn-primary" onclick="assessTravel()" style="margin-bottom:16px"><i class="fas fa-shield-alt"></i> Assess Travel Risk</button>
        <div id="tr-res"></div>
      </div>
    </div>

    <!-- INSIGHTS -->
    <div id="panel-insights" class="lp-panel">
      <div class="card">
        <div class="card-title"><i class="fas fa-lightbulb" style="color:#f39c12"></i> AI Lifestyle Insights <span style="font-size:11px;color:var(--muted);font-weight:400">Based on last 7 days</span></div>
        <button class="btn-primary" onclick="loadInsights()" style="margin-bottom:16px"><i class="fas fa-sync"></i> Refresh Insights</button>
        <div id="ins-list"><div style="color:var(--muted);font-size:13px;text-align:center;padding:30px">Click Refresh to load insights.</div></div>
      </div>
    </div>

    <!-- REPORT -->
    <div id="panel-report" class="lp-panel">
      <div class="card">
        <div class="card-title"><i class="fas fa-chart-bar" style="color:var(--primary)"></i> Weekly Health Report</div>
        <button class="btn-primary" onclick="loadReport()" style="margin-bottom:16px"><i class="fas fa-download"></i> Generate Report</button>
        <div id="rep-cnt"></div>
      </div>
    </div>

  </div>
</main>
<div class="pg-toast" id="pg-toast"></div>
<script>
const TABS=['sleep','calendar','burnout','travel','insights','report'];
function tab(t){
  document.querySelectorAll('.lp-tab').forEach((b,i)=>b.classList.toggle('active',TABS[i]===t));
  document.querySelectorAll('.lp-panel').forEach(p=>p.classList.remove('active'));
  document.getElementById('panel-'+t).classList.add('active');
}
function toast(m,tp='success'){
  const el=document.getElementById('pg-toast');
  el.textContent=m;el.className='pg-toast show '+(tp==='error'?'error':tp==='warning'?'warning':'');
  setTimeout(()=>el.classList.remove('show'),3500);
}
function qb(q){return q==='good'?'bg':q==='average'?'bw':'bb';}
async function loadSummary(){
  try{
    const d=await(await fetch('/api/life/summary')).json();
    document.getElementById('sc-sleep').textContent=d.sleep_hours!=null?d.sleep_hours+'h':'--';
    const sq=document.getElementById('sc-slq');sq.textContent=d.sleep_quality||'--';sq.className=qb(d.sleep_quality);
    document.getElementById('sc-hr').textContent=d.heart_rate_avg!=null?d.heart_rate_avg:' -- ';
    document.getElementById('sc-work').textContent=d.work_hours!=null?d.work_hours+'h':'--';
    const nrg=d.energy_level||'--';
    document.getElementById('sc-nrg').textContent=nrg;
    const nb=document.getElementById('sc-nrb');nb.textContent=nrg.toUpperCase();
    nb.className=nrg==='high'?'bg':nrg==='medium'?'bw':'bb';
    const ab=document.getElementById('alert-bar');ab.innerHTML='';
    (d.alerts||[]).forEach(a=>{const div=document.createElement('div');div.className='ii ib';div.style.marginBottom='8px';div.textContent=a;ab.appendChild(div);});
  }catch(e){console.warn(e);}
}
async function loadSleepHistory(){
  try{
    const d=await(await fetch('/api/sleep?days=14')).json();
    const el=document.getElementById('sleep-list');
    if(!d.records||!d.records.length){el.innerHTML='<div style="color:var(--muted);font-size:13px;text-align:center;padding:20px">No records yet.</div>';return;}
    el.innerHTML=d.records.slice().reverse().map(r=>{
      const cls=qb(r.quality);
      return '<div style="padding:10px;border-bottom:1px solid rgba(255,255,255,.07);display:flex;justify-content:space-between;align-items:center">'+
        '<div><div style="font-weight:600;font-size:13px">'+new Date(r.sleep_start).toLocaleDateString()+' <span class="'+cls+'">'+r.quality+'</span></div>'+
        '<div style="font-size:11px;color:var(--muted)">'+new Date(r.sleep_start).toLocaleTimeString()+' to '+new Date(r.sleep_end).toLocaleTimeString()+'</div></div>'+
        '<div style="font-weight:700;color:var(--primary)">'+r.duration+'h</div></div>';
    }).join('');
  }catch(e){}
}
async function logSleep(){
  const ss=document.getElementById('sl-s').value,se=document.getElementById('sl-e').value;
  if(!ss||!se){toast('Fill both start and end times','error');return;}
  try{
    const d=await(await fetch('/api/sleep',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sleep_start:ss,sleep_end:se})})).json();
    if(d.error){toast(d.error,'error');}else{toast('Sleep logged: '+d.record.duration+'h ('+d.record.quality+')');loadSleepHistory();loadSummary();}
  }catch(e){toast('Error logging sleep','error');}
}
const EV_CLS={work:'ew',meeting:'em',rest:'er',travel:'et',sleep:'es',other:'eo'};
async function loadEvents(){
  try{
    const d=await(await fetch('/api/calendar/events?days=7')).json();
    document.getElementById('ev-stat').textContent='| '+d.work_hours+'h work, '+d.meetings+' meetings';
    const el=document.getElementById('events-list');
    if(!d.events||!d.events.length){el.innerHTML='<div style="color:var(--muted);font-size:13px;text-align:center;padding:20px">No events this week.</div>';return;}
    el.innerHTML=d.events.slice().reverse().map(e=>
      '<div style="padding:10px;border-bottom:1px solid rgba(255,255,255,.07);display:flex;justify-content:space-between;align-items:center">'+
      '<div><div style="font-weight:600;font-size:13px">'+e.title+' <span class="ep '+(EV_CLS[e.type]||'eo')+'">'+e.type+'</span></div>'+
      '<div style="font-size:11px;color:var(--muted)">'+new Date(e.start_time).toLocaleString()+' to '+new Date(e.end_time).toLocaleTimeString()+'</div></div>'+
      '<button onclick="delEv('+e.id+')" style="background:none;border:none;color:#e74c3c;cursor:pointer;font-size:13px"><i class="fas fa-trash"></i></button></div>'
    ).join('');
  }catch(e){}
}
async function addEvent(){
  const t=document.getElementById('ev-t').value.trim(),s=document.getElementById('ev-s').value,en=document.getElementById('ev-e').value;
  const tp=document.getElementById('ev-tp').value,n=document.getElementById('ev-n').value;
  if(!t||!s||!en){toast('Title, start and end required','error');return;}
  try{
    const d=await(await fetch('/api/calendar/event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t,start_time:s,end_time:en,type:tp,notes:n})})).json();
    if(d.error){toast(d.error,'error');}else{toast('Event added!');document.getElementById('ev-t').value='';document.getElementById('ev-n').value='';loadEvents();}
  }catch(e){toast('Error','error');}
}
async function delEv(id){
  try{await fetch('/api/calendar/event/'+id,{method:'DELETE'});toast('Event deleted');loadEvents();}catch(e){}
}
async function loadBurnout(){
  try{
    const d=await(await fetch('/api/burnout?days=7')).json();
    if(d.burnout_score===null){document.getElementById('bo-lv').innerHTML='<div style="color:var(--muted)">'+d.message+'</div>';return;}
    document.getElementById('bo-s').textContent=d.burnout_score;
    document.getElementById('bo-sl').textContent=(d.avg_sleep_hrs||0)+'h';
    document.getElementById('bo-w').textContent=(d.avg_work_hrs||0)+'h';
    const lm={low:'bg low burnout',moderate:'bw moderate burnout',high:'bb high burnout',critical:'bb CRITICAL burnout'};
    document.getElementById('bo-lv').innerHTML='<span class="'+((lm[d.burnout_level]||'bw').split(' ')[0])+'" style="font-size:15px;padding:8px 20px">'+((lm[d.burnout_level]||d.burnout_level).toUpperCase())+'</span>';
    document.getElementById('bo-alerts').innerHTML=(d.alerts||[]).map(a=>'<div class="ii ib">'+a+'</div>').join('');
  }catch(e){toast('Error loading burnout','error');}
}
async function assessTravel(){
  const dest=document.getElementById('tr-d').value.trim(),date=document.getElementById('tr-dt').value,dur=document.getElementById('tr-dur').value;
  if(!dest||!date){toast('Fill destination and date','error');return;}
  try{
    const d=await(await fetch('/api/travel/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({destination:dest,travel_date:date,duration_days:parseInt(dur)})})).json();
    const el=document.getElementById('tr-res');
    const safe=d.travel_status==='SAFE';
    const unk=d.travel_status==='UNKNOWN';
    if(unk){el.innerHTML='<div class="ii iw">'+d.message+'</div>';return;}
    el.innerHTML='<div class="ts '+(safe?'ts-s':'ts-r')+'">'+
      '<div style="font-size:28px;margin-bottom:8px">'+(safe?'&#9989;':'&#9888;&#65039;')+'</div>'+
      '<div style="font-size:18px;font-weight:700;color:'+(safe?'#1db954':'#e74c3c')+'">'+d.message+'</div>'+
      '<div style="margin-top:12px;font-size:13px;color:var(--muted)">Risk: '+d.risk_score+'/100 &nbsp; Sleep: '+d.avg_sleep_hrs+'h &nbsp; HR: '+d.avg_hr+' BPM</div>'+
      '<div style="margin-top:12px;font-size:12px">'+(d.tips||[]).map(t=>'<div style="margin:4px 0">&#8226; '+t+'</div>').join('')+'</div></div>';
    toast('Travel assessment complete');
  }catch(e){toast('Error assessing travel','error');}
}
async function loadInsights(){
  try{
    const d=await(await fetch('/api/insights')).json();
    const el=document.getElementById('ins-list');
    if(!d.insights||!d.insights.length){el.innerHTML='<div style="color:var(--muted);font-size:13px;text-align:center;padding:30px">'+(d.message||'No insights.')+'</div>';return;}
    const tc={warning:'ib',caution:'iw',good:'ig',info:'in'};
    el.innerHTML=d.insights.map(i=>'<div class="ii '+(tc[i.type]||'in')+'">'+i.msg+'</div>').join('');
    if(d.alerts&&d.alerts.length){el.innerHTML+='<div style="margin-top:16px;font-weight:700;font-size:12px;color:var(--muted)">ACTIVE ALERTS</div>'+d.alerts.map(a=>'<div class="ii ib">'+a+'</div>').join('');}
  }catch(e){toast('Error loading insights','error');}
}
async function loadReport(){
  try{
    const d=await(await fetch('/api/report/weekly')).json();
    const el=document.getElementById('rep-cnt');
    el.innerHTML='<div class="grid-3" style="gap:12px;margin-bottom:16px">'+
      '<div class="sc"><div class="sv">'+d.sleep_avg_hrs+'h</div><div class="sl">Avg Sleep</div></div>'+
      '<div class="sc"><div class="sv">'+d.hr_avg_bpm+'</div><div class="sl">Avg HR BPM</div></div>'+
      '<div class="sc"><div class="sv">'+d.total_work_hours+'h</div><div class="sl">Total Work</div></div></div>'+
      '<div class="grid-3" style="gap:12px;margin-bottom:16px">'+
      '<div class="sc"><div class="sv">'+d.burnout_score+'</div><div class="sl">Burnout Score</div></div>'+
      '<div class="sc"><div class="sv">'+d.recovery_score+'</div><div class="sl">Recovery Score</div></div>'+
      '<div class="sc"><div class="sv">'+d.total_meetings+'</div><div class="sl">Meetings</div></div></div>'+
      '<div class="ii ig"><b>Energy:</b> '+(d.energy_level||'--').toUpperCase()+' &nbsp; <b>Poor Sleep Days:</b> '+d.poor_sleep_days+' &nbsp; <b>HR Records:</b> '+d.hr_records+'</div>'+
      '<div style="margin-top:10px;font-size:11px;color:var(--muted)">Generated: '+new Date(d.generated_at).toLocaleString()+' &nbsp; '+d.disclaimer+'</div>';
  }catch(e){toast('Error generating report','error');}
}
document.addEventListener('DOMContentLoaded',()=>{loadSummary();loadSleepHistory();loadEvents();setInterval(loadSummary,30000);});
</script>
</body>
</html>"""

with open(r'c:/Users/JAYANTH DR/CardioSense.AI_Backend/templates/lifeplanner.html','w',encoding='utf-8') as f:
    f.write(html)
print('lifeplanner.html written successfully')
