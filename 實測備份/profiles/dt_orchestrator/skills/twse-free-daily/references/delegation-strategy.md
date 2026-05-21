# 分工策略：delegate_task 平行處理

## 原則

台股盤後分析涉及多個**獨立資料源**，必須使用 `delegate_task` 平行處理以加速完成。

**重要：主 agent 不得自行抓取資料或撰寫報告。** 所有資料抓取、處理和報告撰寫都必須委派給子 agent。主 agent 僅負責派工與驗收。

## 分工架構（4-step，4 角色）

```
主 Agent (Orchestrator)
  ├── delegate_task → 子 Agent A (fetcher): 資料抓取
  │   └── scripts/fetch_twse_daily.py → raw_data/
  ├── delegate_task → 子 Agent B (processor): 資料處理 + 萃取
  │   ├── tools/normalize_market_data.py → processed_data/
  │   ├── tools/rank_intraday_candidates.py → outputs/
  │   └── tools/extract_report_data.py → outputs/report_summary_YYYYMMDD.json
  ├── delegate_task → 子 Agent C (dt_writer): 撰寫報告
  │   └── 讀取 outputs/report_summary_YYYYMMDD.json → reports/twse_YYYYMMDD_analysis.md
  └── 主 Agent: 驗收報告 + 交付使用者
```

此為 4-step 分工：
- Stage 1：fetcher 獨立抓取所有資料源（TWSE + TPEx + T86 + MI_MARGN）
- Stage 2：processor 依賴 fetcher 產出，清洗排序後產生當沖候選池
- Stage 2.5：processor 接續執行 extract_report_data.py，將所有 raw_data 萃取為精簡 JSON（~17KB vs 原始 700KB+）
- Stage 3：dt_writer **只需讀取 report_summary JSON**，撰寫完整報告
- 主 agent 僅做 orchestrator：派工、等待、驗收、交付

## 各子 Agent 任務規格

### 子 Agent A — 資料抓取 (fetcher)

**輸入**：目標日期（YYYYMMDD）
**任務**：
1. 安裝依賴：`pip install pandas requests -q --break-system-packages`
2. 執行腳本：`cd {SKILL_DIR} && python3 scripts/fetch_twse_daily.py YYYYMMDD`
3. 確認 `raw_data/` 目錄下所有輸出檔案
4. 回報各檔案大小與資料筆數

**輸出**：
- `raw_data/twse_stocks_YYYYMMDD.csv`（上市個股，~1,360 筆）
- `raw_data/twse_market_stats_YYYYMMDD.json`（大盤統計）
- `raw_data/twse_updown_YYYYMMDD.json`（漲跌家數）
- `raw_data/twse_indices_YYYYMMDD.json`（類股指數）
- `raw_data/twse_fund_YYYYMMDD.csv`（三大法人，可能無）
- `raw_data/twse_margin_YYYYMMDD.json`（信用交易，可能無）
- `raw_data/tpex_YYYYMMDD.csv`（上櫃個股，~1,000 筆）

**⚠️ Phase 1 子 agent 失敗處理（2026-05-21 新發現）**：
子 agent A（fetcher）可能因 API 錯誤（`max_iterations` / Provider returned error）而失敗。這與 Phase 2 失敗類似，是 API 層面的間歇性錯誤。

**降級流程**：
1. 主 agent 直接用 `terminal` 執行（不需要再啟動子 agent）：
   ```
   pip install pandas requests -q --break-system-packages
   cd {SKILL_DIR} && python3 scripts/fetch_twse_daily.py YYYYMMDD
   ```
2. 確認 `{SKILL_DIR}/raw_data/` 下有 YYYYMMDD 檔案（通常 6 個，可能缺少 twse_margin）
3. 繼續啟動 Phase 2 子 agent

### 子 Agent B — 資料處理 + 萃取 (processor)

**輸入**：目標日期（YYYYMMDD）
**任務**：
1. 安裝依賴：`pip install pandas numpy -q --break-system-packages`
2. 執行資料清洗：`python3 tools/normalize_market_data.py YYYYMMDD`
3. 執行當沖排序：`python3 tools/rank_intraday_candidates.py YYYYMMDD`
4. 執行報告資料萃取：`python3 tools/extract_report_data.py YYYYMMDD`
5. 回報標準化資料總筆數、當沖候選池前 20 名、report_summary 檔案大小

**⚠️ Phase 2 子 agent 失敗處理（2026-05-21 經驗）**：
子 agent B 可能因 API 錯誤（`max_iterations` / Provider returned error）而失敗，即使 fetcher（Phase 1）已成功。這不是腳本問題，而是子 agent 在安裝依賴或執行過程中遇到 API 限流/錯誤。

**降級流程**：
1. 主 agent 直接用 `terminal` 執行（不需要再啟動子 agent）：
   ```
   pip install pandas numpy -q --break-system-packages
   cd {SKILL_DIR} && python3 tools/normalize_market_data.py YYYYMMDD
   python3 tools/rank_intraday_candidates.py YYYYMMDD
   python3 tools/extract_report_data.py YYYYMMDD
   ```
