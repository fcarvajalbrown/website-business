# Site v2 Design — fcarvajalbrown.cl

Date: 2026-06-03
Status: Approved, ready for implementation plan

---

## Overview

Full update to fcarvajalbrown.cl covering: bilingual support (ES/EN), new "El trabajo" section, kinetic hero, scroll animations, full SEO layer, clickable pricing cards, Propuesta page, 3 real articles, and DNS fix.

---

## 1. Site Structure

```
/
├── index.html                                    # Spanish (updated)
├── en/
│   └── index.html                                # English (new, hardcoded)
├── propuesta/
│   └── index.html                                # Propuesta page (new)
├── articulos/
│   ├── index.html                                # Articles listing (new)
│   ├── cuanto-cuesta-sitio-web-chile-2026/
│   │   └── index.html                            # Article 1 (new)
│   ├── startups-chilenas-sin-sitio-web/
│   │   └── index.html                            # Article 2 (new)
│   └── sitio-web-dos-semanas-proceso-real/
│       └── index.html                            # Article 3 (new)
└── src/
    ├── styles.css                                # Updated
    └── main.js                                   # Updated
```

Nav order: `Servicios · Proyectos · El trabajo · Propuesta · Artículos · Contacto · ES | EN · GitHub ↗`

Page section order: Banner → Nav → Hero → **El trabajo** → Pricing → Portfolio → Contact → Footer

---

## 2. i18n Convention

**Two self-contained HTML files. No JS translation dictionary.**

- `index.html` = full Spanish content, hardcoded
- `en/index.html` = full English content, hardcoded
- Nav `ES | EN` toggle = plain anchor links (`/` ↔ `/en/`)
- `hreflang` in `<head>` of both files:
  ```html
  <link rel="alternate" hreflang="es" href="https://fcarvajalbrown.cl/" />
  <link rel="alternate" hreflang="en" href="https://fcarvajalbrown.cl/en/" />
  <link rel="alternate" hreflang="x-default" href="https://fcarvajalbrown.cl/" />
  ```
- `main.js` is shared and language-neutral
- `PROJECTS` array stays in `main.js`
- Rationale: JS-based i18n risks EN content not being indexed in Google's first crawl wave

---

## 3. "El trabajo" Section

**Position:** Between hero and pricing.
**Background:** `var(--bg2)` — breaks page rhythm intentionally.
**Pull-quote:** Full-width, escapes `section-inner` max-width, DM Serif italic, `var(--accent)` color. The only element on the site that breaks out of the column.

### Spanish copy

Hay miles de desarrolladores en Chile. La mayoría cobra barato y entrega tarde. Algunos cobran caro y también entregan tarde.

Pasé seis años en la industria minera hablando con ingenieros y ejecutivos de alto nivel que no tienen tiempo para vaguedades. Aprendí que lo único que importa es que el trabajo quede bien y llegue a tiempo.

De día, trabajo para el retailer más grande de Chile. El de la torre. De noche, construyo sitios web desde Arica hasta Punta Arenas. Precio fijo. Dos semanas o te devuelvo el dinero. Si tienes una pregunta a las 11 de la noche, yo contesto.

**Pull-quote:** *"Dos semanas o te devuelvo el dinero. Sin excusas."*

### English copy

There are thousands of developers in Chile. Most charge little and deliver late. Some charge a lot and still deliver late.

I spent six years in the mining industry talking to engineers and senior executives who have no time for vague answers. I learned that the only thing that matters is that the work is right and on time.

By day, I work for the largest retailer in Chile. The one with the tower. At night, I build websites from Arica to Punta Arenas. Fixed price. Two weeks or your money back. If you have a question at 11pm, I answer.

**Pull-quote:** *"Two weeks or your money back. No excuses."*

---

## 4. Kinetic Hero + Scroll Animations

### Kinetic word cycle

Hero headline cycles one phrase in `var(--accent)` color. 2s per word, CSS opacity transition, ~15 lines of JS. No library.

- **ES cycle:** Rápido · Confiable · Sin agencia · A tiempo · Sin sorpresas
- **EN cycle:** Fast · Reliable · No agency · On time · No surprises

### Scroll-triggered fade-ins

`IntersectionObserver` on: "El trabajo", Pricing cards, Portfolio cards, Contact cards.
Effect: `opacity 0→1` + `translateY(12px→0)`, 0.4s ease. No scroll event listeners.

---

## 5. Pricing Cards → WhatsApp + Featured Fix

**Featured card fix:** Landing page card gets `class="featured"` and badge "Recomendado" — it is the standard offer. Web + admin system loses the featured border and gets badge "A medida" — it is a custom quote, not the default. Consulting keeps "Por hora".

Card click order in the grid: Landing page (featured, left) · Web + admin (center) · Consulting (right).



Each pricing card (`div.price-card`) becomes the clickable element. The entire block links to `https://wa.me/56932364993`. No button added inside the card. `cursor: pointer` on the card. Works on WhatsApp Web (desktop) and app (mobile).

---

## 6. SEO Layer

### JSON-LD (in `<head>` of index.html and en/index.html)

