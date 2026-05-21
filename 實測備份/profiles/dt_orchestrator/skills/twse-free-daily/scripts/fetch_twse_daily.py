# hermes/skills/twse-free-daily/scripts/fetch_twse_daily.py
"""
台股每日收盤資料抓取工具（含上市、上櫃、三大法人、信用交易）

使用方式：
  python3 fetch_twse_daily.py [YYYYMMDD]

說明：
  - 抓取 TWSE MI_INDEX（上市個股收盤、指數、統計、漲跌家數）
  - 抓取 TWSE T86（三大法人買賣超）
  - 抓取 TWSE MI_MARGN（信用交易統計）
  - 抓取 TPEx（上櫃個股收盤）
  - 輸出至 raw_data/ 目錄

注意：
  - TWSE API 已改為 tables 結構（非舊版 data9）
  - 回應含 HTML 標籤需清理後才能解析 JSON
  - 詳細 API 結構說明見 references/twse-api-changes.md
"""
import os
import sys
import time
import random
import json
import re
import requests
import pandas as pd
from datetime import datetime

def clean_json(raw):
    """清理 TWSE API 回應中的 HTML 標籤和控制字元"""
    raw = re.sub(r'<[^>]+>', '', raw)
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)
    return raw

def get_twse_daily(date_str):
    """抓取上市個股日收盤行情（含指數、統計資訊）"""
    print(f"[{datetime.now()}] 正在抓取 TWSE 上市資料: {date_str}...")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALLBUT0999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"TWSE 請求失敗，狀態碼: {response.status_code}")
            return None, None, None, None

        raw = clean_json(response.text)
        data = json.loads(raw)

        if 'tables' not in data:
            print(f"TWSE 該日無交易資料或結構改變: {date_str}")
            return None, None, None, None

        tables = data['tables']

        # tables[8] = 每日收盤行情（全部）— 對應舊版 data9
        stock_df = None
        if len(tables) > 8 and tables[8].get('data'):
            t8 = tables[8]
            stock_df = pd.DataFrame(t8['data'], columns=t8['fields'])
            stock_df['市場'] = '上市'

        # tables[6] = 大盤統計資訊
        market_stats = None
        if len(tables) > 6 and tables[6].get('data'):
            market_stats = tables[6]['data']

        # tables[7] = 漲跌證券數合計
        updown_stats = None
        if len(tables) > 7 and tables[7].get('data'):
            updown_stats = tables[7]['data']

        # tables[0] = 上市類股指數
        index_data = None
        if len(tables) > 0 and tables[0].get('data'):
            index_data = tables[0]['data']

        return stock_df, market_stats, updown_stats, index_data

    except Exception as e:
        print(f"抓取 TWSE 發生異常: {str(e)}")
        return None, None, None, None

def get_twse_fund(date_str):
    """抓取三大法人買賣超 (T86)"""
    print(f"[{datetime.now()}] 正在抓取三大法人買賣超: {date_str}...")
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALLBUT0999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"T86 請求失敗，狀態碼: {response.status_code}")
            return None

        raw = clean_json(response.text)
        data = json.loads(raw)

        if data.get('stat') != 'OK' or 'data' not in data:
            print(f"T86 該日無資料: {date_str}")
            return None

        df = pd.DataFrame(data['data'], columns=data['fields'])
        return df
    except Exception as e:
        print(f"抓取 T86 發生異常: {str(e)}")
        return None

def get_twse_margin(date_str):
    """抓取信用交易統計 (MI_MARGN)"""
    print(f"[{datetime.now()}] 正在抓取信用交易統計: {date_str}...")
    url = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date={date_str}&selectType=ALL"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"MI_MARGN 請求失敗，狀態碼: {response.status_code}")
            return None

        raw = clean_json(response.text)
        data = json.loads(raw)

        if 'tables' not in data:
            return None

        result = {}
        for i, t in enumerate(data['tables']):
            result[f'table_{i}'] = {
                'title': t.get('title', ''),
                'fields': t.get('fields', []),
                'data': t.get('data', [])
            }
        return result
    except Exception as e:
        print(f"抓取 MI_MARGN 發生異常: {str(e)}")
        return None

