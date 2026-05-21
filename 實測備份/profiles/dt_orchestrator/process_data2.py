#!/usr/bin/env python3
"""Process TWSE data for report generation."""
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

def fmt_pct(v):
    """Format percentage with sign."""
    if v > 0:
        return f"+{v:.2f}%"
    return f"{v:.2f}%"

def fmt_change(v):
    """Format change with sign."""
    if v > 0:
        return f"+{v:.2f}"
    return f"{v:.2f}"

# ============ 1. Market Stats (JSON) ============
with open(f"{SKILL_DIR}/raw_data/twse_market_stats_20260520.json") as f:
    market_stats = json.load(f)

# ============ 2. Up/Down (JSON) ============
with open(f"{SKILL_DIR}/raw_data/twse_updown_20260520.json") as f:
    updown = json.load(f)

# ============ 3. Indices (JSON) ============
with open(f"{SKILL_DIR}/raw_data/twse_indices_20260520.json") as f:
    indices = json.load(f)

# ============ 4. Fund CSV ============
with open(f"{SKILL_DIR}/raw_data/twse_fund_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    fund_rows = [r for r in reader if len(r) >= 17]

total_foreign_buy = 0
total_foreign_sell = 0
total_inv_buy = 0
total_inv_sell = 0
total_dealer_net = 0
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
    
    foreign_net_list.append((code, name, foreign_net))
    all_net_list.append((code, name, all_net))

foreign_net_list.sort(key=lambda x: x[2], reverse=True)
all_net_list.sort(key=lambda x: x[2], reverse=True)

# ============ 5. Market data CSV ============
# Header: 日期,代號,名稱,市場,開盤價,最高價,最低價,收盤價,昨收價,漲跌幅%,成交張數,成交金額,均價,振幅%,可當沖
limit_up = []
top_turnover = []

with open(f"{SKILL_DIR}/processed_data/market_data_normalized_20260520.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    mheader = next(reader)
    for row in reader:
        if len(row) < 15:
            continue
        code = row[1].strip()
        name = row[2].strip()
        close = parse_num(row[7])   # 收盤價
        change_pct = parse_num(row[9])  # 漲跌幅%
        volume = parse_num(row[10])  # 成交張數
        amount = parse_num(row[11])  # 成交金額
        amplitude = parse_num(row[13])  # 振幅%
        
        if change_pct >= 9.5:
            limit_up.append({
                'code': code, 'name': name, 'close': close,
                'change_pct': change_pct, 'volume': volume,
                'amount': amount, 'amplitude': amplitude
            })
        top_turnover.append({
            'code': code, 'name': name, 'close': close,
            'change_pct': change_pct, 'amount': amount
        })

top_turnover.sort(key=lambda x: x['amount'], reverse=True)
limit_up.sort(key=lambda x: x['change_pct'], reverse=True)

# ============ 6. Daytrade candidates ============
# Header: 代號,名稱,市場,收盤價,漲跌幅%,成交張數,振幅%,均價,當沖評分
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
            'market': row[2].strip(),
            'close': parse_num(row[3]),
            'change_pct': parse_num(row[4]),
            'volume': parse_num(row[5]),
            'amplitude': parse_num(row[6]),
            'avg_price': parse_num(row[7]),
            'score': parse_num(row[8]),
        })

daytrade.sort(key=lambda x: x['score'], reverse=True)

# ============ Print all data for report ============

print("=== MARKET STATS ===")
print(json.dumps(market_stats, ensure_ascii=False))

print("\n=== UPDOWN ===")
print(json.dumps(updown, ensure_ascii=False))

print("\n=== KEY INDICES ===")
key_indices = ["發行量加權股價指數", "臺灣50指數", "臺灣中型100指數", "臺灣資訊科技指數",
               "未含金融指數", "未含電子指數", "小型股300指數", "臺灣高股息指數"]
for idx in indices:
    if idx[0] in key_indices:
        print(f"{idx[0]}: 收盤={idx[1]}, 漲跌={idx[3]}, 漲跌幅={idx[4]}%")

print("\n=== ALL INDICES ===")
for idx in indices:
    print(f"{idx[0]}|{idx[1]}|{idx[2]}|{idx[3]}|{idx[4]}")

print("\n=== FUND TOTALS ===")
print(f"外資買進:{total_foreign_buy}")
print(f"外資賣出:{total_foreign_sell}")
print(f"外資淨買超:{total_foreign_buy - total_foreign_sell}")
print(f"投信買進:{total_inv_buy}")
print(f"投信賣出:{total_inv_sell}")
print(f"投信淨買超:{total_inv_buy - total_inv_sell}")
print(f"自營商淨買超:{total_dealer_net}")
print(f"三大法人淨買超:{total_foreign_buy - total_foreign_sell + total_inv_buy - total_inv_sell + total_dealer_net}")

print("\n=== FOREIGN TOP10 BUY ===")
for r in foreign_net_list[:10]:
    print(f"{r[0]}|{r[1]}|{r[2]}")

print("\n=== FOREIGN TOP10 SELL ===")
for r in foreign_net_list[-10:][::-1]:
    print(f"{r[0]}|{r[1]}|{r[2]}")

print("\n=== ALL TOP10 BUY ===")
for r in all_net_list[:10]:
    print(f"{r[0]}|{r[1]}|{r[2]}")

print("\n=== ALL TOP10 SELL ===")
for r in all_net_list[-10:][::-1]:
    print(f"{r[0]}|{r[1]}|{r[2]}")

print(f"\n=== LIMIT UP ({len(limit_up)} stocks) ===")
for s in limit_up[:30]:
    print(f"{s['code']}|{s['name']}|{s['close']}|{s['change_pct']}|{s['volume']}|{s['amount']}")

print(f"\n=== TOP 15 TURNOVER ===")
for s in top_turnover[:15]:
    print(f"{s['code']}|{s['name']}|{s['close']}|{s['change_pct']}|{s['amount']}")

print(f"\n=== DAYTRADE TOP 15 ===")
for d in daytrade[:15]:
    print(f"{d['code']}|{d['name']}|{d['close']}|{d['change_pct']}|{d['volume']}|{d['amplitude']}|{d['score']}")
