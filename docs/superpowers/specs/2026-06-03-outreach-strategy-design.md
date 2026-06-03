# Outreach Strategy — Design Spec

**Date:** 2026-06-03  
**Goal:** Convert 840–1600 cold leads into discovery calls using a 6-touch, 2-channel sequence (Brevo email + WA-Automate WhatsApp), with no LLM automation and at ~$25/month.

---

## Tools

| Tool | Purpose | Cost |
|------|---------|------|
| Brevo | Email sequences (4 touches) | Free → $25/month Starter |
| WA-Automate (local node.js) | WhatsApp automation (2 touches) | Free (open-source) |
| leads.db (SQLite) | Source of truth for lead status | Free |
| Calendly (free tier) | Call booking link in every email | Free |

---

## Pipeline

```
scrape-today.sh          # raw leads → SQLite + JSON
  → cleanup.py           # remove has_website=1 (mining exempt), no-contact rows
  → final_filter.py      # DNS confirm, professional signals, phase assignment
  → outputs/
      test.csv           # 5–10 leads (1 per sector)
      phase1.csv         # 3rd tier (~300–400 leads)
      phase2.csv         # 2nd tier (~200–300 leads)
      phase3.csv         # best leads (~50–100 leads)
      mining.csv         # direcmin leads (separate pitch)
  → mark_contacted.py    # stamp contacted=1 after each batch send
```

---

## final_filter.py — Checks and phase assignment

### No-website confirmation (DNS-level)

For each lead with a non-null domain:
1. `socket.getaddrinfo(domain)` → NXDOMAIN → confirmed no website
2. `httpx.get(f"https://{domain}", timeout=5)` → refused or empty body → confirmed no website
3. Both pass → domain is live → demote lead to phase1 (don't discard, still has email)

### "Can pay" professional signal scoring (+1 each)

| Signal | How to detect |
|--------|---------------|
| Professional email domain | Not @gmail / @hotmail / @yahoo / @outlook |
| Has phone number | `phone` field is non-null |
| Premium city location | Las Condes, Providencia, Vitacura, Ñuñoa |
| Registered company suffix | Name contains S.A., SPA, Ltda., E.I.R.L., S.A.C. |

Max 4 points. Score stored as `quality_score` in output CSV.

### Phase assignment

| Phase | composite_score | quality_score | no_website confirmed | Volume |
|-------|----------------|---------------|---------------------|--------|
| TEST | Top 1 per sector (best score) | Any | Any | 5–10 |
| phase1 | 4–6 | ≥ 1 | No (directory flag only) | ~300–400 |
| phase2 | 6–8 | ≥ 2 | Yes (DNS) OR quality ≥ 3 | ~200–300 |
| phase3 | 8+ | ≥ 3 | Yes (DNS confirmed) | ~50–100 |
| mining | Any | Any | Exempt (different pitch) | ~121–150 |

Additional phases (later):
- **phase0-bounce**: Hard bounces from any phase → WhatsApp-only follow-up
- **reactivation**: Opened but no reply after 30 days → re-approach with different subject

---

## Message cadence — 6 touches over 14 days

| Day | Touch | Channel | Automated by |
|-----|-------|---------|-------------|
| 0 | Cold intro | Email | Brevo |
| 2 | "Te escribí por email" | WhatsApp | WA-Automate |
| 3 | Short follow-up | Email | Brevo |
| 7 | Value add / portfolio link | Email | Brevo |
| 9 | Last WhatsApp touch | WhatsApp | WA-Automate |
| 14 | Break-up email | Email | Brevo |

Brevo stops the sequence automatically when a lead replies. WA-Automate uses 30–90s random delay between sends to avoid bans. Volume cap: 50 WhatsApp sends/day.

---

## What is automated

| Step | Automated? | Tool |
|------|-----------|------|
| Lead scraping daily | ✅ | scrape-today.sh |
| Filter + phase assignment | ✅ | cleanup.py + final_filter.py |
| Email send + schedule | ✅ | Brevo |
| Email open/click/bounce tracking | ✅ | Brevo |
| Unsubscribe handling | ✅ | Brevo |
| Sequence stop on reply | ✅ | Brevo |
| WhatsApp send + delay | ✅ | WA-Automate |
| Mark as contacted in DB | ✅ (one command) | mark_contacted.py |
| Call booking | ✅ | Calendly link in email |

## What is NOT automated (human only)

| Step | Why |
|------|-----|
| Writing the 4 email templates + 2 WA templates | One-time creative work |
| Reading and qualifying replies | Human judgment required |
| Discovery call | Human |
| Writing proposal | Human |
| Closing the deal | Human |

---

## Send order (strategic)

**Do not send to best leads first.** Cold outreach wisdom:

1. **TEST** — validate open rate (target >30%) and reply rate (target >3%)
2. **phase1** — warm up sender reputation, iterate copy if open rate is low
3. **phase2** — send validated message with good open rate
4. **phase3** — best leads only after message is proven
5. **mining** — separate campaign with industry-specific pitch at any time

---

## Before first send — prerequisites

- [ ] Google Business Profile registered (per pna0.5.md — do before first batch)
- [ ] Calendly link set up with 30-minute discovery call slot
- [ ] 4 email templates written (Spanish)
- [ ] 2 WhatsApp templates written (Spanish, ≤160 chars each)
- [ ] Brevo account created, sender verified, sequence configured
- [ ] WA-Automate installed locally, WhatsApp Business number connected
- [ ] `final_filter.py` built and run on today's clean CSV
- [ ] Test send to yourself verified in inbox (not spam)

---

## Files to build

| File | Purpose |
|------|---------|
| `tools/biz-analyzer/final_filter.py` | DNS check + professional signal scoring + phase CSV output |
| `tools/biz-analyzer/mark_contacted.py` | Stamp contacted=1 in SQLite for a given CSV |
| `tools/wa-automate/send.js` | WA-Automate script: reads CSV, sends templated WA with delay |
