---
name: twse-free-daily
description: 台股每日盤後分析 — 抓取上市/上櫃收盤行情、三大法人買賣超、信用交易、類股指數，產出結構化市場資料與當沖候選池。
---

# SKILL: twse-free-daily

## 使命 (Mission)
以完全免費、公開可取得的資料來源，抓取台灣證券交易所 (TWSE) 最近一個交易日的完整收盤交易資訊，並產出適合當日沖銷 (Day Trading) 篩選的結構化市場資料。

## 職責範圍 (Responsibilities)
- 每日自動或手動觸發後，抓取前一日台股完整交易資料
- 支援個股基本資訊、成交量、漲跌幅、成交值、振幅、均價等核心欄位
- 產出標準化的市場資料（JSON / CSV / DataFrame）
- 提供當沖候選池初步排序與統計指標

## ⚠️ 執行流程（強制，不可跳過）

此任務**必須**按照以下標準流程執行，不得自行省略任何步驟：

### Phase 1：資料抓取（子 agent A）

**必須使用 `delegate_task` 啟動子 agent 執行**，不得由主 agent 自行抓取。

子 agent 任務：
1. 安裝依賴：`pip install pandas requests -q --break-system-packages`
2. 執行腳本：`cd {SKILL_DIR} && python3 scripts/fetch_twse_daily.py YYYYMMDD`
3. 確認 `{SKILL_DIR}/raw_data/` 目錄下所有輸出檔案（注意：腳本輸出到 skill 根目錄的 `raw_data/`，不是 `scripts/raw_data/`）
4. 回報各檔案大小與資料筆數

**⚠️ Phase 1 子 agent 失敗處理（2026-05-21 經驗）**：
子 agent A 可能因 API 錯誤（`max_iterations` / Provider returned error）而失敗。
若 Phase 1 子 agent 失敗，**主 agent 應降級自行執行**：
1. `pip install pandas requests -q --break-system-packages`
2. `cd {SKILL_DIR} && python3 scripts/fetch_twse_daily.py YYYYMMDD`
3. 確認 `{SKILL_DIR}/raw_data/` 下有 6 個 YYYYMMDD 檔案（可能缺少 twse_margin）
4. 繼續啟動 Phase 2 子 agent

降級時不需要再啟動新的子 agent 做 Phase 1，直接用 terminal 執行即可。

### Phase 2：資料清洗與排序（子 agent B）

**必須使用 `delegate_task` 啟動子 agent 執行**，與 Phase 1 平行或接續。

子 agent 任務：
1. 安裝依賴：`pip install pandas numpy -q --break-system-packages`
2. 執行資料清洗：`python3 tools/normalize_market_data.py YYYYMMDD`
3. 執行當沖排序：`python3 tools/rank_intraday_candidates.py YYYYMMDD`
4. 回報標準化資料總筆數、當沖候選池前 20 名

**⚠️ Phase 2 子 agent 失敗處理（2026-05-21 經驗）**：
子 agent B 可能因 API 錯誤（`max_iterations` / Provider returned error）而失敗，即使 fetcher 已成功。
若 Phase 2 子 agent 失敗，**主 agent 應降級自行執行**：
1. `pip install pandas numpy -q --break-system-packages`
2. `python3 tools/normalize_market_data.py YYYYMMDD`（預期輸出：`資料清洗完成！總計處理 N 檔股票。`）
3. `python3 tools/rank_intraday_candidates.py YYYYMMDD`（預期輸出：前 10 名列表 + 完整 50 檔 CSV）
4. 繼續執行 Phase 2.5（extract_report_data.py）

降級時不需要再啟動新的子 agent，直接用 terminal 執行即可。

### Phase 2.5：報告資料萃取（子 agent B 接續執行）

**在 Phase 2 完成後，由同一子 agent 接續執行**，不需另啟新 agent。

子 agent 任務：
1. 執行萃取腳本：`python3 tools/extract_report_data.py YYYYMMDD`
2. 確認 `outputs/report_summary_YYYYMMDD.json` 已產出（約 20KB）
3. 回報檔案大小與關鍵數據摘要

此步驟產出的精簡 JSON（~20KB）取代了 dt_writer 原本需要讀取的 7 個原始檔案（合計 700KB+），是解決 Phase 3 超時的關鍵。

### Phase 3：撰寫報告（子 agent C — dt_writer）

**必須使用 `delegate_task` 啟動子 agent 執行**，不得由主 agent 自行撰寫報告。

