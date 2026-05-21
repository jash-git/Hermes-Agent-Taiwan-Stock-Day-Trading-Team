# 三大法人資料延遲處理

## 問題描述

TWSE T86（三大法人買賣超）和 MI_MARGN（信用交易）API 在收盤當天通常**不會立即上架**。

API 回傳：
```json
{"stat": "很抱歉，沒有符合條件的資料!", "total": 0}
```

## 處理策略

1. **先嘗試抓取當天資料**
2. **若回傳「沒有符合條件的資料」**：
   - 在報告中標註「三大法人資料尚未公布（資料日期：YYYY-MM-DD）」
   - 自動退回前一個交易日抓取法人資料
   - 在報告中以前日法人資料作為參考，並加註說明
3. **若當天有資料**：正常使用
## 實作範例

```python
import csv, json, re
import requests

def fetch_fund_data(date_str):
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALLBUT0999"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=15)

    raw = re.sub(r'<[^>]+>', '', response.text)
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)
    data = json.loads(raw)

    if data.get('stat') != 'OK' or not data.get('data'):
        return None  # 資料尚未公布

    return data

# 使用方式
fund = fetch_fund_data('20260520')
if fund is None:
    print("三大法人資料尚未公布，使用前日資料...")
    fund = fetch_fund_data('20260519')  # fallback
```

## CSV 解析注意事項

T86 CSV 的數字欄位包含千分位逗號且被雙引號包裹（如 `"12,870"`）。

**必須使用 `csv.reader` 解析，不可手動 `split(',')`。**

詳見：`references/csv-parsing-gotchas.md`

## 時間參考

- 15:00 收盤
- 15:30~16:00 個股行情陸續上架（MI_INDEX）
- 16:00~17:00 三大法人資料可能上架（T86、MI_MARGN）
- 建議在 16:30 後執行分析，以取得最完整資料
