
import pandas as pd
import csv
import sys

# TWSE stocks analysis
df = pd.read_csv('raw_data/twse_stocks_20260520.csv', encoding='utf-8-sig')
for c in df.columns:
    df[c] = df[c].astype(str).str.replace(',','').str.strip()

df['成交金額'] = pd.to_numeric(df['成交金額'], errors='coerce')
df['收盤價'] = pd.to_numeric(df['收盤價'], errors='coerce')
df['漲跌價差'] = pd.to_numeric(df['漲跌價差'], errors='coerce')

# Top 10 by turnover
print("=== 成交值排行 TOP10 ===")
top = df.nlargest(10, '成交金額')
for _, r in top.iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} 收盤{r['收盤價']} 漲跌{r['漲跌價差']} 成交值{r['成交金額']/1e8:.1f}億")

# Stocks near limit up (漲跌幅 > 9.5%)
# We need to calculate from 漲跌價差 and previous close
# 漲跌幅 = 漲跌價差 / (收盤價 - 漲跌價差) * 100
df['prev_close'] = df['收盤價'] - df['漲跌價差']
df['chg_pct'] = (df['漲跌價差'] / df['prev_close'] * 100).round(2)

limit_up = df[df['chg_pct'] >= 9.5].sort_values('chg_pct', ascending=False)
print(f"\n=== 漲停股 ({len(limit_up)} 檔) ===")
for _, r in limit_up.iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} 收盤{r['收盤價']} 漲幅{r['chg_pct']}%")

# Top gainers
print("\n=== 漲幅 TOP10 ===")
for _, r in df.nlargest(10, 'chg_pct').iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} 收盤{r['收盤價']} 漲幅{r['chg_pct']}%")

# Top losers
print("\n=== 跌幅 TOP10 ===")
for _, r in df.nsmallest(10, 'chg_pct').iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} 收盤{r['收盤價']} 跌幅{r['chg_pct']}%")

# Three major investors
print("\n=== 三大法人買超 TOP10 ===")
with open('raw_data/twse_fund_20260520.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    code_idx = header.index('證券代號')
    name_idx = header.index('證券名稱')
    foreign_idx = header.index('外陸資買賣超股數(不含外資自營商)')
    invest_idx = header.index('投信買賣超股數')
    total_idx = header.index('三大法人買賣超股數')
    
    rows = []
    for row in reader:
        if len(row) < len(header) or row[code_idx] == '合計':
            try:
                if row[code_idx] == '合計':
                    f_total = int(row[foreign_idx].replace(',',''))
                    i_total = int(row[invest_idx].replace(',',''))
                    t_total = int(row[total_idx].replace(',',''))
                    print(f"合計: 三大法人{t_total:,} 外資{f_total:,} 投信{i_total:,}")
            except:
                pass
            continue
        try:
            net = int(row[total_idx].replace(',',''))
            rows.append((row[code_idx], row[name_idx].strip(), net,
                        int(row[foreign_idx].replace(',','')),
                        int(row[invest_idx].replace(',',''))))
        except:
            continue

rows.sort(key=lambda x: x[2], reverse=True)
for r in rows[:10]:
    print(f"{r[0]} {r[1]} 三大{r[2]:+,} 外資{r[3]:+,} 投信{r[4]:+,}")

print("\n=== 三大法人賣超 TOP10 ===")
rows.sort(key=lambda x: x[2])
for r in rows[:10]:
    print(f"{r[0]} {r[1]} 三大{r[2]:+,} 外資{r[3]:+,} 投信{r[4]:+,}")
