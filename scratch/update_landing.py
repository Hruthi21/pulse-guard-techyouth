import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of CardioSense.AI with PulseGuard AI
content = content.replace("CardioSense.AI", "PulseGuard AI")
content = content.replace("CardioSense", "PulseGuard")

# Update navbar section
new_navbar = """  <!-- NAVBAR -->
  <nav class="navbar" style="background: rgba(10, 10, 15, 0.95); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 10px 0;">
    <div class="container navbar-content" style="max-width: 1440px; width: 95%; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
      <a href="#home" class="logo" style="text-decoration: none; display: flex; align-items: center; gap: 10px;">
        <i class="fas fa-heartbeat" style="color: var(--primary, #1db954); font-size: 26px;"></i>
        <span style="font-weight: 800; font-size: 22px; background: linear-gradient(90deg, #1db954 0%, #2ecc71 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PulseGuard AI</span>
      </a>

      <div class="nav-links" style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        <a href="#home" class="active" style="padding: 6px 10px; font-size: 13.5px; font-weight: 600;"><i class="fas fa-home"></i> Home</a>
        <a href="/dashboard" style="color: #1db954; font-weight: 700; padding: 6px 10px; font-size: 13.5px;"><i class="fas fa-chart-line"></i> Dashboard</a>
        <a href="/heartrate" style="padding: 6px 10px; font-size: 13.5px;"><i class="fas fa-heartbeat"></i> Heart Rate (PPG)</a>
        <a href="/appointments" style="color: #2ecc71; font-weight: 700; padding: 6px 10px; font-size: 13.5px;"><i class="fas fa-video"></i> Video Consult</a>
        <a href="/doctor" style="color: #3498db; font-weight: 700; padding: 6px 10px; font-size: 13.5px;"><i class="fas fa-user-md"></i> Doctor Portal</a>
        <a href="/reports" style="padding: 6px 10px; font-size: 13.5px;"><i class="fas fa-file-medical"></i> Reports</a>
        <a href="/chat" style="padding: 6px 10px; font-size: 13.5px;"><i class="fas fa-robot"></i> AI Chat</a>
        
        <a href="/emergency" style="background: linear-gradient(135deg, #e74c3c, #c0392b); color: #fff !important; font-weight: 800; padding: 7px 14px; border-radius: 20px; font-size: 13px; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 10px rgba(231,76,60,0.4); margin: 0 4px;">
          <i class="fas fa-ambulance"></i> 🚨 SOS Emergency
        </a>

        {% if current_user.is_authenticated %}
        <a href="/logout" style="color: #e74c3c; border: 1px solid rgba(231,76,60,0.4); padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; text-decoration: none;">
          <i class="fas fa-sign-out-alt"></i> Logout ({{ current_user.full_name.split()[0] }})
        </a>
        {% else %}
        <a href="/login" style="color: var(--primary, #1db954); font-weight: 700; border: 1px solid var(--primary, #1db954); padding: 6px 12px; border-radius: 6px; font-size: 13px; text-decoration: none;">
          <i class="fas fa-sign-in-alt"></i> Login
        </a>
        <a href="/register" style="color: #fff; background: var(--primary, #1db954); font-weight: 700; padding: 6px 14px; border-radius: 6px; font-size: 13px; text-decoration: none;">
          <i class="fas fa-user-plus"></i> Register
        </a>
        {% endif %}
      </div>
    </div>
  </nav>"""

# Replace existing navbar
content = re.sub(r'<!-- NAVBAR -->.*?<!-- HERO SECTION -->', new_navbar + '\n\n  <!-- HERO SECTION -->', content, flags=re.DOTALL)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated templates/index.html with PulseGuard AI branding and organized navbar")