Three stacked schemas:
- `Person` — name, url, jobTitle, sameAs (LinkedIn, GitHub)
- `LocalBusiness` — name, address Santiago, areaServed Chile, priceRange
- `Service` — one per offering (landing page, web+admin, consulting) with price and description

### Meta completeness

- `og:image` added (currently missing — needed for WhatsApp link previews). Use `assets/img/fcb_card_front.png` as interim; ideally replace with a dedicated 1200×630px PNG before launch
- `twitter:card` added
- Each subpage gets unique `<title>` and `<meta description>`
- `/articulos/` meta: *"Artículos sobre desarrollo web, startups chilenas y tecnología."*

### DNS fix (critical)

Remove NIC.cl redirector — it sends a 302 to github.io, causing Google to index github.io instead of fcarvajalbrown.cl.

Replace with direct DNS records in NIC.cl:

| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | fcarvajalbrown.github.io |

Then: GitHub repo Settings → Pages → Custom domain → `fcarvajalbrown.cl` → Enforce HTTPS.

---

## 7. Articles (`/articulos/`)

Three real articles. Each gets: unique `<title>`, `<meta description>`, JSON-LD `Article` schema, internal links to `/` and `/propuesta/`.

| Slug | Title | SEO target |
|------|-------|-----------|
| `cuanto-cuesta-sitio-web-chile-2026` | ¿Cuánto cuesta un sitio web en Chile en 2026? | "cuanto cuesta sitio web chile" |
| `startups-chilenas-sin-sitio-web` | El 70% de las startups chilenas no tiene sitio web. Esto les está costando clientes. | "startup chile sin sitio web" |
| `sitio-web-dos-semanas-proceso-real` | Cómo entrego un sitio web en 2 semanas: el proceso real, sin agencia. | "desarrollo web rapido chile" |

Articles listing page (`/articulos/index.html`) shows all 3 with title, excerpt, and read link.

---

## 8. Propuesta Page (`/propuesta/`)

Public page. ES only. **This Propuesta covers the Landing Page tier ($360 lanzamiento / $600 regular). Web + Sistema Interno is quoted separately on request.**

**Structure:**
1. Header: "Propuesta — Landing Page" · subtitle: "Claro, directo, sin sorpresas."
2. Qué incluye
3. Qué no incluye
4. Plazos y garantía
5. Pago
6. Comunicación
7. Entrega y acceso
8. CTA: "Escribir por WhatsApp →" + "Descargar PDF"
9. T&C (small font)

**Qué incluye (expand this — it's longer than what's excluded):**
- Diseño personalizado desde cero — sin templates, sin WordPress, sin constructores de páginas
- Código HTML / CSS / JS puro y limpio, escrito a mano
- Registro de dominio .cl (NIC Chile)
- Hosting en servidor real — incluido el primer año
- HTTPS / SSL (certificado TLS, renovación automática)
- DNS configurado y apuntado correctamente desde el primer día
- Diseño responsive — móvil, tablet y escritorio
- Velocidad optimizada — sin plugins, sin librerías innecesarias, carga rápida en datos móviles chilenos
- Meta tags completos (título, descripción, og:image para previsualizaciones en WhatsApp y redes)
- Configuración de Google Search Console para indexación inmediata
- Botón de contacto WhatsApp integrado
- Hasta 2 rondas de revisión incluidas
- Entrega en máximo 2 semanas — garantía de devolución si no se cumple

**Qué no incluye:**
- Redacción de textos (el cliente provee el contenido o se cotiza aparte)
- Fotografía profesional
- Ilustración o diseño gráfico personalizado
- Pasarela de pagos (Transbank, MercadoPago, etc.)
- Login de usuarios o áreas privadas
- Base de datos propia o lógica de servidor
- Mantenimiento mensual (puede cotizarse por separado)

**Plazos:** 2 semanas máximo desde el pago inicial. Devolución completa sin preguntas si no se cumple. Máximo 2 rondas de revisión incluidas.

**Pago:** 50% al inicio, 50% en entrega. Proyectos sobre USD $1.000: 6 cuotas mensuales a solicitud.

**Hosting:** Incluido el primer año. Administrado por FCB. Cliente recibe credenciales NIC Chile y acceso al dominio.

**T&C (small font):**
> El código fuente del sitio es propiedad de Brøwn Marcó Studios hasta el pago total del servicio. La transferencia de propiedad del repositorio y código fuente requiere un acuerdo adicional. El hosting puede ser transferido al cliente previo acuerdo por escrito.

**PDF:** Static PDF committed to the repo at `docs/propuesta.pdf`. Generated once manually (or via reportlab) from the same content. The "Descargar PDF" link points to this file directly.

---

## 9. Hosting Model (for client sites)

- Chilean shared hosting provider (e.g. Hosting.cl)
- Felipe owns the account
- Client gets running site + domain credentials
- Code ownership transfer = premium, requires separate agreement (see T&C)

---

## Out of scope

- Blog/articles content in English
- Upsell mentions anywhere on the Propuesta page
- LinkedIn Sales Navigator
- GitHub Pages for client sites (client sites go on real server)
