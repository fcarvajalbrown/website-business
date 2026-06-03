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

// scroll fade-ins
(function () {
  var els = document.querySelectorAll('.fade-in');
  if (!els.length) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });
  els.forEach(function (el) { io.observe(el); });
})();

// featured projects to show in portfolio
var PROJECTS = [
  {
    name: 'perport',
    lang: 'JavaScript',
    desc: 'GitHub API-powered personal portfolio — auto-pulls repos, stats, and READMEs. Deployed on GitHub Pages.',
    tags: ['GitHub API', 'Vanilla JS', 'CSS'],
    url: 'https://github.com/fcarvajalbrown/perport',
    demo: 'https://fcarvajalbrown.github.io/perport'
  },
  {
    name: 'maskops',
    lang: 'Rust',
    desc: 'Polars expression plugin for GDPR PII masking. 4,000× faster than Presidio on 10k rows. Covers RUT, CPF, CURP, email, phone, IP.',
    tags: ['Rust', 'Polars', 'Python', 'GDPR'],
    url: 'https://github.com/fcarvajalbrown/maskops'
  },
  {
    name: 'lupa-municipal-2026',
    lang: 'HTML',
    desc: 'Chilean municipality cybersecurity audit — 345 municipalities scanned. 82 with MySQL exposed, 221 with cPanel. Single-file interactive dashboard.',
    tags: ['Civic Tech', 'Security', 'Chile'],
    url: 'https://github.com/fcarvajalbrown/lupa-municipal-2026'
  },
  {
    name: 'MuniANCI',
    lang: 'Rust',
    desc: 'Tauri 2 desktop app for Ley 21.663 cybersecurity compliance scanning in Chilean municipalities. EOL enrichment, streaming logs, React GUI.',
    tags: ['Rust', 'Tauri', 'React', 'TypeScript'],
    url: 'https://github.com/fcarvajalbrown/MuniANCI'
  },
  {
    name: 'Nano-FFI',
    lang: 'Zig',
    desc: 'Python-to-Zig FFI library achieving sub-110ns call overhead — 3.8× faster than ctypes. Published on PyPI.',
    tags: ['Zig', 'Python', 'PyPI', 'Performance'],
    url: 'https://github.com/fcarvajalbrown/Nano-FII'
  },
  {
    name: 'PROGRAM.VIRUS',
    lang: 'Rust',
    desc: 'First-person horror/puzzle game built in Bevy 0.18. Neon wireframe aesthetic, fake desktop OS shell, procedural level design.',
    tags: ['Rust', 'Bevy', 'Game Dev', 'WASM'],
    url: 'https://github.com/fcarvajalbrown/PROGRAM.VIRUS'
  }
];

// render portfolio grid
(function () {
  var grid = document.getElementById('portfolio-grid');
  if (!grid) return;

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
})();
