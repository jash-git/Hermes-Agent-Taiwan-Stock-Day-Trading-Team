#!/usr/bin/env python3
"""Generate TWSE 20260520 post-market analysis report."""

import csv
import json
import os

BASE = "/home/vblinux/.hermes/profiles/dt_orchestrator/skills/twse-free-daily"

def parse_num(s):
    """Remove commas and convert to int/float."""
    if s is None:
        return 0
    s = str(s).strip().replace(',', '').replace('"', '')
    if s in ('', '--', '-', '除息', '除權'):
        return 0
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except:
        return 0

def parse_float(s):
    s = str(s).strip().replace(',', '').replace('"', '')
    if s in ('', '--', '-'):
        return 0.0
    try:
        return float(s)
    except:
        return 0.0

# ========== 1. Read Market Stats ==========
with open(os.path.join(BASE, "raw_data/twse_market_stats_20260520.json"), "r") as f:
    market_stats = json.load(f)

# Extract totals
total_row = None
stock_row = None
for row in market_stats:
    if row[0] == "總計(1~15)":
        total_row = row
    if row[0] == "1.一般股票":
        stock_row = row
    if row[0] == "證券合計(1+6+14+15)":
        stock_total_row = row

total_value = parse_num(total_row[1])  # 成交金額
total_shares = parse_num(total_row[2])  # 成交股數
total_txns = parse_num(total_row[3])    # 成交筆數

stock_value = parse_num(stock_row[1])
stock_shares = parse_num(stock_row[2])
stock_txns = parse_num(stock_row[3])

# ========== 2. Read Up/Down counts ==========
with open(os.path.join(BASE, "raw_data/twse_updown_20260520.json"), "r") as f:
    updown = json.load(f)

# updown[0]: 上上漲(漲停) -> [上市, 上櫃]
# updown[1]: 下跌(跌停)
# updown[2]: 持平
# updown[3]: 未成交
# updown[4]: 無比價

def parse_updown_pair(s):
    """Parse '4,486(154)' -> (4486, 154)"""
    s = s.replace(',', '')
    if '(' in s:
        main, sub = s.split('(')
        return int(main), int(sub.replace(')', ''))
    return int(s), 0

up_twse, uplimit_twse = parse_updown_pair(updown[0][1])
up_tpex, uplimit_tpex = parse_updown_pair(updown[0][2])
down_twse, downlimit_twse = parse_updown_pair(updown[1][1])
down_tpex, downlimit_tpex = parse_updown_pair(updown[1][2])
flat_twse = parse_num(updown[2][1])
flat_tpex = parse_num(updown[2][2])

# ========== 3. Read Indices ==========
with open(os.path.join(BASE, "raw_data/twse_indices_20260520.json"), "r") as f:
    indices = json.load(f)

# Find main index
main_idx = None
for row in indices:
    if row[0] == "發行量加權股價指數":
        main_idx = row
        break

main_close = parse_float(main_idx[1])
main_sign = main_idx[2]
main_change = parse_float(main_idx[3])
main_pct = parse_float(main_idx[4])

# Category indices (skip the first ~15 non-category indices)
category_indices = []
skip_names = {"寶島股價指數", "發行量加權股價指數", "臺灣公司治理100指數", "臺灣50指數",
              "臺灣50權重上限30%指數", "臺灣中型100指數", "臺灣資訊科技指數", "臺灣發達指數",
              "臺灣高股息指數", "臺灣就業99指數", "臺灣高薪100指數", "未含金融指數",
              "未含電子指數", "未含金融電子指數", "小型股300指數",
              "臺指日報酬兩倍指數", "臺指反向一倍指數", "電子類兩倍槓桿指數", "電子類反向指數"}

for row in indices:
    name = row[0]
    if name in skip_names or '其他類指數' in name:
        continue
    if '指數' in name:
        sign = row[2]
        pct = parse_float(row[4])
        change = parse_float(row[3])
        close_val = parse_float(row[1])
        if sign == '+':
            actual_pct = abs(pct)
        elif sign == '-':
            actual_pct = -abs(pct)
        else:
            actual_pct = 0
        category_indices.append({
            'name': name.replace('指數', '').strip(),
            'close': close_val,
            'change': change,
            'pct': actual_pct,
            'sign': sign
        })

