# TWSE API 結構變更記錄

## MI_INDEX 端點 (上市每日收盤行情)

**舊結構（已失效）：**
- 回應包含 `stat`, `fields9`, `data9` 頂層欄位
- `data9` 直接是所有個股收盤行情

**新結構（2025年起）：**
- 回應包含 `tables` 陣列，每個元素有 `title`, `fields`, `data`
- `tables[0]`: 上市價格指數（56 rows）— 各類股指數
- `tables[1]`: 跨市場指數（48 rows）
- `tables[2]`: 臺灣指數公司指數（34 rows）
- `tables[3]`: 報酬指數（47 rows）
- `tables[4]`: 跨市場報酬指數（49 rows）
- `tables[5]`: 臺灣指數公司報酬指數（33 rows）
- `tables[6]`: 大盤統計資訊（17 rows）— 成交金額/股數/筆數
- `tables[7]`: 漲跌證券數合計（5 rows）— 上漲/下跌/持平家數
- `tables[8]`: **每日收盤行情（全部）**（~1360 rows）— 這就是原本的 `data9`
  - Fields: `['證券代號', '證券名稱', '成交股數', '成交筆數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌(+/-)', '漲跌價差', '最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量', '本益比']`
- `tables[9]`: 空表

## JSON 解析注意事項

1. **HTML 標籤嵌入**：`漲跌(+/-)` 欄位值為 `<p style='color:green'>-</p>` 或 `<p style='color:red'>+</p>`，需先去除 HTML 標籤
2. **控制字元**：回應中可能含有 `\x00-\x1f` 控制字元，需先清理
3. **清理步驟**：
   ```python
   raw_clean = re.sub(r'<[^>]+>', '', raw)  # 去 HTML
   raw_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_clean)  # 去控制字元
   data = json.loads(raw_clean)
   ```

## 三大法人買賣超 (T86)

- 端點：`https://www.twse.com.tw/fund/T86?response=json&date=YYYYMMDD&selectType=ALLBUT0999`
- 回傳結構：`stat`, `fields`, `data`（非 tables）
- 欄位：證券代號, 證券名稱, 外陸資買進, 外陸資賣出, 外陸資買賣超, 外資自營商買進, 外資自營商賣出, 外資自營商買賣超, 投信買進, 投信賣出, 投信買賣超, 自營商買賣超, 自營商買進(自行), 自營商賣出(自行), 自營商買賣超(自行), 自營商買進(避險), 自營商賣出(避險), 自營商買賣超(避險), 三大法人買賣超
- 同樣有 HTML 標籤問題需清理

## 信用交易統計 (MI_MARGN)

- 端點：`https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date=YYYYMMDD&selectType=ALL`
- 回傳結構：`tables` 陣列
- `tables[0]`: 信用交易統計（融資/融券彙總）
- `tables[1]`: 融資融券彙總（個股）

## 上櫃 (TPEx)

- 端點：`https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d=YYY/MM/DD&se=EW&s=0,asc,0`
- 日期格式：民國年（如 115/05/19）
- 回傳結構：`tables[0]` 含 `fields` 和 `data`
- 注意：欄位名稱可能有 trailing space（如 `'收盤 '`, `'開盤 '`）

## BWIBBU_d (個股本益比/殖利率/淨值比)

- 端點：`https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=json&date=YYYYMMDD&selectType=ALL`
- 回傳結構：`stat`, `fields`, `data`（非 tables）
- 欄位：證券代號, 證券名稱, 收盤價, 殖利率(%), 股利年度, 本益比, 股價淨值比, 財報年/季
