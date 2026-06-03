# Send Log — 03-06-2026

Mark each batch after uploading to Brevo AND sending the WhatsApp run.

---

## TEST (4 leads)

| Canal | Enviado | Fecha | Notas |
|-------|---------|-------|-------|
| Email (Brevo) | [ ] | | |
| WhatsApp | [ ] | | |

---

## PHASE 1 — 1,146 leads total (5 chunks)

Enviar chunk por chunk. Esperar 2–3 días entre cada uno para monitorear open rate.

| Chunk | Leads | Email enviado | WA enviado | Fecha email | Fecha WA | Notas |
|-------|-------|--------------|------------|-------------|----------|-------|
| chunk1 | 230 | [ ] | [ ] | | | |
| chunk2 | 230 | [ ] | [ ] | | | |
| chunk3 | 230 | [ ] | [ ] | | | |
| chunk4 | 230 | [ ] | [ ] | | | |
| chunk5 | 226 | [ ] | [ ] | | | |

---

## PHASE 2 (460 leads)

| Canal | Enviado | Fecha | Notas |
|-------|---------|-------|-------|
| Email (Brevo) | [ ] | | Enviar solo después de validar phase1 (>3% reply) |
| WhatsApp | [ ] | | |

---

## MINING (151 leads — pitch diferente)

| Canal | Enviado | Fecha | Notas |
|-------|---------|-------|-------|
| Email (Brevo) | [ ] | | Usar variante minería de email-templates.md |
| WhatsApp | [ ] | | |

---

## PHASE 3 (206 leads — mejores leads)

| Canal | Enviado | Fecha | Notas |
|-------|---------|-------|-------|
| Email (Brevo) | [ ] | | Enviar solo con mensaje probado y open rate >30% |
| WhatsApp | [ ] | | |

---

## Métricas de seguimiento

Actualizar después de cada batch.

| Fase | Enviados | Abiertos | Respuestas | Llamadas | Clientes |
|------|----------|----------|------------|----------|---------|
| test | | | | | |
| phase1-chunk1 | | | | | |
| phase1-chunk2 | | | | | |
| phase1-chunk3 | | | | | |
| phase1-chunk4 | | | | | |
| phase1-chunk5 | | | | | |
| phase2 | | | | | |
| mining | | | | | |
| phase3 | | | | | |

---

## Recordatorios

- Después de cada batch: `python3 mark_contacted.py outputs/03-06-2026-phaseN.csv`
- Open rate < 20% → cambiar asunto antes del siguiente chunk
- Reply rate < 1% → revisar cuerpo del email antes de phase2
- Esperar al menos phase1-chunk2 antes de enviar mining o phase2