子 agent 任務：
1. 安裝依賴：`pip install -q --break-system-packages`（無額外依賴，此步可跳過）
2. 讀取 `{SKILL_DIR}/outputs/report_summary_YYYYMMDD.json`（精簡報告摘要，唯一需要的資料檔）
3. 根據摘要資料撰寫完整盤後分析報告（Markdown 格式），存至 `{SKILL_DIR}/reports/twse_YYYYMMDD_analysis.md`
4. 報告必須包含：大盤指數、市場統計、漲跌家數、類股指數、三大法人、漲停股票、成交值排行、盤勢總結、明日當沖標的建議
5. 回報報告完整內容

**重要**：dt_writer 不需要讀取 raw_data/ 下的任何原始檔案，所有資料已在 report_summary JSON 中。這是解決 Phase 3 超時的核心設計。

**⚠️ 路徑注意**：報告必須寫入 `{SKILL_DIR}/reports/twse_YYYYMMDD_analysis.md`（skill 目錄下的 reports/），不是 `/home/vblinux/reports/`。dt_writer 子 agent 可能因工作目錄不同而寫錯路徑，請在任務描述中明確指定完整路徑。

**Phase 3 超時現狀（2026-05-21 更新）**：
得益於 Phase 2.5 的 extract_report_data.py（將 700KB+ 原始資料萃取為 ~20KB 精簡 JSON），dt_writer 只需讀取單一精簡檔案，context 大幅減少。實測 dt_writer 可在 ~370s 內完成（低於 600s 門檻）。**目前不需要預先降級**，但若未來再次超時，再啟用降級策略。

### Phase 4：主 Agent 彙總交付（Orchestrator）

1. 驗收 dt_writer 子 agent 產出的報告
2. 確認 `{SKILL_DIR}/reports/twse_YYYYMMDD_analysis.md` 已寫入
3. 將報告重點摘要交付給使用者

## 可用工具 (Tools)
- `scripts/fetch_twse_daily.py`：**修正版腳本，唯一使用的抓取工具**。抓取 TWSE MI_INDEX（上市個股收盤、指數、統計、漲跌家數）、T86（三大法人）、MI_MARGN（信用交易）、TPEx（上櫃）。
- `tools/fetch_twse_daily.py`：舊版腳本（使用已失效的 data9 結構，**勿用**）
- `tools/normalize_market_data.py`：資料清洗、欄位統一、計算技術指標（振幅%、量比、漲幅等）
- `tools/rank_intraday_candidates.py`：根據當沖偏好進行初步排序（振幅×2 + |漲跌幅|×1.5 + log10(成交量)×1.2）
- `tools/extract_report_data.py`：**報告資料萃取**。從 raw_data/ 讀取所有原始檔案，萃取為精簡的 report_summary JSON（~17KB），供 dt_writer 使用。解決 dt_writer 讀取大量原始檔案導致超時的問題。

## API 結構說明（重要）
TWSE API 已從舊版 `data9` 結構改為 `tables` 陣列結構。詳細說明見：
`references/twse-api-changes.md`

重點摘錄：
- `tables[8]` = 每日收盤行情（全部個股）— 對應舊版 `data9`
- `tables[6]` = 大盤統計資訊（成交金額/股數/筆數）
- `tables[7]` = 漲跌證券數合計
- `tables[0]` = 上市類股指數
- 三大法人 (T86) 仍用 `data` 結構（非 tables）
- TPEx 上櫃也用 `tables[0]` 結構（非舊版 `aaData`）

## TWSE 上市個股 CSV 欄位解析（關鍵）
`raw_data/twse_stocks_YYYYMMDD.csv` 的欄位中**沒有「漲跌幅」欄位**，只有：
- `漲跌(+/-)`：符號欄位（'+' = 上漲，'-' = 下跌，空 = 平盤）
- `漲跌價差`：絕對漲跌金額（永遠為正數）

計算漲跌幅的正確方式：
```python
sign = row['漲跌(+/-)']
signed_chg = row['漲跌價差'] if sign == '+' else (-row['漲跌價差'] if sign == '-' else 0)
prev_close = row['收盤價'] - signed_chg
chg_pct = (signed_chg / prev_close) * 100
```

常見錯誤：直接把 `漲跌價差` 當作帶符號的漲跌幅，會導致所有個股都顯示上漲（跌的也變漲）。

三大法人 CSV（`twse_fund_YYYYMMDD.csv`）**沒有「合計」列**，需自行加總所有個股的買賣超欄位。

