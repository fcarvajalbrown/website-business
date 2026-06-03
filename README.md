# fcarvajalbrown.cl

Personal site for Felipe Carvajal Brown — software developer based in Santiago, Chile.

## Structure

```
.
├── index.html          # Single-page site (landing + portfolio + contact)
├── src/
│   ├── styles.css      # All styles + design tokens
│   └── main.js         # Countdown timer + portfolio renderer
├── assets/
│   ├── palette.json    # Brand color tokens
│   ├── fcb_card_front.svg
│   ├── fcb_card_back.svg
│   ├── img/
│   │   ├── fcb_card_front.png   # 300 DPI, 3mm bleed
│   │   └── fcb_card_back.png
└── README.md
```

## Deploy

Push to `fcarvajalbrown/website-business` repo.  
In Settings → Pages → Source: `main` branch, `/ (root)`.  
Configure `fcarvajalbrown.cl` CNAME at NIC Chile pointing to `fcarvajalbrown.github.io`.

## DNS (NIC Chile)

| Type  | Host | Value                        |
|-------|------|------------------------------|
| A     | @    | 185.199.108.153               |
| A     | @    | 185.199.109.153               |
| A     | @    | 185.199.110.153               |
| A     | @    | 185.199.111.153               |
| CNAME | www  | fcarvajalbrown.github.io      |

## Business cards

Print-ready files in `assets/` — upload PNG or SVG to [aloprint.cl](https://aloprint.cl).  
Spec: Tarjeta Clásica Premium, 9×5cm, 300gr, matte laminate.
