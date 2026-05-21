
import pandas as pd
import csv

df = pd.read_csv('raw_data/twse_stocks_20260520.csv', encoding='utf-8-sig')
for c in df.columns:
    df[c] = df[c].astype(str).str.replace(',','').str.strip()

df['成交金額'] = pd.to_numeric(df['成交金額'], errors='coerce')
df['收盤價'] = pd.to_numeric(df['收盤價'], errors='coerce')
df['漲跌價差'] = pd.to_numeric(df['漲跌價差'], errors='coerce')

sign_col = '漲跌(+/-)'
# sign: '+' means up, '-' means down, blank means flat
df['signed_chg_val'] = df.apply(lambda r: 
    r['漲跌價差'] if r[sign_col] == '+' else 
    (-r['漲跌價差'] if r[sign_col] == '-' else 0), axis=1)

df['prev_close'] = df['收盤價'] - df['signed_chg_val']
df['chg_pct'] = (df['signed_chg_val'] / df['prev_close'] * 100).round(2)

# Filter only regular stocks (4-digit codes)
stocks_only = df[df['證券代號'].str.match(r'^\d{4}[A-Z]?$')]

# Limit UP stocks (漲停)
limit_up = stocks_only[stocks_only['chg_pct'] >= 9.5].sort_values('chg_pct', ascending=False)
print(f'=== LIMIT UP STOCKS ({len(limit_up)} stocks) ===')
for _, r in limit_up.head(15).iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} close={r['收盤價']} chg=+{r["chg_pct"]}%")

# Limit DOWN stocks (跌停)
limit_down = stocks_only[stocks_only['chg_pct'] <= -9.5].sort_values('chg_pct')
print(f'\n=== LIMIT DOWN STOCKS ({len(limit_down)} stocks) ===')
for _, r in limit_down.head(15).iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} close={r['收盤價']} chg={r['chg_pct']}%")

# Top losers (excluding limit down)
print('\n=== TOP LOSERS (個股) ===')
for _, r in stocks_only[stocks_only['chg_pct'] < -5].nsmallest(15, 'chg_pct').iterrows():
    print(f"{r['證券代號']} {r['證券名稱']} close={r['收盤價']} chg={r['chg_pct']}%")

# Fund totals
print('\n=== FUND TOTALS ===')
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
            print(f'三大法人合計買賣超: {t:,} 股')
            print(f'外資及陸資: {fr:,} 股')
            print(f'投信: {iv:,} 股')
            print(f'自營商: {dl:,} 股')
            break
