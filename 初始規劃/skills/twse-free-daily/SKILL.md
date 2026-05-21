# SKILL: twse-free-daily

## 使命 (Mission)
以完全免費、公開可取得的資料來源，抓取台灣證券交易所 (TWSE) 最近一個交易日的完整收盤交易資訊，並產出適合當日沖銷 (Day Trading) 篩選的結構化市場資料。

## 職責範圍 (Responsibilities)
- 每日自動或手動觸發後，抓取前一日台股完整交易資料
- 支援個股基本資訊、成交量、漲跌幅、成交值、振幅、均價等核心欄位
- 產出標準化的市場資料（JSON / CSV / DataFrame）
- 提供當沖候選池初步排序與統計指標

## 可用工具 (Tools)
- `fetch_twse_daily.py`：抓取 TWSE 官方公開資料（含上市櫃個股日線）
- `fetch_daytrading_list.py`：取得當日可當沖股票清單（注意融資融券、注意股等限制）
- `normalize_market_data.py`：資料清洗、欄位統一、計算技術指標（振幅%、量比、漲幅等）
- `rank_intraday_candidates.py`：根據當沖偏好進行初步排序（例如量能、波動率、價格區間等）

## 輸入 (Input)
- 目標日期（預設為前一個交易日）
- 可選參數：市場別（上市/上櫃）、排除類股、價格區間等

## 輸出 (Output)
- `market_data_normalized.json` / `.csv`
- `daytrade_candidates_ranked.csv`（含排名分數）
- 市場整體統計摘要（總成交量、漲跌家數、熱門類股等）

## 關鍵原則
- 僅使用公開免費來源（TWSE、TPEx 公開資料、證交所 API）
- 資料必須有時間戳記與來源記錄
- 確保可重現性（同一日期輸入應產出相同結果）
- 處理假日、休市、早盤等特殊情況

## 成功指標
- 每日 16:00 後可穩定抓取前日完整資料
- 資料完整率 > 99%
- 當沖候選池產出時間 < 3 分鐘