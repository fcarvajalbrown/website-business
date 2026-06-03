/**
 * send.js — WhatsApp batch sender for outreach phase CSVs.
 *
 * Usage:
 *   node send.js <path/to/phase.csv>            # real send
 *   node send.js <path/to/phase.csv> --dry-run  # print without sending
 *
 * Environment variables:
 *   WA_TEMPLATE  - Message template. Use {company} and {city} as placeholders.
 *   WA_MAX       - Max sends per run (default 50)
 *   WA_MIN_DELAY - Min ms between sends (default 30000)
 *   WA_MAX_DELAY - Max ms between sends (default 90000)
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const { parse } = require('csv-parse/sync');

// ── Config ────────────────────────────────────────────────────────────────────
const CSV_PATH = process.argv.find(a => a.endsWith('.csv'));
const DRY_RUN  = process.argv.includes('--dry-run');

const TEMPLATE = process.env.WA_TEMPLATE ||
    'Hola {company} 👋 Vi que no tienen sitio web todavía. Soy Felipe, desarrollador web freelance en Chile — ayudo a empresas a tener presencia online en 2 semanas. ¿Tienen 15 min esta semana para conversar? Pueden ver mi trabajo en fcarvajalbrown.cl';

const MAX_SENDS  = parseInt(process.env.WA_MAX       || '50',    10);
const MIN_DELAY  = parseInt(process.env.WA_MIN_DELAY || '30000', 10);
const MAX_DELAY  = parseInt(process.env.WA_MAX_DELAY || '90000', 10);

// ── Helpers ───────────────────────────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));

const randomDelay = () =>
    Math.floor(Math.random() * (MAX_DELAY - MIN_DELAY + 1)) + MIN_DELAY;

/**
 * Normalise a Chilean phone number → WhatsApp chat ID (56XXXXXXXXX@c.us).
 * Handles: (9)62063759, (2)22034072, +56 9 1234 5678, 56912345678
 */
function formatPhone(raw) {
    if (!raw || !raw.trim()) return null;

    let num = raw.replace(/[\s\-().]/g, '');
    if (num.startsWith('+')) num = num.slice(1);

    // Already has country code 56
    if (num.startsWith('56') && num.length >= 10) return num + '@c.us';

    // Mobile: 9 digits starting with 9
    if (num.startsWith('9') && num.length === 9) return '569' + num + '@c.us';

    // Landline or other: prepend 56
    if (num.length >= 7) return '56' + num + '@c.us';

    return null;
}

const renderTemplate = (tpl, row) =>
    tpl
        .replace(/\{company\}/g, row.company || 'equipo')
        .replace(/\{city\}/g,    row.city    || 'Chile')
        .replace(/\{sector\}/g,  row.sector  || '');

// ── Main ─────────────────────────────────────────────────────────────────────
async function main() {
    if (!CSV_PATH) {
        console.error('Usage: node send.js <path/to/phase.csv> [--dry-run]');
        process.exit(1);
    }

    const rows     = parse(fs.readFileSync(CSV_PATH, 'utf8'), { columns: true, skip_empty_lines: true });
    const sendable = rows.filter(r => r.phone && r.phone.trim());

    console.log(`CSV:     ${CSV_PATH}`);
    console.log(`Rows:    ${rows.length} total | ${sendable.length} with phone`);
    console.log(`Limits:  max ${MAX_SENDS} sends | ${MIN_DELAY/1000}–${MAX_DELAY/1000}s delay`);

    if (DRY_RUN) {
        console.log('\n⚠️  DRY RUN — no messages will be sent\n');
        for (const row of sendable.slice(0, 5)) {
            const chatId = formatPhone(row.phone);
            console.log(`→ ${row.company} | ${row.phone} → ${chatId || 'INVALID'}`);
            console.log(`  "${renderTemplate(TEMPLATE, row)}"\n`);
        }
        if (sendable.length > 5) console.log(`  ... and ${sendable.length - 5} more`);
        process.exit(0);
    }

    const logPath = CSV_PATH.replace('.csv', '-sent.log');
    const log     = fs.createWriteStream(logPath, { flags: 'a' });
    const stamp   = () => new Date().toISOString();

    const client = new Client({
        authStrategy: new LocalAuth({ clientId: 'biz-outreach' }),
        puppeteer: { headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] },
    });

    client.on('qr', qr => {
        console.log('\nScan this QR code in WhatsApp (Settings → Linked devices → Link a device):');
        qrcode.generate(qr, { small: true });
    });

    client.on('authenticated', () => console.log('✓ Authenticated'));

    client.on('ready', async () => {
        console.log('✓ WhatsApp ready. Sending...\n');
        let sent = 0, skipped = 0;

        for (const row of sendable) {
            if (sent >= MAX_SENDS) {
                console.log(`\nLimit of ${MAX_SENDS} reached. Run again tomorrow.`);
                break;
            }

            const chatId = formatPhone(row.phone);
            if (!chatId) {
                log.write(`${stamp()} | SKIP  | ${row.company} | bad phone: ${row.phone}\n`);
                skipped++;
                continue;
            }

            const msg = renderTemplate(TEMPLATE, row);
            try {
                await client.sendMessage(chatId, msg);
                sent++;
                log.write(`${stamp()} | SENT  | ${row.company} | ${row.phone}\n`);
                console.log(`[${sent}/${MAX_SENDS}] ✓ ${row.company} (${row.phone})`);
            } catch (err) {
                log.write(`${stamp()} | ERROR | ${row.company} | ${row.phone} | ${err.message}\n`);
                console.error(`[${sent}/${MAX_SENDS}] ✗ ${row.company} — ${err.message}`);
                skipped++;
            }

            if (sent < MAX_SENDS) {
                const d = randomDelay();
                console.log(`  ⏱  ${Math.round(d / 1000)}s...`);
                await sleep(d);
            }
        }

        log.end();
        console.log(`\nDone. Sent: ${sent} | Skipped: ${skipped}`);
        console.log(`Log: ${logPath}`);
        process.exit(0);
    });

    client.on('auth_failure', msg => { console.error('Auth failed:', msg); process.exit(1); });
    client.initialize();
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
