#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hermes Agent Team - Risk Filter Skill Tool
File: hermes/skills/risk-filter/tools/apply_risk_rules.py
Description: 對當沖候選名單進行嚴格的風險過濾，產出通過與被排除的名單。
"""

import os
import sys
import json
import argparse
import pandas as pd

# 預設風險設定檔內容（若找不到外部 config，則使用此預設值）
DEFAULT_CONFIG = {
    "standard": {
        "min_volume": 500,         # 最少成交量 (張)
        "min_turnover": 30000000,  # 最少成交金額 (元)
        "min_price": 10.0,         # 最低股價 (元)
        "max_price": 300.0,        # 最高股價 (元)
        "max_amplitude": 8.0,      # 最大振幅 (%)
        "exclude_limit_up": True   # 是否排除前一日漲停股
    },
    "conservative": {
        "min_volume": 1000,
        "min_turnover": 50000000,
        "min_price": 20.0,
        "max_price": 200.0,
        "max_amplitude": 6.0,
        "exclude_limit_up": True
    },
    "aggressive": {
        "min_volume": 300,
        "min_turnover": 15000000,
        "min_price": 5.0,
        "max_price": 500.0,
        "max_amplitude": 10.0,
        "exclude_limit_up": False
    }
}

def load_config(config_path, mode="standard"):
    """讀取風險設定檔"""
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[INFO] 成功讀取外部設定檔: {config_path}")
                return config.get(mode, DEFAULT_CONFIG["standard"])
        except Exception as e:
            print(f"[WARNING] 讀取設定檔出錯 ({e})，將使用內建預設值。")
    
    print(f"[INFO] 使用內建 {mode} 風險模式參數。")
    return DEFAULT_CONFIG.get(mode, DEFAULT_CONFIG["standard"])


def apply_risk_filters(df, rules):
    """
    核心風險過濾引擎
    輸入欄位預期包含: stock_id, stock_name, close, volume(張), turnover(元), open, high, low, amplitude(%)
    """
    passed_list = []
    rejected_list = []
    
    # 確保欄位型態正確
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df['turnover'] = pd.to_numeric(df['turnover'], errors='coerce')
    df['amplitude'] = pd.to_numeric(df['amplitude'], errors='coerce')
    
    for _, row in df.iterrows():
        stock_id = row.get('stock_id', 'Unknown')
        stock_name = row.get('stock_name', '')
        
        # 提取檢查數值
        price = row['close']
        volume = row['volume']
        turnover = row['turnover']
        amplitude = row['amplitude']
        
        # 檢查缺失值
        if pd.isna(price) or pd.isna(volume) or pd.isna(turnover):
            row['reject_reason'] = "資料不完整(NaN)"
            rejected_list.append(row)
            continue
            
        # 1. 流動性檢驗 (張數)
        if volume < rules['min_volume']:
            row['reject_reason'] = f"流動性不足: 成交量 {volume}張 < {rules['min_volume']}張"
            rejected_list.append(row)
            continue
            
        # 2. 流動性檢驗 (成交金額)
        if turnover < rules['min_turnover']:
            row['reject_reason'] = f"流動性不足: 成交額 {turnover/(10**4):.1f}萬 < {rules['min_turnover']/(10**4):.1f}萬"
            rejected_list.append(row)
            continue
            
        # 3. 價格區間檢驗
        if price < rules['min_price'] or price > rules['max_price']:
            row['reject_reason'] = f"價格不符區間: 股價 {price} 元不在 [{rules['min_price']} - {rules['max_price']}] 範圍"
            rejected_list.append(row)
            continue
            
        # 4. 波動率檢驗 (過度激烈的股票不留)
        if amplitude > rules['max_amplitude']:
            row['reject_reason'] = f"波動過大: 前日振幅 {amplitude}% > {rules['max_amplitude']}%"
            rejected_list.append(row)
            continue
            
        # 5. 漲停過濾 (模擬免費訊號：若收盤價接近或等於最高價，且漲幅大於9.5%)
        # 注意：此處可根據上游是否有提供 'change_percent' 欄位加強
        if rules['exclude_limit_up'] and row.get('change_percent', 0) >= 9.5:
            row['reject_reason'] = f"排除強勢漲停股，避免隔日跳空鎖死無法操作"
            rejected_list.append(row)
            continue
            
        # 6. 免費第三方警示/處置股標記（預留擴充）
        # 如果上游資料庫有標記 is_caution 或 is_altered，在此處攔截
        if row.get('is_caution', False) or row.get('is_altered', False):
            row['reject_reason'] = "證交所列為注意股/處置股/全額交割"
            rejected_list.append(row)
            continue

        # 通過所有考驗
        passed_list.append(row)

    df_passed = pd.DataFrame(passed_list) if passed_list else pd.DataFrame(columns=df.columns)
    df_rejected = pd.DataFrame(rejected_list) if rejected_list else pd.DataFrame(columns=list(df.columns) + ['reject_reason'])
    
    return df_passed, df_rejected


def generate_summary_report(passed_count, rejected_count, df_rejected, mode):
    """生成終端機視覺化摘要報告"""
    total = passed_count + rejected_count
    print("\n" + "="*50)
    print(f"【Hermes Risk-Filter 風險審查報告 - 模式: {mode.upper()}】")
    print("="*50)
    print(f" 總審查標的數: {total} 檔")
    print(f" ✅ 審查通過 (可當沖): {passed_count} 檔")
    print(f" ❌ 風險排除 (已過濾): {rejected_count} 檔")
    print("-"*50)
    
    if rejected_count > 0:
        print("【主要排除原因統計】")
        # 簡易統計排除原因
        reason_counts = df_rejected['reject_reason'].apply(lambda x: x.split(":")[0]).value_counts()
        for reason, count in reason_counts.items():
            print(f" - {reason}: {count} 檔")
    print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Hermes 交易團隊 - 風險過濾引擎")
    parser.add_argument("--input", required=True, help="輸入的候選名單 CSV 檔案路徑 (e.g. daytrade_candidates_ranked.csv)")
    parser.format_help()
    parser.add_argument("--outdir", default=".", help="輸出結果的資料夾路徑")
    parser.add_argument("--config", default=None, help="risk_rules_config.json 的路徑")
    parser.add_argument("--mode", choices=["standard", "conservative", "aggressive"], default="standard", help="風險控管嚴格度")
    
    args = parser.parse_args()
    
    # 1. 檢查輸入檔案
    if not os.path.exists(args.input):
        print(f"[ERROR] 找不到輸入檔案: {args.input}")
        sys.exit(1)
        
    try:
        df_input = pd.read_csv(args.input)
    except Exception as e:
        print(f"[ERROR] 讀取 CSV 失敗: {e}")
        sys.exit(1)
        
    if df_input.empty:
        print("[WARNING] 輸入的候選名單為空，終止風險篩選。")
        # 產出空的輸出檔案確保下游不崩潰
        pd.DataFrame().to_csv(os.path.join(args.outdir, "filtered_candidates.csv"), index=False)
        sys.exit(0)

    # 2. 載入規則
    rules = load_config(args.config, mode=args.mode)
    
    # 3. 執行風險過濾
    print(f"[INFO] 開始進行風險過濾處理...")
    df_passed, df_rejected = apply_risk_filters(df_input, rules)
    
    # 4. 確保輸出目錄存在
    os.makedirs(args.outdir, exist_ok=True)
    
    passed_path = os.path.join(args.outdir, "filtered_candidates.csv")
    rejected_path = os.path.join(args.outdir, "rejected_candidates.csv")
    
    # 5. 儲存結果（保持上游的排序順序，只拿掉不安全的股票）
    df_passed.to_csv(passed_path, index=False, encoding='utf-8-sig')
    df_rejected.to_csv(rejected_path, index=False, encoding='utf-8-sig')
    
    print(f"[SUCCESS] 篩選完成！")
    print(f" -> 通過名單已寫入: {passed_path}")
    print(f" -> 排除名單已寫入: {rejected_path}")
    
    # 6. 印出摘要
    generate_summary_report(len(df_passed), len(df_rejected), df_rejected, args.mode)

if __name__ == "__main__":
    main()