詳細欄位解析與陷阱見：`references/twse-stocks-csv-parsing.md`

## JSON 解析注意事項（關鍵）
TWSE API 回應中**嵌入 HTML 標籤**（如 `<p style='color:green'>-</p>`）和**控制字元**，
直接 `response.json()` 會失敗。必須先清理：

```python
import re, json
raw = re.sub(r'<[^>]+>', '', response.text)           # 去 HTML 標籤
raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)  # 去控制字元
data = json.loads(raw)
```

TPEx 欄位名稱可能有 trailing space（如 `'收盤 '`），清理時需 `.strip()`。

## CSV 解析注意事項（關鍵）
T86 三大法人 CSV 的數字欄位可能包含千分位逗號且被雙引號包裹（如 `"92,077"`），
使用 `csv.reader` 而非手動 `split(',')` 解析。詳見：
`references/csv-parsing-gotchas.md`

## 三大法人資料延遲
T86 和 MI_MARGN 在收盤當天可能尚未上架。處理策略見：
`references/fund-data-delay.md`

## 分工策略
多資料源必須平行處理。詳細分工架構見：
`references/delegation-strategy.md`

## 輸入 (Input)
- 目標日期（預設為前一個交易日）
- 可選參數：市場別（上市/上櫃）、排除類股、價格區間等

## 輸出 (Output)
- `raw_data/twse_stocks_YYYYMMDD.csv` — 上市個股收盤
- `raw_data/twse_market_stats_YYYYMMDD.json` — 大盤統計
- `raw_data/twse_updown_YYYYMMDD.json` — 漲跌家數
- `raw_data/twse_indices_YYYYMMDD.json` — 類股指數
- `raw_data/twse_fund_YYYYMMDD.csv` — 三大法人買賣超
- `raw_data/twse_margin_YYYYMMDD.json` — 信用交易
- `raw_data/tpex_YYYYMMDD.csv` — 上櫃個股收盤
- `processed_data/market_data_normalized_YYYYMMDD.json` / `.csv`
- `outputs/daytrade_candidates_ranked_YYYYMMDD.csv`（含排名分數）
- `outputs/report_summary_YYYYMMDD.json`（精簡報告摘要，~17KB，供 dt_writer 使用）
- `reports/twse_YYYYMMDD_analysis.md` — 完整分析報告

## 關鍵原則
- 僅使用公開免費來源（TWSE、TPEx 公開資料、證交所 API）
- 資料必須有時間戳記與來源記錄
- 確保可重現性（同一日期輸入應產出相同結果）
- 處理假日、休市、早盤等特殊情況
- **若當天資料尚未上架（通常 16:00 後），自動退回前一個交易日**
- **必須使用 delegate_task 平行處理，不得由主 agent 自行抓取資料**

## 成功指標
- 每日 16:00 後可穩定抓取前日完整資料
- 資料完整率 > 99%
- 當沖候選池產出時間 < 3 分鐘

## 已知問題與限制
- `tools/` 目錄下的舊版腳本使用已失效的 `data9` API，勿直接使用
- `scripts/fetch_twse_daily.py` 為修正版，使用新版 `tables` 結構
- 若 TWSE 再次改版，檢查 `tables` 索引號是否偏移
- TPEx 日期格式為民國年（YYYY-1911/MM/DD）
- 三大法人 (T86) 當天資料可能延遲，需有 fallback 機制
- T86 CSV 數字欄位含千分位逗號，必須用 `csv.reader` 解析（非手動 split）
- TPEx CSV 可能缺少 `均價` 欄位，normalize 腳本已處理（以 成交金額/成交股數 計算）
- normalize 腳本讀取的上市檔案名稱為 `raw_data/twse_stocks_{date}.csv`（非 `twse_{date}.csv`）
- 上市個股 CSV 無「漲跌幅」欄位，需從 `漲跌(+/-)` + `漲跌價差` 計算（見 `references/twse-stocks-csv-parsing.md`）
- 三大法人 CSV 無「合計」列，需自行加總（見 `references/twse-stocks-csv-parsing.md`）
- Phase 3 dt_writer 子 agent 常超時（600s），主 agent 應降級為自行撰寫報告（見 `references/delegation-strategy.md` 超時處理段）
- Phase 2 processor 子 agent 可能因 API 錯誤（max_iterations）失敗，主 agent 應降級為直接用 terminal 執行三個腳本（見 `references/delegation-strategy.md` Phase 2 失敗處理段）
