#!/usr/bin/env python3
"""
extract_report_data.py — 從 raw_data/ 萃取精簡報告摘要 JSON

用途：讓 dt_writer 子 agent 不需讀取原始大檔，只需讀取這份精簡摘要即可撰寫報告。
解決：dt_writer 因讀取多個大型 CSV/JSON 而 context 膨脹導致超時的問題。

輸入：target_date (YYYYMMDD)
輸出：outputs/report_summary_YYYYMMDD.json（約 3-5KB，vs 原始檔合計 700KB+）

用法：
  cd {SKILL_DIR}
  python3 tools/extract_report_data.py 20260520
"""

import os
import sys
import json
import csv

def read_csv_safe(path):
    """讀取 TWSE CSV，處理千分位逗號"""
    rows = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        header = [h.strip() for h in header]
        for row in reader:
            if len(row) < len(header):
                continue
            rows.append(dict(zip(header, [c.strip() for c in row])))
    return header, rows

def to_int(val):
    """安全轉整數，處理千分位"""
    try:
        return int(str(val).replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
        return 0

def to_float(val):
    """安全轉浮點"""
    try:
        return float(str(val).replace(',', '').replace(' ', '').replace('+', ''))
    except (ValueError, TypeError):
        return 0.0

def extract(target_date):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base)
    
    summary = {
        "date": target_date,
        "indices": [],
        "market_stats": {},
        "updown": {},
        "sector_top5": [],
        "sector_bottom5": [],
        "fund_totals": {},
        "fund_buy_top10": [],
        "fund_sell_top10": [],
        "limit_up_stocks": [],
        "limit_down_stocks": [],
        "top_losers_10": [],
        "turnover_top10": [],
        "daytrade_top20": [],
    }
    
    # === 1. 類股指數 ===
    indices_path = f'raw_data/twse_indices_{target_date}.json'
    if os.path.exists(indices_path):
        with open(indices_path, 'r', encoding='utf-8') as f:
            indices_data = json.load(f)
        
        sector_indices = []
        major_names = ['發行量加權股價指數', '臺灣50指數', '臺灣中型100指數', 
                       '臺灣高股息指數', '未含金融指數', '未含電子指數', '小型股300指數',
                       '臺灣資訊科技指數', '臺灣發達指數']
        
        for row in indices_data:
            name = row[0].strip()
            val = to_float(row[1])
            sign = row[2].strip() if len(row) > 2 else ''
            chg = to_float(row[3])
            pct = to_float(row[4])
            
            if sign == '-':
                chg = -abs(chg)
                pct = -abs(pct)
            elif sign == '+':
                chg = abs(chg)
                pct = abs(pct)
            # else: blank = flat, keep as is
            
            entry = {"name": name, "close": val, "change": chg, "pct": pct}
            
            if name in major_names:
                summary["indices"].append(entry)
            elif '類指數' in name and name != '其他類指數':
                sector_indices.append(entry)
        
        # Sort sectors by pct
        sector_indices.sort(key=lambda x: x['pct'], reverse=True)
        summary["sector_top5"] = sector_indices[:5]
        summary["sector_bottom5"] = sector_indices[-5:] if len(sector_indices) >= 5 else sector_indices
    
    # === 2. 大盤統計 ===
    stats_path = f'raw_data/twse_market_stats_{target_date}.json'
    if os.path.exists(stats_path):
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats_data = json.load(f)
        for row in stats_data:
            label = row[0].strip()
            if '證券合計' in label:
                summary["market_stats"] = {
                    "label": "證券合計",
                    "value": to_int(row[1]),
                    "volume": to_int(row[2]),
                    "transactions": to_int(row[3])
                }
                break
    
    # === 3. 漲跌家數 ===
    updown_path = f'raw_data/twse_updown_{target_date}.json'
    if os.path.exists(updown_path):
        with open(updown_path, 'r', encoding='utf-8') as f:
            updown_data = json.load(f)
        summary["updown"] = {
            "twse_up": to_int(updown_data[0][1].split('(')[0]),
            "twse_up_limit": to_int(updown_data[0][1].split('(')[1].rstrip(')')),
            "twse_down": to_int(updown_data[1][1].split('(')[0]),
            "twse_down_limit": to_int(updown_data[1][1].split('(')[1].rstrip(')')),
            "twse_flat": to_int(updown_data[2][1]),
            "tpex_up": to_int(updown_data[0][2].split('(')[0]),
            "tpex_up_limit": to_int(updown_data[0][2].split('(')[1].rstrip(')')),
            "tpex_down": to_int(updown_data[1][2].split('(')[0]),
            "tpex_down_limit": to_int(updown_data[1][2].split('(')[1].rstrip(')')),
            "tpex_flat": to_int(updown_data[2][2]),
        }
    
    # === 4. 三大法人 ===
    fund_path = f'raw_data/twse_fund_{target_date}.csv'
    if os.path.exists(fund_path):
        header, rows = read_csv_safe(fund_path)
        
        total_3 = 0; total_foreign = 0; total_invest = 0; total_dealer = 0
        fund_rows = []
        
        for row in rows:
            try:
                t = to_int(row['三大法人買賣超股數'])
                fr = to_int(row['外陸資買賣超股數(不含外資自營商)'])
                iv = to_int(row['投信買賣超股數'])
                dl = to_int(row['自營商買賣超股數'])
                total_3 += t
                total_foreign += fr
                total_invest += iv
                total_dealer += dl
                fund_rows.append({
                    "code": row['證券代號'],
                    "name": row['證券名稱'],
                    "total3": t,
                    "foreign": fr,
                    "invest": iv,
                    "dealer": dl
                })
            except (KeyError, ValueError):
                continue
        
        summary["fund_totals"] = {
            "total3": total_3,
            "foreign": total_foreign,
            "invest": total_invest,
            "dealer": total_dealer
        }
        
        fund_rows.sort(key=lambda x: x['total3'], reverse=True)
        summary["fund_buy_top10"] = fund_rows[:10]
        fund_rows.sort(key=lambda x: x['total3'])
        summary["fund_sell_top10"] = fund_rows[:10]
    
    # === 5. 上市個股分析（漲停/跌停/成交值排行/跌幅排行）===
    stocks_path = f'raw_data/twse_stocks_{target_date}.csv'
    if os.path.exists(stocks_path):
        import pandas as pd
        df = pd.read_csv(stocks_path, encoding='utf-8-sig')
        for c in df.columns:
            df[c] = df[c].astype(str).str.replace(',', '').str.strip()
        
        df['成交金額'] = pd.to_numeric(df['成交金額'], errors='coerce')
        df['收盤價'] = pd.to_numeric(df['收盤價'], errors='coerce')
        df['漲跌價差'] = pd.to_numeric(df['漲跌價差'], errors='coerce')
        
        sign_col = '漲跌(+/-)'
        df['signed_chg'] = df.apply(
            lambda r: r['漲跌價差'] if r[sign_col] == '+' else 
                      (-r['漲跌價差'] if r[sign_col] == '-' else 0), axis=1)
        df['prev_close'] = df['收盤價'] - df['signed_chg']
        df['chg_pct'] = (df['signed_chg'] / df['prev_close'] * 100).round(2)
        
        # Filter regular stocks only (4-digit codes, possibly with suffix letter)
        stocks = df[df['證券代號'].str.match(r'^\d{4}[A-Za-z]?$')].copy()
        
        # 漲停
        limit_up = stocks[stocks['chg_pct'] >= 9.5].sort_values('chg_pct', ascending=False)
        for _, r in limit_up.iterrows():
            summary["limit_up_stocks"].append({
                "code": r['證券代號'], "name": r['證券名稱'],
                "close": r['收盤價'], "chg_pct": r['chg_pct']
            })
        
        # 跌停
        limit_down = stocks[stocks['chg_pct'] <= -9.5].sort_values('chg_pct')
        for _, r in limit_down.iterrows():
            summary["limit_down_stocks"].append({
                "code": r['證券代號'], "name": r['證券名稱'],
                "close": r['收盤價'], "chg_pct": r['chg_pct']
            })
        
        # 跌幅 TOP10
        for _, r in stocks.nsmallest(10, 'chg_pct').iterrows():
            summary["top_losers_10"].append({
                "code": r['證券代號'], "name": r['證券名稱'],
                "close": r['收盤價'], "chg_pct": r['chg_pct']
            })
        
        # 成交值 TOP10
        for _, r in stocks.nlargest(10, '成交金額').iterrows():
            summary["turnover_top10"].append({
                "code": r['證券代號'], "name": r['證券名稱'],
                "close": r['收盤價'], "chg_pct": r['chg_pct'],
                "value_b": round(r['成交金額'] / 1e8, 1)
            })
    
    # === 6. 當沖候選池 TOP20 ===
    candidates_path = f'outputs/daytrade_candidates_ranked_{target_date}.csv'
    if os.path.exists(candidates_path):
        import pandas as pd
        cdf = pd.read_csv(candidates_path, encoding='utf-8-sig')
        for _, r in cdf.head(20).iterrows():
            summary["daytrade_top20"].append({
                "code": str(r.iloc[0]), "name": str(r.iloc[1]),
                "market": str(r.iloc[2]), "close": r.iloc[3],
                "chg_pct": r.iloc[4], "volume_lots": r.iloc[5],
                "amplitude": r.iloc[6], "avg_price": r.iloc[7],
                "score": r.iloc[8]
            })
    
    # === 輸出 ===
    os.makedirs('outputs', exist_ok=True)
    out_path = f'outputs/report_summary_{target_date}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"Report summary written to {out_path}")
    print(f"File size: {os.path.getsize(out_path):,} bytes")
    
    # Print key stats for verification
    print(f"\n--- Summary Stats ---")
    print(f"Indices: {len(summary['indices'])} major + {len(summary['sector_top5'])} sector top + {len(summary['sector_bottom5'])} sector bottom")
    print(f"Limit up: {len(summary['limit_up_stocks'])}, Limit down: {len(summary['limit_down_stocks'])}")
    print(f"Fund buy top10: {len(summary['fund_buy_top10'])}, sell top10: {len(summary['fund_sell_top10'])}")
    print(f"Daytrade top20: {len(summary['daytrade_top20'])}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 extract_report_data.py YYYYMMDD")
        sys.exit(1)
    extract(sys.argv[1])
