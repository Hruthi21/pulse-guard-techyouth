/* ═══════════════════════════════════════════════════════════════════
   PulseGuard AI — Shared JavaScript Utilities
   Used by: dashboard.html, lifestyle.html, diet.html, emergency.html
   ═══════════════════════════════════════════════════════════════════ */

/* ── Toast notification ──────────────────────────────────────────── */
function showToast(msg, type='') {
  let toast = document.getElementById('pg-toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `pg-toast ${type}`;
  void toast.offsetWidth; // reflow
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3200);
}

/* ── Sidebar toggle (mobile) ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  // Add hamburger to header on mobile
  const header = document.querySelector('.pg-header');
  if (header && window.innerWidth <= 900) {
    const ham = document.createElement('button');
    ham.innerHTML = '<i class="fas fa-bars"></i>';
    ham.style.cssText = 'background:none;border:none;color:var(--light-text);font-size:20px;cursor:pointer;margin-right:12px;';
    ham.onclick = () => sidebar.classList.toggle('mobile-open');
    header.insertBefore(ham, header.firstChild);
  }

  // Highlight active nav item
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    }
  });

  // Animate cards on scroll
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('fade-in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.card').forEach(c => io.observe(c));
});

/* ── Number counter animation ────────────────────────────────────── */
function animateCounter(el, from, to, duration=800) {
  const start = performance.now();
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(from + (to - from) * p);
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ── Format time ─────────────────────────────────────────────────── */
function formatTime(date) {
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}
