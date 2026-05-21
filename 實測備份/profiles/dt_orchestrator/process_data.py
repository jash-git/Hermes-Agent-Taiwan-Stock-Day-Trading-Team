#!/usr/bin/env python3
import csv
import json

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

# ============ 1. Fund CSV ============
with open(f"{SKILL_DIR}/raw_data/twse_fund_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    fund_rows = [r for r in reader if len(r) >= 17]

total_foreign_buy = 0
total_foreign_sell = 0
total_inv_buy = 0
total_inv_sell = 0
total_dealer_net = 0
total_all_net = 0

foreign_net_list = []
all_net_list = []

for row in fund_rows:
    code = row[0].strip()
    name = row[1].strip()
    
    foreign_buy = parse_num(row[2]) + parse_num(row[5])
    foreign_sell = parse_num(row[3]) + parse_num(row[6])
    foreign_net = foreign_buy - foreign_sell
    
    inv_buy = parse_num(row[8])
    inv_sell = parse_num(row[9])
    inv_net = inv_buy - inv_sell
    
    dealer_net = parse_num(row[11])
    all_net = foreign_net + inv_net + dealer_net
    
    total_foreign_buy += foreign_buy
    total_foreign_sell += foreign_sell
    total_inv_buy += inv_buy
    total_inv_sell += inv_sell
    total_dealer_net += dealer_net
    total_all_net += all_net
    
    foreign_net_list.append((code, name, foreign_net))
    all_net_list.append((code, name, all_net))

foreign_net_list.sort(key=lambda x: x[2], reverse=True)
all_net_list.sort(key=lambda x: x[2], reverse=True)

fund_summary = {
    "foreign_buy": total_foreign_buy,
    "foreign_sell": total_foreign_sell,
    "foreign_net": total_foreign_buy - total_foreign_sell,
    "inv_buy": total_inv_buy,
    "inv_sell": total_inv_sell,
    "inv_net": total_inv_buy - total_inv_sell,
    "dealer_net": total_dealer_net,
    "all_net": total_all_net,
    "foreign_top10_buy": foreign_net_list[:10],
    "foreign_top10_sell": foreign_net_list[-10:][::-1],
    "all_top10_buy": all_net_list[:10],
    "all_top10_sell": all_net_list[-10:][::-1],
}

# ============ 2. Market data for limit-up and top turnover ============
limit_up = []
top_turnover = []

with open(f"{SKILL_DIR}/processed_data/market_data_normalized_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    mheader = next(reader)
    print("Market header:", mheader)
    for row in reader:
        if len(row) < 13:
            continue
        code = row[1].strip()
        name = row[2].strip()
        close = parse_num(row[7])
        change_pct = parse_num(row[8])
        volume = parse_num(row[9])  # 成交張數
        amount = parse_num(row[10])  # 成交金額
        
        if change_pct >= 9.5:
            limit_up.append((code, name, close, change_pct, volume, amount))
        top_turnover.append((code, name, close, change_pct, amount))

top_turnover.sort(key=lambda x: x[4], reverse=True)

# ============ 3. Daytrade candidates ============
daytrade = []
with open(f"{SKILL_DIR}/outputs/daytrade_candidates_ranked_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    dheader = next(reader)
    print("Daytrade header:", dheader)
    for row in reader:
        if len(row) < 8:
            continue
        daytrade.append({
            'code': row[0].strip(),
            'name': row[1].strip(),
            'close': row[4].strip(),
            'change_pct': row[5].strip(),
            'volume': row[6].strip(),
            'amplitude': row[7].strip(),
            'avg_price': row[8].strip() if len(row) > 8 else '',
            'score': row[9].strip() if len(row) > 9 else '',
        })

# Output all results
print("\n=== FUND SUMMARY ===")
print(json.dumps(fund_summary, ensure_ascii=False, indent=2))

print("\n=== LIMIT UP STOCKS ===")
for s in limit_up:
    print(f"{s[0]} {s[1]} 收盤:{s[2]} 漲幅:{s[3]}% 成交量:{s[4]} 成交值:{s[5]}")

print("\n=== TOP 15 TURNOVER ===")
for s in top_turnover[:15]:
    print(f"{s[0]} {s[1]} 收盤:{s[2]} 漲跌幅:{s[3]}% 成交值:{s[4]:,.0f}")

print("\n=== DAYTRADE CANDIDATES (top 10) ===")
for d in daytrade[:10]:
    print(f"{d['code']} {d['name']} 收盤:{d['close']} 漲跌幅:{d['change_pct']}% 振幅:{d['amplitude']}% 評分:{d['score']}")
