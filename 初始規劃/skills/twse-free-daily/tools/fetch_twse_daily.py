# hermes/skills/twse-free-daily/tools/fetch_twse_daily.py
import os
import sys
import time
import random
import json
import requests
import pandas as pd
from datetime import datetime

def get_twse_daily(date_str):
    """抓取上市個股日收盤行情 (包含大盤，這裡主要取個股)"""
    print(f"[{datetime.now()}] 正在抓取 TWSE 上市資料: {date_str}...")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALLBUT0999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"TWSE 請求失敗，狀態碼: {response.status_code}")
            return None
        
        data = response.json()
        if data.get('stat') != 'OK' or 'data9' not in data:
            print(f"TWSE 該日無交易資料或結構改變: {date_str}")
            return None
            
        # data9 是所有股票的收盤行情
        columns = data['fields9']
        rows = data['data9']
        df = pd.DataFrame(rows, columns=columns)
        df['市場'] = '上市'
        return df
    except Exception as e:
        print(f"抓取 TWSE 發生異常: {str(e)}")
        return None

def get_tpex_daily(date_str):
    """抓取上櫃個股日收盤行情"""
    print(f"[{datetime.now()}] 正在抓取 TPEx 上櫃資料: {date_str}...")
    # 櫃買中心的日期格式需要轉為 民國年 (如 115/05/19)
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
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"TPEx 請求失敗，狀態碼: {response.status_code}")
            return None
            
        data = response.json()
        if not data.get('aaData'):
            print(f"TPEx 該日無交易資料: {tpex_date}")
            return None
            
        # 欄位定義
        columns = ["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "均價", "成交股數", "成交金額(元)", "成交筆數", "最後買價", "最後買量", "最後賣價", "最後賣量", "發行股數", "次日漲停價", "次日跌停價"]
        rows = data['aaData']
        
        # 只取前 11 個我們需要的核心欄位，避免 API 欄位數量變動不匹配
        cleaned_rows = [row[:11] for row in rows]
        df = pd.DataFrame(cleaned_rows, columns=columns[:11])
        df['市場'] = '上櫃'
        return df
    except Exception as e:
        print(f"抓取 TPEx 發生異常: {str(e)}")
        return None

def main():
    # 預設為前一個交易日/最新交易日，若手動輸入則使用參數
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")
    
    # 建立暫存資料夾
    os.makedirs('raw_data', exist_ok=True)
    
    # 抓取上市
    twse_df = get_twse_daily(target_date)
    
    # 隨機延遲，防止被鎖 IP
    time.sleep(random.uniform(3.0, 6.0))
    
    # 抓取上櫃
    tpex_df = get_tpex_daily(target_date)
    
    if twse_df is None and tpex_df is None:
        print(f"Error: 無法取得 {target_date} 的任何市場資料，可能為休假日。")
        sys.exit(1)
        
    # 保存原始資料供後續模組讀取
    if twse_df is not None:
        twse_df.to_csv(f'raw_data/twse_{target_date}.csv', index=False, encoding='utf-8-sig')
    if tpex_df is not None:
        tpex_df.to_csv(f'raw_data/tpex_{target_date}.csv', index=False, encoding='utf-8-sig')
        
    print(f"成功儲存 {target_date} 原始交易資料。")

if __name__ == "__main__":
    main()