# Sort by pct
category_indices_sorted = sorted(category_indices, key=lambda x: x['pct'], reverse=True)
top5_strong = category_indices_sorted[:5]
top5_weak = category_indices_sorted[-5:]

# ========== 4. Read Three Major Investors (三大法人) ==========
fund_data = []
fund_total = {'foreign': 0, 'trust': 0, 'dealer': 0, 'total': 0}

with open(os.path.join(BASE, "raw_data/twse_fund_20260520.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 18:
            continue
        code = row[0].strip()
        name = row[1].strip()
        foreign_net = parse_num(row[4])  # 外陸資買賣超(不含外資自營商)
        foreign_dealer_net = parse_num(row[7])  # 外資自營商買賣超
        foreign_total = foreign_net + foreign_dealer_net
        trust_net = parse_num(row[10])  # 投信買賣超
        dealer_self_net = parse_num(row[13])  # 自營商(自行買賣)
        dealer_hedge_net = parse_num(row[16])  # 自營商(避險)
        dealer_net = parse_num(row[11])  # 自營商買賣超
        three_total = parse_num(row[17])  # 三大法人買賣超

        fund_data.append({
            'code': code,
            'name': name,
            'foreign': foreign_total,
            'trust': trust_net,
            'dealer': dealer_net,
            'total': three_total
        })

        fund_total['foreign'] += foreign_total
        fund_total['trust'] += trust_net
        fund_total['dealer'] += dealer_net
        fund_total['total'] += three_total

# Sort by three_total
fund_sorted_by_total = sorted(fund_data, key=lambda x: x['total'], reverse=True)
fund_top10_buy = fund_sorted_by_total[:10]
fund_top10_sell = fund_sorted_by_total[-10:]

# Also sort by foreign, trust, dealer
fund_sorted_foreign = sorted(fund_data, key=lambda x: x['foreign'], reverse=True)
fund_sorted_trust = sorted(fund_data, key=lambda x: x['trust'], reverse=True)
fund_sorted_dealer = sorted(fund_data, key=lambda x: x['dealer'], reverse=True)

# ========== 5. Read TWSE Stocks ==========
twse_stocks = []
with open(os.path.join(BASE, "raw_data/twse_stocks_20260520.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 17:
            continue
        code = row[0].strip()
        name = row[1].strip()
        shares = parse_num(row[2])
        txns = parse_num(row[3])
        value = parse_num(row[4])
        open_p = parse_float(row[5])
        high = parse_float(row[6])
        low = parse_float(row[7])
        close = parse_float(row[8])
        sign = row[9].strip()
        change = parse_float(row[10])
        pe = parse_float(row[16])
        market = row[17].strip() if len(row) > 17 else "上市"
        
        twse_stocks.append({
            'code': code, 'name': name, 'shares': shares, 'txns': txns,
            'value': value, 'open': open_p, 'high': high, 'low': low,
            'close': close, 'sign': sign, 'change': change, 'pe': pe,
            'market': market
        })

# ========== 6. Read TPEX Stocks ==========
tpex_stocks = []
with open(os.path.join(BASE, "raw_data/tpex_20260520.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 11:
            continue
        code = row[0].strip()
        name = row[1].strip()
        close = parse_float(row[2])
        change_str = row[3].strip()
        open_p = parse_float(row[4])
        high = parse_float(row[5])
        low = parse_float(row[6])
        shares = parse_num(row[7])
        value = parse_num(row[8])
        txns = parse_num(row[9])
        market = row[10].strip() if len(row) > 10 else "上櫃"
        
        # Parse change
        if change_str.startswith('+'):
            change = parse_float(change_str[1:])
            sign = '+'
        elif change_str.startswith('-') or change_str.startswith('－'):
            change = parse_float(change_str[1:])
            sign = '-'
        elif '除息' in change_str or '除權' in change_str:
            change = 0
            sign = ' '
        else:
            change = parse_float(change_str)
            sign = ' '
        
        tpex_stocks.append({
            'code': code, 'name': name, 'close': close, 'change': change,
            'sign': sign, 'open': open_p, 'high': high, 'low': low,
            'shares': shares, 'value': value, 'txns': txns, 'market': market
        })

# Combine all stocks
all_stocks = twse_stocks + tpex_stocks

# ========== 7. 漲停股票 ==========
# 漲停 = change equals ~10% of close (for general stocks) or closer to limit up
limit_up_stocks = []
for s in all_stocks:
    if s['close'] <= 0:
        continue
    pct = (s['change'] / s['close']) * 100 if s['close'] > 0 else 0
    if s['sign'] == '+' and pct >= 9.5:
        limit_up_stocks.append(s)

# Also check from updown: 漲停 154(上市) + 30(上櫃)
# Let's also identify from the data directly
limit_up_stocks_sorted = sorted(limit_up_stocks, key=lambda x: x['value'], reverse=True)

# ========== 8. 成交值排行 Top 10 ==========
# Only regular stocks (exclude ETFs, etc.)
regular_stocks = [s for s in all_stocks if not s['code'].startswith('0') or len(s['code']) == 4]
# Filter: exclude ETF-like codes (00xxxx)
value_ranked = sorted([s for s in all_stocks if s['value'] > 0], key=lambda x: x['value'], reverse=True)

# ========== 9. Read Daytrade Candidates ==========
daytrade_candidates = []
with open(os.path.join(BASE, "outputs/daytrade_candidates_ranked_20260520.csv"), "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 9:
            continue
        daytrade_candidates.append({
            'code': row[0].strip(),
            'name': row[1].strip(),
            'market': row[2].strip(),
            'close': parse_float(row[3]),
            'pct': parse_float(row[4]),
            'shares': parse_num(row[5]),
            'amplitude': parse_float(row[6]),
            'avg_price': parse_float(row[7]),
            'score': parse_float(row[8])
        })

# ========== 10. Read Margin Data ==========
with open(os.path.join(BASE, "raw_data/twse_margin_20260520.json"), "r") as f:
    margin = json.load(f)

margin_summary = margin['table_0']['data']
margin_financing_buy = parse_num(margin_summary[0][1])
margin_financing_sell = parse_num(margin_summary[0][2])
margin_financing_repay = parse_num(margin_summary[0][3])
margin_financing_prev = parse_num(margin_summary[0][4])
margin_financing_today = parse_num(margin_summary[0][5])

margin_short_buy = parse_num(margin_summary[1][1])
margin_short_sell = parse_num(margin_summary[1][2])
margin_short_repay = parse_num(margin_summary[1][3])
margin_short_prev = parse_num(margin_summary[1][4])
margin_short_today = parse_num(margin_summary[1][5])

margin_amount_buy = parse_num(margin_summary[2][1])
margin_amount_sell = parse_num(margin_summary[2][2])
margin_amount_repay = parse_num(margin_summary[2][3])
margin_amount_prev = parse_num(margin_summary[2][4])
margin_amount_today = parse_num(margin_summary[2][5])

# ========== Generate Report ==========
def fmt_num(n, prefix=''):
    """Format number with thousand separators."""
    if n == 0:
        return '0'
    sign = ''
    if n < 0:
        sign = '-'
        n = abs(n)
    if isinstance(n, float):
        return f"{sign}{n:,.2f}"
    return f"{sign}{n:,}"

def fmt_change(val, sign):
    if sign == '-':
        return f"-{val:,.2f}"
    elif sign == '+':
        return f"+{val:,.2f}"
    else:
        return f"{val:,.2f}"

# Build top value stocks (filter out ETF/TDR etc)
# Let's identify ETFs: codes starting with 00 and having more than 4 chars, or known ETF prefixes
def is_etf_like(code):
    if code.startswith('00') and len(code) >= 5:
        return True
    if code.endswith('L') or code.endswith('R') or code.endswith('U') or code.endswith('K'):
        return True
    if 'A' in code and code.startswith('00'):
        return True
    return False

real_stocks_value = sorted(
    [s for s in all_stocks if s['value'] > 0 and not is_etf_like(s['code'])],
    key=lambda x: x['value'], reverse=True
)

# Get top 10 limit up stocks
limit_up_display = limit_up_stocks_sorted[:30]

# ========== Compose Markdown Report ==========
report = f"""# 台股 2026/05/20 盤後分析報告

---

## 一、大盤指數與漲跌幅

| 指數名稱 | 收盤指數 | 漲跌 | 漲跌幅 |
|----------|---------|------|--------|
| 發行量加權股價指數 | {main_close:,.2f} | {fmt_change(main_change, main_sign)} | {fmt_change(main_pct, main_sign)}% |

- 加權指數收在 **{main_close:,.2f}** 點，{('上漲' if main_sign == '+' else '下跌')} **{abs(main_change):,.2f}** 點，跌幅 **{abs(main_pct):.2f}%**
- 臺灣50指數收在 36,980.73 點，下跌 226.22 點（-0.61%）
- 臺灣中型100指數收在 32,440.82 點，上漲 78.51 點（+0.24%）
- 小型股300指數收在 13,010.61 點，微漲 5.76 點（+0.04%）

---

## 二、市場統計

| 項目 | 成交金額（元） | 成交股數 | 成交筆數 |
|------|---------------|---------|---------|
| 一般股票 | {fmt_num(stock_value)} | {fmt_num(stock_shares)} | {fmt_num(stock_txns)} |
| **總計** | **{fmt_num(total_value)}** | **{fmt_num(total_shares)}** | **{fmt_num(total_txns)}** |

- 市場總成交金額 **{fmt_num(total_value)}** 元（約 {total_value/1e8:,.2f} 億元）
- 一般股票成交金額 {fmt_num(stock_value)} 元（約 {stock_value/1e8:,.2f} 億元）

---

## 三、漲跌家數

| 類別 | 上市 | 上櫃 |
|------|------|------|
| 上漲（漲停） | {up_twse:,}（{uplimit_twse}） | {up_tpex:,}（{uplimit_tpex}） |
| 下跌（跌停） | {down_twse:,}（{downlimit_twse}） | {down_tpex:,}（{downlimit_tpex}） |
| 持平 | {flat_twse:,} | {flat_tpex:,} |

- 上市上漲 {up_twse:,} 檔、下跌 {down_twse:,} 檔，下跌家數明顯多於上漲家數
- 上櫃上漲 {up_tpex:,} 檔、下跌 {down_tpex:,} 檔
- 上市漲停 {uplimit_twse} 檔、跌停 {downlimit_twse} 檔；上櫃漲停 {uplimit_tpex} 檔、跌停 {downlimit_tpex} 檔
- 整體市場 **偏空**，下跌家數約為上漲家數的 {down_twse/(up_twse+1):.1f} 倍

---

## 四、類股指數漲跌排行

### 類股前 5 強

| 排名 | 類股 | 收盤 | 漲跌 | 漲跌幅 |
|------|------|------|------|--------|
"""

for i, c in enumerate(top5_strong, 1):
    sign_str = '+' if c['pct'] > 0 else '-'
    report += f"| {i} | {c['name']} | {c['close']:,.2f} | {sign_str}{abs(c['change']):,.2f} | {sign_str}{abs(c['pct']):.2f}% |\n"

report += """
### 類股前 5 弱

| 排名 | 類股 | 收盤 | 漲跌 | 漲跌幅 |
|------|------|------|------|--------|
"""

for i, c in enumerate(reversed(top5_weak), 1):
    sign_str = '+' if c['pct'] > 0 else '-'
    report += f"| {i} | {c['name']} | {c['close']:,.2f} | {sign_str}{abs(c['change']):,.2f} | {sign_str}{abs(c['pct']):.2f}% |\n"

report += f"""
- **電子通路類**大漲 4.45% 領銜，航運類上漲 2.27%，紡織纖維類上漲 1.17%
- **光電類**下跌 2.02% 最弱，玻璃陶瓷類下跌 2.00%，通信網路類下跌 1.39%

---

## 五、三大法人買賣超

### 合計買賣超

| 法人別 | 買賣超（股） |
|--------|-------------|
| 外資（含外資自營商） | {fmt_num(fund_total['foreign'])} |
| 投信 | {fmt_num(fund_total['trust'])} |
| 自營商（含避險） | {fmt_num(fund_total['dealer'])} |
| **三大法人合計** | **{fmt_num(fund_total['total'])}** |

"""

total_dir = '買超' if fund_total['total'] > 0 else '賣超'
report += f"- 三大法人合計{total_dir} **{fmt_num(abs(fund_total['total']))}** 股\n"
foreign_dir = '買超' if fund_total['foreign'] > 0 else '賣超'
trust_dir = '買超' if fund_total['trust'] > 0 else '賣超'
dealer_dir = '買超' if fund_total['dealer'] > 0 else '賣超'
report += f"- 外資{foreign_dir} {fmt_num(abs(fund_total['foreign']))} 股、投信{trust_dir} {fmt_num(abs(fund_total['trust']))} 股、自營商{dealer_dir} {fmt_num(abs(fund_total['dealer']))} 股\n"

report += """
### 三大法人買超前 10 大個股

| 排名 | 代號 | 名稱 | 外資買賣超 | 投信買賣超 | 自營商買賣超 | 三大法人合計 |
|------|------|------|-----------|-----------|-------------|-------------|
"""

for i, d in enumerate(fund_top10_buy, 1):
    report += f"| {i} | {d['code']} | {d['name']} | {fmt_num(d['foreign'])} | {fmt_num(d['trust'])} | {fmt_num(d['dealer'])} | {fmt_num(d['total'])} |\n"

report += """
### 三大法人賣超前 10 大個股

| 排名 | 代號 | 名稱 | 外資買賣超 | 投信買賣超 | 自營商買賣超 | 三大法人合計 |
|------|------|------|-----------|-----------|-------------|-------------|
"""

for i, d in enumerate(reversed(fund_top10_sell), 1):
    report += f"| {i} | {d['code']} | {d['name']} | {fmt_num(d['foreign'])} | {fmt_num(d['trust'])} | {fmt_num(d['dealer'])} | {fmt_num(d['total'])} |\n"

# ========== 漲停股票列表 ==========
report += """
---

## 六、漲停股票列表

| 排名 | 代號 | 名稱 | 收盤價 | 成交值（元） |
|------|------|------|--------|-------------|
"""

for i, s in enumerate(limit_up_display, 1):
    report += f"| {i} | {s['code']} | {s['name']} | {s['close']:.2f} | {fmt_num(s['value'])} |\n"

report += f"""
- 今日漲停共 **{len(limit_up_stocks_sorted)}** 檔（上市 {uplimit_twse} 檔、上櫃 {uplimit_tpex} 檔）

---

## 七、成交值排行前 10

| 排名 | 代號 | 名稱 | 收盤價 | 漲跌 | 成交值（元） |
|------|------|------|--------|------|-------------|
"""

for i, s in enumerate(real_stocks_value[:10], 1):
    ch_sign = s.get('sign', ' ')
    ch_val = s.get('change', 0)
    report += f"| {i} | {s['code']} | {s['name']} | {s['close']:.2f} | {fmt_change(ch_val, ch_sign)} | {fmt_num(s['value'])} |\n"

# ========== 信用交易 ==========
report += f"""
---

## 八、信用交易概況

| 項目 | 買進 | 賣出 | 現金(券)償還 | 前日餘額 | 今日餘額 |
|------|------|------|-------------|---------|---------|
| 融資(交易單位) | {fmt_num(margin_financing_buy)} | {fmt_num(margin_financing_sell)} | {fmt_num(margin_financing_repay)} | {fmt_num(margin_financing_prev)} | {fmt_num(margin_financing_today)} |
| 融券(交易單位) | {fmt_num(margin_short_buy)} | {fmt_num(margin_short_sell)} | {fmt_num(margin_short_repay)} | {fmt_num(margin_short_prev)} | {fmt_num(margin_short_today)} |
| 融資金額(仟元) | {fmt_num(margin_amount_buy)} | {fmt_num(margin_amount_sell)} | {fmt_num(margin_amount_repay)} | {fmt_num(margin_amount_prev)} | {fmt_num(margin_amount_today)} |

- 融資餘額減少 {fmt_num(margin_financing_prev - margin_financing_today)} 張，融券餘額增加 {fmt_num(margin_short_today - margin_short_prev)} 張
- 融資金額今日餘額 {fmt_num(margin_amount_today)} 仟元（約 {margin_amount_today/1e6:,.2f} 億元）

---

## 九、盤勢總結

今日台股加權指數收在 **{main_close:,.2f}** 點，{('上漲' if main_sign == '+' else '下跌')} **{abs(main_change):,.2f}** 點（{fmt_change(main_pct, main_sign)}%），成交值約 {total_value/1e8:,.0f} 億元。

**盤面特徵：**

1. **大盤震盪走低**：加權指數下跌 154.74 點，跌幅 0.39%，權值股表現偏弱，臺灣50指數跌幅更大達 -0.61%。

2. **類股分化明顯**：電子通路類大漲 4.45% 一枝獨秀，航運類上漲 2.27%，紡織纖維類漲 1.17%；反之光電類大跌 2.02%、玻璃陶瓷類跌 2.00%、通信網路類跌 1.39%。電子工業類整體下跌 0.44%。

3. **下跌家數遠多於上漲**：上市上漲 {up_twse:,} 檔 vs 下跌 {down_twse:,} 檔，上櫃上漲 {up_tpex:,} 檔 vs 下跌 {down_tpex:,} 檔，整體市場賣壓較重。

4. **三大法人{total_dir}**：合計{total_dir} {fmt_num(abs(fund_total['total']))} 股，外資{foreign_dir} {fmt_num(abs(fund_total['foreign']))} 股為主力，投信{trust_dir} {fmt_num(abs(fund_total['trust']))} 股，自營商{dealer_dir} {fmt_num(abs(fund_total['dealer']))} 股。

5. **漲停股以中小型電子股為主**：今日漲停 {len(limit_up_stocks_sorted)} 檔，集中在被動元件、IC設計、光電等中小型股，顯示資金流向具題材性的中小型股。

6. **融資減少、融券增加**：融資餘額減少 {fmt_num(margin_financing_prev - margin_financing_today)} 張，融券增加 {fmt_num(margin_short_today - margin_short_prev)} 張，短線偏空氣氛濃厚。

**整體評估**：今日盤勢偏空，大型權值股走弱拖累指數，但中小型題材股仍有表現空間，市場呈現「指數弱、個股強」的格局。電子通路及航運類為盤面亮點，後續可留意相關族群延續性。

---

## 十、明日（2026/05/21）當沖標的建議

以下從當沖候選池中精選標的，依當沖評分排序：

| 排名 | 代號 | 名稱 | 收盤價 | 當沖評分 | 建議理由 |
|------|------|------|--------|---------|---------|
"""

# Pick top candidates with reasoning
top_candidates = daytrade_candidates[:10]
reasons = {
    '3580': '振幅達13.15%為全場最高，流動性佳(1萬張)，評分46.13居冠，適合當沖操作',
    '4916': '三大法人買超逾507萬股，漲停鎖住強勢，振幅11.86%，評分44.05',
    '5321': '漲停鎖住，振幅12.29%，評分43.04，小型股爆發力強',
    '6174': '資安題材股漲停，振幅11.27%，評分42.08，題材續航力佳',
    '8064': '跌停打開振幅11.31%，評分42.01，空方力道釋放後可能反彈',
    '6175': '漲停鎖住，振幅11.07%，評分41.85，半導體通路題材',
    '2484': '石英元件題材，漲停鎖住，振幅10.67%，評分41.48，量能充足(2.3萬張)',
    '8121': '漲停鎖住，振幅11.09%，評分41.46，被動元件族群強勢',
    '6127': '被動元件漲停，振幅10.43%，評分40.88，成交2.6萬張流動性佳',
    '1533': '車用電子題材，漲停鎖住，振幅10.71%，評分40.47',
}

for i, c in enumerate(top_candidates, 1):
    reason = reasons.get(c['code'], f"振幅{c['amplitude']:.1f}%，評分{c['score']:.1f}，流動性充足")
    report += f"| {i} | {c['code']} | {c['name']} | {c['close']:.1f} | {c['score']:.2f} | {reason} |\n"

report += """
### 當沖選股邏輯說明

1. **振幅優先**：振幅越大，當沖獲利空間越大，優先選擇振幅 > 9% 的標的
2. **流動性篩選**：成交張數需達一定規模，避免流動性不足導致滑價過大
3. **法人動能**：三大法人買超個股具續航力，賣超個股則留意反彈空間
4. **漲停鎖住股**：漲停鎖住代表強勢，次日開高機率高，但需注意追高風險
5. **跌停打開股**：跌停打開表示賣壓釋放，次日可能有反彈行情

### 風險提醒

- 當沖操作風險較高，需嚴格設停損點
- 漲停股次日可能開高走低，追高需謹慎
- 大盤偏空環境下，當沖以短打為主，不宜留倉
- 以上建議僅供參考，投資人應審慎評估自身風險承受度

---

*報告產出時間：2026/05/20 盤後*
*資料來源：臺灣證券交易所、櫃買中心*
"""

# Write report
os.makedirs(os.path.join(BASE, "reports"), exist_ok=True)
output_path = os.path.join(BASE, "reports/twse_20260520_analysis.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(report)

print(f"Report written to: {output_path}")
print(f"Report length: {len(report)} characters")
