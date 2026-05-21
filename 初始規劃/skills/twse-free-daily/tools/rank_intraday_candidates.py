# hermes/skills/twse-free-daily/tools/rank_intraday_candidates.py
import os
import sys
import pandas as pd
from datetime import datetime

def rank_candidates(target_date, min_volume=1000, min_price=10, max_price=150):
    """
    根據當沖特性進行篩選與評分：
    - 當沖需要流動性：成交張數 > min_volume (預設 1000 張)
    - 當沖需要波動：振幅% 愈高、漲跌幅絕對值愈大愈好
    - 價格區間過低(沒有Tick利潤)或過高(資金成本高)進行過濾
    """
    file_path = f'processed_data/market_data_normalized_{target_date}.csv'
    if not os.path.exists(file_path):
        print(f"找不到標準化資料: {file_path}，請先執行前面的工具。")
        return

    df = pd.read_csv(file_path)
    
    # 基本硬性當沖篩選
    filtered_df = df[
        (df['可當沖'] == True) &
        (df['成交張數'] >= min_volume) &
        (df['收盤價'] >= min_price) &
        (df['收盤價'] <= max_price)
    ].copy()
    
    if filtered_df.empty:
        print("經過基本流動性與價格區間過濾後，沒有剩餘股票。")
        return

    # 計算當沖核心得分 (Daytrade Score)
    # 算法邏輯：得分 = 振幅% * 2.0 + abs(漲跌幅%) * 1.5 + (log10(成交張數) * 1.0)
    # 這樣既能抓出高波動股票，又能確保高流動性股票獲得加權
    import numpy as np
    filtered_df['當沖評分'] = (
        filtered_df['振幅%'] * 2.0 + 
        filtered_df['漲跌幅%'].abs() * 1.5 + 
        np.log10(filtered_df['成交張數']) * 1.2
    )
    
    filtered_df['當沖評分'] = filtered_df['當沖評分'].round(2)
    
    # 排序並取前 50 強最適合當沖的標的
    ranked_df = filtered_df.sort_values(by='當沖評分', ascending=False).head(50)
    
    # 整理輸出欄位
    output_columns = [
        "代號", "名稱", "市場", "收盤價", "漲跌幅%", "成交張數", "振幅%", "均價", "當沖評分"
    ]
    final_pool = ranked_df[output_columns]
    
    # 建立輸出路徑
    os.makedirs('outputs', exist_ok=True)
    output_path = f'outputs/daytrade_candidates_ranked_{target_date}.csv'
    final_pool.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 印出前 10 名供 CLI 快速檢視
    print(f"\n===== {target_date} 前 10 名最適合下個交易日當沖候選池 =====")
    print(final_pool.head(10).to_string(index=False))
    print(f"\n完整 50 檔候選名單已輸出至: {output_path}")

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d")
    rank_candidates(target_date)

if __name__ == "__main__":
    main()