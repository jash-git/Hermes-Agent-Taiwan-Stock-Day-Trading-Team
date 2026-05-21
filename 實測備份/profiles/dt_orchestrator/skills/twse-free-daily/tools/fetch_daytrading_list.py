# hermes/skills/twse-free-daily/tools/fetch_daytrading_list.py
import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime

def fetch_twse_daytable():
    """從證交所開放資料下載現股當沖名冊"""
    print(f"[{datetime.now()}] 正在抓取可當沖標的名冊...")
    # 證交所開放資料：可現股當沖之證券名冊
    url = "https://openapi.twse.com.tw/v1/exchangeReport/TWTB4U"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print("無法由 OpenAPI 取得當沖名冊，嘗試備用方案...")
            return None
        
        data = response.json()
        if not data:
            return None
            
        df = pd.DataFrame(data)
        # 欄位：Code (證券代號), Name (證券名稱)
        df = df.rename(columns={"Code": "代號", "Name": "名稱"})
        df['可當沖'] = True
        return df[['代號', '名稱', '可當沖']]
    except Exception as e:
        print(f"抓取當沖名冊時發生錯誤: {e}")
        return None

def fetch_notice_stocks():
    """抓取今日公佈之注意股票 (風險過高標的)"""
    # 備用輕量級設計：若有需要可在此擴充爬取證交所公佈欄
    # 此處回傳空清單，保留介面讓風險模組使用
    return []

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")
    os.makedirs('raw_data', exist_ok=True)
    
    dt_list = fetch_twse_daytable()
    
    if dt_list is None:
        print("警告: 未能取得官方最新當沖名冊，將由後續模組以基本規則判斷或放行。")
        # 建立一個空的白名單，避免後面程式出錯
        dt_list = pd.DataFrame(columns=['代號', '名稱', '可當沖'])
        
    output_path = f'raw_data/daytrade_list_{target_date}.csv'
    dt_list.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"成功儲存當沖名冊白名單至 {output_path}。")

if __name__ == "__main__":
    main()