2. 確認 `outputs/report_summary_YYYYMMDD.json` 已產出
3. 繼續啟動 Phase 3 dt_writer

**預期輸出**：
- normalize：`資料清洗完成！總計處理 N 檔股票。`
- rank：前 10 名列表 + `完整 50 檔候選名單已輸出至: outputs/daytrade_candidates_ranked_YYYYMMDD.csv`
- extract：`Report summary written to outputs/report_summary_YYYYMMDD.json` + 檔案大小

**輸出**：
- `processed_data/market_data_normalized_YYYYMMDD.csv`（~1,950 檔）
- `processed_data/market_data_normalized_YYYYMMDD.json`
- `outputs/daytrade_candidates_ranked_YYYYMMDD.csv`（50 檔）
- `outputs/report_summary_YYYYMMDD.json`（~20KB 精簡摘要）

### 子 Agent C — 撰寫報告 (dt_writer)

**輸入**：目標日期（YYYYMMDD）、技能目錄路徑
**任務**：
1. 讀取 `{SKILL_DIR}/outputs/report_summary_YYYYMMDD.json`（精簡報告摘要，**唯一需要的資料檔**，~20KB）
2. 根據摘要資料撰寫完整盤後分析報告（Markdown 格式），存至 `{SKILL_DIR}/reports/twse_YYYYMMDD_analysis.md`
3. 報告必須包含：大盤指數、市場統計、漲跌家數、類股指數、三大法人、漲停股票、成交值排行、盤勢總結、明日當沖標的建議
4. 從當沖候選池篩選 5 檔明日當沖建議標的（考量法人動向、流動性、題材延續性）
5. 回報報告完整內容

**重要**：dt_writer **不需要**讀取 raw_data/ 下的任何原始檔案。所有資料已在 report_summary JSON 中預先萃取完畢。這是解決 Phase 3 超時（600s）的核心設計——原本 dt_writer 需要讀取 7 個檔案合計 700KB+，現在只需 1 個 ~17KB 檔案。

**輸出**：
- `reports/twse_YYYYMMDD_analysis.md`

### 主 Agent — Orchestrator

收到所有子 agent 完成後：
1. 驗收 dt_writer 子 agent 產出的報告
2. 確認 `reports/twse_YYYYMMDD_analysis.md` 已寫入
3. 將報告重點摘要交付給使用者
4. 不得自行撰寫報告內容

## ⚠️ 超時與失敗處理

### Phase 3 超時（已大幅改善）
Phase 3（dt_writer）原本需要讀取多個大型 CSV/JSON 檔案（合計 700KB+）並交叉分析，`delegate_task` 預設 600 秒 timeout 下幾乎必超時。

**根本修正**：新增 `tools/extract_report_data.py`（Phase 2.5），在 dt_writer 啟動前先將所有 raw_data 萃取為 ~17KB 的 `report_summary_YYYYMMDD.json`。dt_writer 只需讀取這一個精簡檔案，context 大小從 700KB+ 降至 17KB。

**現狀（2026-05-21 實測）**：dt_writer 可在 ~470s 內完成，低於 600s 門檻。**目前不需要預先降級**，直接啟動 dt_writer 即可。若未來再次超時，再啟用降級策略。

### Phase 2 子 agent 失敗（2026-05-21 新發現）
子 agent B（processor）可能因 API 錯誤（`max_iterations` / Provider returned error）而失敗。這與 Phase 3 超時不同，是 API 層面的間歇性錯誤。

**處理方式**：主 agent 降級為直接用 `terminal` 執行三個腳本（normalize → rank → extract），不需要再啟動新的子 agent。詳見「子 Agent B」章節的降級流程。

### 降級策略（Phase 3 仍超時時）
若 dt_writer 仍超時，主 agent 應降級為自行處理：
1. 用 `read_file` 讀取 `outputs/report_summary_YYYYMMDD.json`
2. 根據摘要資料自行撰寫報告
3. 用 `write_file` 撰寫報告至 `reports/` 目錄
4. **此時主 agent 可暫時違反「不自撰報告」原則，因為是 fallback**

### 分析腳本執行技巧
寫 Python 腳本檔案再用 `terminal` 執行，比 heredoc/inline Python 更可靠：
```python
# ✅ 可靠：寫檔 + 執行
write_file('/path/analyze.py', script_content)
terminal(command='cd {SKILL_DIR} && python3 analyze.py')

# ❌ 不可靠：heredoc 或 -c "..." 容易因引號/換行出問題
```

## 注意事項

- 三大法人資料可能延遲，若無資料則標註並使用前日參考
- 使用 `delegate_task` 時，每個子 agent 的 prompt 要包含完整的執行步驟和預期輸出
- Agent A 和 Agent B 可以平行啟動（Agent B 依賴 Agent A 的輸出，但可以在 Agent A 完成後立即啟動）
- Agent C (dt_writer) 必須在 Agent A 和 Agent B 都完成後才啟動
- 主 agent 絕不自行撰寫報告，只做 orchestrator 的角色：派工、驗收、交付（超時 fallback 除外）
