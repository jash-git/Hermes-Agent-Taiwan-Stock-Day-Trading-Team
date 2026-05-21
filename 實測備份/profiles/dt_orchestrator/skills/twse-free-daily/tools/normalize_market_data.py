# hermes/skills/twse-free-daily/tools/normalize_market_data.py
import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime

def clean_and_float(val):
    """將字串中的逗號、正負號洗乾淨並轉為 float"""
    if pd.isna(val):
        return 0.0
    val_str = str(val).replace(',', '').replace(' ', '').strip()
    if val_str in ['', '-', 'X', '加']:
        return 0.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def normalize_data(target_date):
    twse_path = f'raw_data/twse_stocks_{target_date}.csv'
    tpex_path = f'raw_data/tpex_{target_date}.csv'
    dt_list_path = f'raw_data/daytrade_list_{target_date}.csv'
    
    final_list = []
    
    # 1. 處理上市
    if os.path.exists(twse_path):
        df_twse = pd.read_csv(twse_path)
        for _, row in df_twse.iterrows():
            # 排除權證、ETF（代號通常長度大於4位數且包含英文字母，或非純數字個股股票）
            code = str(row['證券代號']).strip().replace('"', '')
            if len(code) != 4: 
                continue
                
            close = clean_and_float(row['收盤價'])
            open_p = clean_and_float(row['開盤價'])
            high = clean_and_float(row['最高價'])
            low = clean_and_float(row['最低價'])
            
            # 計算昨日收盤（透過今日收盤與漲跌價差推算）
            change_sign = row['漲跌(+/-)'] if '漲跌(+/-)' in row and pd.notna(row['漲跌(+/-)']) else ''
            change_val = clean_and_float(row['漲跌價差'])
            if '?' in str(change_sign) or '-' in str(change_sign):
                change_val = -change_val
                
            prev_close = close - change_val if close != 0 else 0
            
            # 成交股數轉張數，成交金額轉元
            volume_shares = clean_and_float(row['成交股數'])
            volume_sheets = volume_shares / 1000
            amount = clean_and_float(row['成交金額'])
            
            # 計算振幅與均價
            amplitude = ((high - low) / prev_close * 100) if prev_close > 0 else 0
            avg_price = (amount / volume_shares) if volume_shares > 0 else close
            pct_change = (change_val / prev_close * 100) if prev_close > 0 else 0
            
            final_list.append({
                "日期": target_date,
                "代號": code,
                "名稱": str(row['證券名稱']).strip(),
                "市場": "上市",
                "開盤價": open_p,
                "最高價": high,
                "最低價": low,
                "收盤價": close,
                "昨收價": prev_close,
                "漲跌幅%": round(pct_change, 2),
                "成交張數": int(volume_sheets),
                "成交金額": int(amount),
                "均價": round(avg_price, 2),
                "振幅%": round(amplitude, 2)
            })

    # 2. 處理上櫃
    if os.path.exists(tpex_path):
        df_tpex = pd.read_csv(tpex_path)
        for _, row in df_tpex.iterrows():
            code = str(row['代號']).strip()
            if len(code) != 4:
                continue
                
            close = clean_and_float(row['收盤'])
            open_p = clean_and_float(row['開盤'])
            high = clean_and_float(row['最高'])
            low = clean_and_float(row['最低'])
            change_val = clean_and_float(row['漲跌'])
            
            prev_close = close - change_val if close != 0 else 0
            volume_shares = clean_and_float(row['成交股數'])
            volume_sheets = volume_shares / 1000
            amount = clean_and_float(row['成交金額(元)'])
            
            amplitude = ((high - low) / prev_close * 100) if prev_close > 0 else 0
            avg_price = (amount / volume_shares) if volume_shares > 0 else close
            pct_change = (change_val / prev_close * 100) if prev_close > 0 else 0
            
            final_list.append({
                "日期": target_date,
                "代號": code,
                "名稱": str(row['名稱']).strip(),
                "市場": "上櫃",
                "開盤價": open_p,
                "最高價": high,
                "最低價": low,
                "收盤價": close,
                "昨收價": prev_close,
                "漲跌幅%": round(pct_change, 2),
                "成交張數": int(volume_sheets),
                "成交金額": int(amount),
                "均價": round(avg_price, 2),
                "振幅%": round(amplitude, 2)
            })

    if not final_list:
        print("沒有轉換出任何結構化資料，請確認原始資料是否正確。")
        return
        
    master_df = pd.DataFrame(final_list)
    
    # 3. 整合當沖名冊白名單
    if os.path.exists(dt_list_path):
        dt_df = pd.read_csv(dt_list_path)
        dt_df['代號'] = dt_df['代號'].astype(str).str.strip()
        # 合併，找不到的預設為 False (但台股基本上多數4碼普通股皆可當沖)
        master_df = pd.merge(master_df, dt_df[['代號', '可當沖']], on='代號', how='left')
        master_df['可當沖'] = master_df['可當沖'].fillna(True) # 預設放行基本股
    else:
        master_df['可當沖'] = True
        
    # 過濾掉未開盤或流動性極差的殭屍股
    master_df = master_df[master_df['收盤價'] > 0]
    master_df = master_df[master_df['成交張數'] > 0]
    
    # 輸出標準化檔案
    os.makedirs('processed_data', exist_ok=True)
    master_df.to_csv(f'processed_data/market_data_normalized_{target_date}.csv', index=False, encoding='utf-8-sig')
    master_df.to_json(f'processed_data/market_data_normalized_{target_date}.json', orient='records', force_ascii=False, indent=2)
    
    print(f"資料清洗完成！總計處理 {len(master_df)} 檔股票。")

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")
    normalize_data(target_date)

if __name__ == "__main__":
    main()