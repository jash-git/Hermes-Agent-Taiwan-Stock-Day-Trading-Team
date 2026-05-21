# TWSE 上市個股 CSV 欄位解析與陷阱

## CSV 完整欄位

`raw_data/twse_stocks_YYYYMMDD.csv` 欄位（含 BOM）：

```
證券代號,證券名稱,成交股數,成交筆數,成交金額,開盤價,最高價,最低價,收盤盤價,漲跌(+/-),漲跌價差,最後揭示買價,最後揭示買量,最後揭示賣價,最後揭示賣量,本益比,市場
```

**注意：沒有「漲跌幅」欄位**，必須自行計算。

## 漲跌幅計算（最容易出錯的地方）

### 錯誤做法 ❌
```python
# 錯誤：直接用漲跌價差當帶符號值
chg_pct = df['漲跌價差'] / (df['收盤價'] - df['漲跌價差']) * 100
# 結果：所有個股都顯示正數，下跌股變成上漲
```

### 正確做法 ✅
```python
sign_col = '漲跌(+/-)'
df['signed_chg'] = df.apply(
    lambda r: r['漲跌價差'] if r[sign_col] == '+' 
    else (-r['漲跌價差'] if r[sign_col] == '-' else 0), 
    axis=1
)
df['prev_close'] = df['收盤價'] - df['signed_chg']
df['chg_pct'] = (df['signed_chg'] / df['prev_close'] * 100).round(2)
```

## 數字欄位含千分位逗號

成交股數、成交筆數、成交金額等欄位以千分位逗號格式化且被雙引號包裹：
```
"35,958,875","7,535","458,982,455"
```

解析方式：
```python
for c in df.columns:
    df[c] = df[c].astype(str).str.replace(',','').str.strip()
df['成交金額'] = pd.to_numeric(df['成交金額'], errors='coerce')
df['收盤價'] = pd.to_numeric(df['收盤價'], errors='coerce')
df['漲跌價差'] = pd.to_numeric(df['漲跌價差'], errors='coerce')
```

## 篩選一般個股

CSV 中包含 ETF（代號以 00 開頭）、DR（代號 91xx）、特別股等，篩選一般股票：
```python
stocks_only = df[df['證券代號'].str.match(r'^\d{4}[A-Z]?$')]
```

## 三大法人 CSV 無合計列

`twse_fund_YYYYMMDD.csv` 沒有「合計」行，必須自行加總：
```python
total_3 = sum(int(row[total_idx].replace(',','')) for row in reader)
total_foreign = sum(int(row[foreign_idx].replace(',','')) for row in reader)
```

## 實際案例（2026-05-20）

| 欄位 | 範例值 | 說明 |
|------|--------|------|
| 證券代號 | 0050 | ETF 代號以 00 開頭 |
| 成交股數 | "121,650,308" | 千分位+引號 |
| 漲跌(+/-) | - | 下跌符號 |
| 漲跌價差 | 0.60 | 永遠為正 |
| 收盤價 | 92.50 | 當日收盤 |

計算：prev_close = 92.50 - (-0.60) = 93.10，chg_pct = -0.60/93.10 = -0.644%