def get_tpex_daily(date_str):
    """抓取上櫃個股日收盤行情"""
    print(f"[{datetime.now()}] 正在抓取 TPEx 上櫃資料: {date_str}...")
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        roc_year = dt.year - 1911
        tpex_date = f"{roc_year}/{dt.strftime('%m/%d')}"
    except ValueError:
        print("日期格式錯誤，請使用 YYYYMMDD")
        return None

    url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={tpex_date}&se=EW&s=0,asc,0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"TPEx 請求失敗，狀態碼: {response.status_code}")
            return None

        raw = clean_json(response.text)
        data = json.loads(raw)

        if 'tables' not in data or not data['tables'][0].get('data'):
            print(f"TPEx 該日無交易資料: {tpex_date}")
            return None

        t0 = data['tables'][0]
        # 清理欄位名稱的 trailing space
        columns = [c.strip() for c in t0['fields']]
        rows = t0['data']

        # 只取核心欄位（避免欄位數量變動）
        core_cols = ['代號', '名稱', '收盤', '漲跌', '開盤', '最高', '最低', '均價', '成交股數', '成交金額(元)', '成交筆數']
        col_indices = [columns.index(c) for c in core_cols if c in columns]
        cleaned_rows = [[row[i] for i in col_indices] for row in rows]
        cleaned_cols = [columns[i] for i in col_indices]

        df = pd.DataFrame(cleaned_rows, columns=cleaned_cols)
        df['市場'] = '上櫃'
        return df
    except Exception as e:
        print(f"抓取 TPEx 發生異常: {str(e)}")
        return None

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")

    os.makedirs('raw_data', exist_ok=True)

    # 1. 抓取上市（含指數、統計、漲跌家數）
    stock_df, market_stats, updown_stats, index_data = get_twse_daily(target_date)

    time.sleep(random.uniform(2.0, 4.0))

    # 2. 抓取三大法人
    fund_df = get_twse_fund(target_date)

    time.sleep(random.uniform(2.0, 4.0))

    # 3. 抓取信用交易
    margin_data = get_twse_margin(target_date)

    time.sleep(random.uniform(2.0, 4.0))

    # 4. 抓取上櫃
    tpex_df = get_tpex_daily(target_date)

    # 儲存原始資料
    if stock_df is not None:
        stock_df.to_csv(f'raw_data/twse_stocks_{target_date}.csv', index=False, encoding='utf-8-sig')
    if market_stats is not None:
        with open(f'raw_data/twse_market_stats_{target_date}.json', 'w', encoding='utf-8') as f:
            json.dump(market_stats, f, ensure_ascii=False, indent=2)
    if updown_stats is not None:
        with open(f'raw_data/twse_updown_{target_date}.json', 'w', encoding='utf-8') as f:
            json.dump(updown_stats, f, ensure_ascii=False, indent=2)
    if index_data is not None:
        with open(f'raw_data/twse_indices_{target_date}.json', 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    if fund_df is not None:
        fund_df.to_csv(f'raw_data/twse_fund_{target_date}.csv', index=False, encoding='utf-8-sig')
    if margin_data is not None:
        with open(f'raw_data/twse_margin_{target_date}.json', 'w', encoding='utf-8') as f:
            json.dump(margin_data, f, ensure_ascii=False, indent=2)
    if tpex_df is not None:
        tpex_df.to_csv(f'raw_data/tpex_{target_date}.csv', index=False, encoding='utf-8-sig')

    if stock_df is None and tpex_df is None:
        print(f"Error: 無法取得 {target_date} 的任何市場資料，可能為休假日。")
        sys.exit(1)

    print(f"成功儲存 {target_date} 原始交易資料。")

if __name__ == "__main__":
    main()
