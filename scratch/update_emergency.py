import re

with open('templates/emergency.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Simulation Notice Banner right after `<div class="pg-content">`
notice_banner = """
    <!-- Prominent Simulation Transparency Banner -->
    <div style="background: rgba(243, 156, 18, 0.12); border: 1px solid rgba(243, 156, 18, 0.4); border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px;" class="fade-in">
      <i class="fas fa-exclamation-triangle" style="color: #f39c12; font-size: 24px; flex-shrink: 0;"></i>
      <div style="font-size: 13px; line-height: 1.5; color: #e6e6e6;">
        <strong style="color: #f39c12; text-transform: uppercase; letter-spacing: 0.5px;">Simulation & Demo Notice:</strong>
        Ambulance fleet tracking, positions, and ETA estimations shown on this map are <strong>simulated demonstrations</strong>. 
        In a real life-threatening emergency, <strong>always dial 112 immediately</strong> or go directly to the nearest hospital.
        <span style="color:#2ecc71;">(Real SMS and voice alert calls are dispatched to your verified emergency contacts when SOS is pressed).</span>
      </div>
    </div>
"""

if "<!-- Prominent Simulation Transparency Banner -->" not in html:
    html = html.replace('<div class="pg-content">', '<div class="pg-content">\n' + notice_banner)

# 2. Replace hardcoded contacts with dynamic contacts loop
old_contacts = re.search(r'<div id="contacts-list">.*?</div>\s*</div>\s*<!-- Alert log -->', html, re.DOTALL)
if old_contacts:
    new_contacts = """<div id="contacts-list">
            {% if contacts %}
              {% for c in contacts %}
              <div class="hospital-card" style="cursor:default; {% if c.type == 'emergency' %}border-color:rgba(231,76,60,0.4);{% endif %}">
                <div class="hospital-icon" style="{% if c.type == 'emergency' %}background:rgba(231,76,60,0.2); color:#e74c3c;{% else %}background:rgba(46,204,113,0.15); color:#2ecc71;{% endif %}">
                  <i class="fas {{ c.icon }}"></i>
                </div>
                <div>
                  <div class="hospital-name">{{ c.name }}</div>
                  <div class="hospital-phone">{{ c.phone }}</div>
                  <div style="font-size:11px; color:var(--muted);">
                    {{ c.relation }} {% if c.is_user_saved %}<span style="color:#2ecc71; font-weight:700;">&bull; Saved in Profile</span>{% endif %}
                  </div>
                </div>
                {% if c.phone and c.phone != 'Not provided' %}
                <a href="tel:{{ c.phone }}" style="margin-left:auto; color:{% if c.type == 'emergency' %}var(--danger){% else %}var(--primary){% endif %}; font-size:18px;" title="Call {{ c.name }}">
                  <i class="fas fa-phone-alt"></i>
                </a>
                {% endif %}
              </div>
              {% endfor %}
            {% else %}
              <div style="padding:15px; font-size:13px; color:var(--muted);">
                No emergency contacts saved. Please configure in your profile.
              </div>
            {% endif %}
          </div>
        </div>

        <!-- Alert log -->"""
    html = html[:old_contacts.start()] + new_contacts + html[old_contacts.end():]

# 3. Add Simulated Tag to Ambulance Cards & Fleet header
html = html.replace('<div class="card-title">Active Ambulances</div>', '<div class="card-title">Simulated Ambulances</div>')
html = html.replace('<div class="card-sub">Units in Bengaluru</div>', '<div class="card-sub"><span style="color:#f39c12; font-weight:700;">[DEMO FLEET]</span> Active in Demo</div>')
html = html.replace('<div style="font-weight:700;font-size:14px;"><i class="fas fa-ambulance" style="color:var(--primary);margin-right:6px;"></i>Active Fleet</div>',
                    '<div style="font-weight:700;font-size:14px;"><i class="fas fa-ambulance" style="color:var(--primary);margin-right:6px;"></i>Active Fleet <span style="font-size:11px; background:rgba(243,156,18,0.2); color:#f39c12; border:1px solid rgba(243,156,18,0.4); padding:2px 8px; border-radius:10px; margin-left:6px;">SIMULATED</span></div>')

# 4. Enhance Geolocation JavaScript in emergency.html
geo_script = """
// ── Real Browser Geolocation ──────────────────────────────────────────────
function acquireRealLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                USER_LAT = pos.coords.latitude;
                USER_LNG = pos.coords.longitude;
                userMarker.setLatLng([USER_LAT, USER_LNG]);
                map.setView([USER_LAT, USER_LNG], 14);
                
                const coordStr = `${USER_LAT.toFixed(4)}°N, ${USER_LNG.toFixed(4)}°E`;
                document.getElementById('user-coords').textContent = coordStr;
                document.getElementById('user-location-display').textContent = 'Live GPS Position';
                addAlertLog('📍 Real GPS location acquired: ' + coordStr);

                // Reverse geocoding for city / suburb
                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${USER_LAT}&lon=${USER_LNG}`)
                    .then(r => r.json())
                    .then(geo => {
                        if (geo && geo.address) {
                            const addr = geo.address;
                            const locName = addr.suburb || addr.neighbourhood || addr.city || addr.town || addr.county || 'Your Area';
                            const stateName = addr.state || '';
                            document.getElementById('user-location-display').textContent = `${locName}${stateName ? ', ' + stateName : ''} (Live GPS)`;
                            addAlertLog(`📍 Detected area: ${locName}`);
                        }
                    }).catch(()=>{});

                // Reposition simulated fleet around user's real location for realistic demo
                reseedFleetAroundUser(USER_LAT, USER_LNG);
                updateNearestAmbulance();
                initHospitals();
            },
            (err) => {
                console.warn("Browser GPS permission denied or timed out. Using fallback coords.", err);
                addAlertLog('⚠️ Browser GPS not available; using default coordinates.');
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    }
}

function reseedFleetAroundUser(lat, lng) {
    const offsets = [
        { dLat: 0.012, dLng: -0.015, zone: "North-West" },
        { dLat: -0.018, dLng: 0.010, zone: "South-East" },
        { dLat: 0.008, dLng: 0.016, zone: "East" },
        { dLat: -0.010, dLng: -0.012, zone: "South-West" },
        { dLat: 0.005, dLng: 0.004, zone: "Central" }
    ];
    ambulances.forEach((a, idx) => {
        if (offsets[idx]) {
            a.lat = lat + offsets[idx].dLat;
            a.lng = lng + offsets[idx].dLng;
            if (ambMarkers[a.id]) {
                ambMarkers[a.id].setLatLng([a.lat, a.lng]);
            }
        }
    });
}

window.addEventListener('DOMContentLoaded', acquireRealLocation);
"""

if "function acquireRealLocation()" not in html:
    html = html.replace('// ── Animate ambulances ─────────────────────────────────────────────────────', geo_script + '\n// ── Animate ambulances ─────────────────────────────────────────────────────')

with open('templates/emergency.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Successfully updated emergency.html with real geolocation, real saved contacts, and simulation transparency labels")
