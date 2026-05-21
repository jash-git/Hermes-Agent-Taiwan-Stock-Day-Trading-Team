#!/usr/bin/env python3
"""Get remaining data for report."""
import csv

SKILL_DIR = "/home/vblinux/.hermes/profiles/dt_orchestrator/skills/twse-free-daily"

def parse_num(s):
    s = str(s).strip().replace('"', '').replace(',', '')
    if s in ('', '-', '--'):
        return 0
    try:
        return int(s)
    except:
        try:
            return float(s)
        except:
            return 0

# All limit-up stocks
limit_up = []
with open(f"{SKILL_DIR}/processed_data/market_data_normalized_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    mheader = next(reader)
    for row in reader:
        if len(row) < 15:
            continue
        code = row[1].strip()
        name = row[2].strip()
        close = parse_num(row[7])
        change_pct = parse_num(row[9])
        volume = parse_num(row[10])
        amount = parse_num(row[11])
        
        if change_pct >= 9.5:
            limit_up.append((code, name, close, change_pct, volume, amount))

limit_up.sort(key=lambda x: x[3], reverse=True)

print(f"=== ALL LIMIT UP ({len(limit_up)} stocks) ===")
for s in limit_up:
    amount_wan = s[5] / 10000
    print(f"{s[0]}|{s[1]}|{s[2]}|{s[3]:.2f}|{s[4]}|{amount_wan:.0f}")

# All daytrade candidates
daytrade = []
with open(f"{SKILL_DIR}/outputs/daytrade_candidates_ranked_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    dheader = next(reader)
    for row in reader:
        if len(row) < 9:
            continue
        daytrade.append({
            'code': row[0].strip(),
            'name': row[1].strip(),
            'close': parse_num(row[3]),
            'change_pct': parse_num(row[4]),
            'volume': parse_num(row[5]),
            'amplitude': parse_num(row[6]),
            'score': parse_num(row[8]),
        })

daytrade.sort(key=lambda x: x['score'], reverse=True)

print(f"\n=== ALL DAYTRADE ({len(daytrade)} stocks) ===")
for d in daytrade:
    print(f"{d['code']}|{d['name']}|{d['close']}|{d['change_pct']:.2f}|{d['volume']}|{d['amplitude']:.2f}|{d['score']:.2f}")
