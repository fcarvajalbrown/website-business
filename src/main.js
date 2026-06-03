// kinetic hero word cycle — skipped if page defines its own (e.g. /en/)
if (!window.__heroCycleDefined) {
  (function () {
    var words = ['Rápido.', 'Confiable.', 'Sin agencia.', 'A tiempo.', 'Sin sorpresas.'];
    var el = document.getElementById('hero-cycle');
    if (!el) return;
    var i = 0;
    setInterval(function () {
      el.style.opacity = '0';
      setTimeout(function () {
        i = (i + 1) % words.length;
        el.textContent = words[i];
        el.style.opacity = '1';
      }, 350);
    }, 2200);
  })();
}

// featured projects — pinned repos from github.com/fcarvajalbrown
var PROJECTS = [
  {
    name: 'MaskOps',
    lang: 'Rust',
    desc: 'High-speed PII masking as a Polars plugin — powered by Rust. Runs directly on Arrow buffers, no NLP models, no intermediate files.',
    tags: ['Rust', 'Polars', 'GDPR', 'PII'],
    url: 'https://github.com/fcarvajalbrown/MaskOps'
  },
  {
    name: 'Nano-FII',
    lang: 'Zig',
    desc: 'Minimalist Python-to-Zig FFI bridge. 79ns call overhead via comptime trampolines — 4× faster than ctypes.',
    tags: ['Zig', 'Python', 'FFI', 'Performance'],
    url: 'https://github.com/fcarvajalbrown/Nano-FII'
  },
  {
    name: 'Auth4Free',
    lang: 'Rust',
    desc: 'Secure, modular authentication library for Rust. Password validation, JWT tokens, bcrypt hashing and security tooling for web services and APIs.',
    tags: ['Rust', 'JWT', 'bcrypt', 'Security'],
    url: 'https://github.com/fcarvajalbrown/Auth4Free'
  },
  {
    name: 'SentinelNode',
    lang: 'TypeScript',
    desc: 'Self-hosted security dashboard — scans directories for leaked secrets and audits HTTP security headers. Rust + Node.js, deployable with Docker Compose.',
    tags: ['TypeScript', 'Rust', 'Security', 'Docker'],
    url: 'https://github.com/fcarvajalbrown/SentinelNode'
  },
  {
    name: 'port-scanner',
    lang: 'Python',
    desc: 'Infrastructure recon tool — resolves domains via DNS and scans for open ports.',
    tags: ['Python', 'DNS', 'Security', 'Recon'],
    url: 'https://github.com/fcarvajalbrown/port-scanner'
  },
  {
    name: 'pipeonjoy',
    lang: 'Python',
    desc: 'Vaporwave composition wizard — AI-free, lyrics-driven, modal. Win98 GUI with live FluidSynth previews.',
    tags: ['Python', 'MIDI', 'FluidSynth', 'Music'],
    url: 'https://github.com/fcarvajalbrown/pipeonjoy'
  }
];

// render portfolio grid, then wire up animations
(function () {
  var grid = document.getElementById('portfolio-grid');
  if (grid) {
    PROJECTS.forEach(function (p) {
      var card = document.createElement('div');
      card.className = 'project-card fade-in';

      var tagsHtml = p.tags.map(function (t) {
        return '<span class="proj-tag">' + t + '</span>';
      }).join('');

      var demoBtn = p.demo
        ? '<a href="' + p.demo + '" target="_blank" rel="noopener" class="btn" style="padding:6px 14px;font-size:12px;">Live ↗</a>'
        : '';

      card.innerHTML =
        '<div class="project-header">' +
          '<span class="project-name">' + p.name + '</span>' +
          '<span class="project-lang">' + p.lang + '</span>' +
        '</div>' +
        '<p class="project-desc">' + p.desc + '</p>' +
        '<div class="project-footer">' +
          tagsHtml +
          '<div style="flex:1"></div>' +
          '<a href="' + p.url + '" target="_blank" rel="noopener" class="btn" style="padding:6px 14px;font-size:12px;">GitHub ↗</a>' +
          demoBtn +
        '</div>';

      grid.appendChild(card);
    });
  }

  var els = Array.prototype.slice.call(document.querySelectorAll('.fade-in'));
  if (!els.length) return;

  function show(el) { el.classList.add('visible'); }

  // No observer support → show everything immediately.
  if (!('IntersectionObserver' in window)) { els.forEach(show); return; }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { show(e.target); io.unobserve(e.target); }
    });
  }, { threshold: 0.05, rootMargin: '0px 0px -8% 0px' });

  els.forEach(function (el) { io.observe(el); });

  // Reveal anything already in view on load (double rAF so layout is settled).
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      els.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < window.innerHeight * 1.1) show(el);
      });
    });
  });

  // BULLETPROOF FALLBACK: after 2.5s, force-show everything still hidden — so a
  // missed observer event or stale cache can never leave the page blank.
  setTimeout(function () { els.forEach(show); }, 2500);
})();
