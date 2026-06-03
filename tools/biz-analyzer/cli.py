import argparse, importlib, signal
from db import append_lead, export_csv, load_seen, stats as db_stats
from scorer import score

_stop = False

def _handle_sigint(sig, frame):
    global _stop
    print("\nInterrupt — finishing current record then stopping.", flush=True)
    _stop = True

signal.signal(signal.SIGINT, _handle_sigint)

SOURCE_MAP = {
    "amarillas": "sources.amarillas",
    "direcmin": "sources.direcmin",
    "pymesdechile": "sources.pymesdechile",
}

SECTORS_IN_ORDER = ["saas", "healthtech", "mining", "agtech", "retail"]


def cmd_scrape(args):
    sources = list(SOURCE_MAP.keys()) if args.all_sources else [args.source]
    sectors = SECTORS_IN_ORDER if args.all_sectors else [args.sector]
    seen = load_seen()
    count = 0

    for src_name in sources:
        mod = importlib.import_module(SOURCE_MAP[src_name])
        for sector in sectors:
            print(f"[{src_name}] {sector}...", flush=True)
            for lead in mod.scrape(sector, city=args.city):
                if _stop:
                    break
                key = (lead.get("company", ""), lead.get("source", ""))
                if key in seen:
                    continue
                seen.add(key)
                lead = score(lead)
                if lead["composite_score"] == 0:
                    continue
                append_lead(lead)
                count += 1
                tag = lead.get("email") or "no-email"
                print(f"  + [{lead['composite_score']}] {lead['company']} — {tag}", flush=True)
            if _stop:
                break
        if _stop:
            break

    print(f"\nSaved {count} new leads.")
    csv_path = export_csv()
    print(f"CSV: {csv_path}")


def cmd_stats(args):
    s = db_stats()
    print(f"Total: {s['total']}  With email: {s['with_email']}")
    for sector, n in sorted(s["by_sector"].items()):
        print(f"  {sector}: {n}")


def cmd_export(args):
    print(f"Exported: {export_csv()}")


def main():
    parser = argparse.ArgumentParser(description="biz-analyzer — Chilean SME lead scraper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scrape")
    g1 = p.add_mutually_exclusive_group(required=True)
    g1.add_argument("--source", choices=list(SOURCE_MAP.keys()))
    g1.add_argument("--all-sources", action="store_true")
    g2 = p.add_mutually_exclusive_group(required=True)
    g2.add_argument("--sector", choices=SECTORS_IN_ORDER)
    g2.add_argument("--all-sectors", action="store_true")
    p.add_argument("--city", default=None)
    p.set_defaults(func=cmd_scrape)

    q = sub.add_parser("stats")
    q.set_defaults(func=cmd_stats)

    e = sub.add_parser("export")
    e.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
