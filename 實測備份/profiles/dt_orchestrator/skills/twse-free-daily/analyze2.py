
import pandas as pd
import csv

df = pd.read_csv('raw_data/twse_stocks_20260520.csv', encoding='utf-8-sig')
for c in df.columns:
    df[c] = df[c].astype(str).str.replace(',','').str.strip()

df['成交金額'] = pd.to_numeric(df['成交金額'], errors='coerce')
df['收盤價'] = pd.to_numeric(df['收盤價'], errors='coerce')
df['漲跌價差'] = pd.to_numeric(df['漲跌價差'], errors='coerce')
df['prev_close'] = df['收盤價'] - df['漲跌價差']
df['chg_pct'] = (df['漲跌價差'] / df['prev_close'] * 100).round(2)

stocks_only = df[~df['證券代號'].str.startswith('00')]
print('=== STOCK LOSERS TOP10 ===')
for _, r in stocks_only.nsmallest(10, 'chg_pct').iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} close={r['收盤價']} chg={r['chg_pct']}%")

print()
with open('raw_data/twse_fund_20260520.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) >= len(header) and '合計' in str(row[0]):
            total_idx = header.index('三大法人買賣超股數')
            foreign_idx = header.index('外陸資買賣超股數(不含外資自營商)')
            invest_idx = header.index('投信買賣超股數')
            dealer_idx = header.index('自營商買賣超股數')
            t = int(row[total_idx].replace(',',''))
            fr = int(row[foreign_idx].replace(',',''))
            iv = int(row[invest_idx].replace(',',''))
            dl = int(row[dealer_idx].replace(',',''))
            print(f'TOTAL3: {t:,}')
            print(f'FOREIGN: {fr:,}')
            print(f'INVEST: {iv:,}')
            print(f'DEALER: {dl:,}')
            break
