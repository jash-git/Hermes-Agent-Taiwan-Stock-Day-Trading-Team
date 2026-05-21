#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime
from string import Template

# 定義 Markdown 報告模板
MD_TEMPLATE = """# 每日台股當沖建議報告 ($date)

> **⚠️ 風險提示：** 本報告僅供學術研究與模擬交易參考，不構成任何投資建議。交易有風險，當沖請務必嚴格執行停損。
> *資料來源：台灣證券交易所 (TWSE) | 生成時間：$timestamp*

---

## 一、 市場總覽
* **大盤收盤指數：** $market_index ($market_change)
* **大盤成交量：** $market_volume 億
* **市場熱門族群：** $hot_sectors
* **整體當沖機會評估：** **$opportunity_level**
  * *評語：$market_comment*

---

## 二、 精選當沖候選名單 (Top $candidate_count)

| 排名 | 股號 | 股名 | 前日收盤 | 漲跌幅 | 振幅 | 成交量 | 量比 | 簡短理由 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
$candidate_rows

---

## 三、 風險提醒與注意事項
1. **量能維持：** 當沖核心在於流動性，若開盤後量能無法放大（或低於預估量），應放棄操作。
2. **波動度觀察：** 優先選擇振幅大且在關鍵價位（如突破昨日高點、回測均線）有支撐/壓力反應的個股。
3. **嚴守紀律：** 進場前務必設定好停損點（如 -1.5% 或跌破開盤低點），絕不留單過夜。

---

## 四、 審計軌跡 (Audit Trail)
* **資料日期：** $date
* **Hermes Skill 版本：** `report-builder v1.0.0`
* **篩選依據：** 經 `risk-filter` 完全過濾，排除處置股、變更交易方法及流動性不足之標的。
"""

# 定義 HTML 報告模板（含基本 CSS 美化）
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>每日台股當沖建議報告 - $date</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f8f9fa; }
        h1, h2, h3 { color: #1a252f; border-bottom: 2px solid #e9ecef; padding-bottom: 8px; }
        .disclaimer { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; margin-bottom: 20px; border-radius: 4px; font-weight: bold; color: #856404; }
        .meta { font-size: 0.9em; color: #6c757d; margin-top: -10px; margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 4px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; }
        th { background-color: #343a40; color: #ffffff; text-align: center; }
        tr:hover { background-color: #f1f3f5; }
        .text-center { text-align: center; }
        .up-color { color: #dc3545; font-weight: bold; }
        .down-color { color: #28a745; font-weight: bold; }
        .audit { background-color: #e9ecef; padding: 15px; border-radius: 4px; font-size: 0.9em; margin-top: 4px; }
    </style>
</head>
<body>

    <h1>每日台股當沖建議報告 ($date)</h1>
    <div class="meta">資料來源：台灣證券交易所 (TWSE) | 生成時間：$timestamp</div>

    <div class="disclaimer">
        ⚠️ 風險提示：本報告僅供學術研究與模擬交易參考，不構成任何投資建議。交易有風險，當沖請務必嚴格執行停損。
    </div>

    <h2>一、 市場總覽</h2>
    <ul>
        <li><strong>大盤收盤指數：</strong> $market_index ($market_change)</li>
        <li><strong>大盤成交量：</strong> $market_volume 億</li>
        <li><strong>市場熱門族群：</strong> $hot_sectors</li>
        <li><strong>整體當沖機會評估：</strong> <span style="color: #007bff; font-weight: bold;">$opportunity_level</span>
            <ul><li><em>評語：$market_comment</em></li></ul>
        </li>
    </ul>

    <h2>二、 精選當沖候選名單 (Top $candidate_count)</h2>
    <table>
        <thead>
            <tr>
                <th>排名</th>
                <th>股號</th>
                <th>股名</th>
                <th>前日收盤</th>
                <th>漲跌幅</th>
                <th>振幅</th>
                <th>成交量</th>
                <th>量比</th>
                <th>簡短理由</th>
            </tr>
        </thead>
        <tbody>
            $html_candidate_rows
        </tbody>
    </table>

    <h2>三、 風險提醒與注意事項</h2>
    <ol>
        <li><strong>量能維持：</strong> 當沖核心在於流動性，若開盤後量能無法放大（或低於預估量），應放棄操作。</li>
        <li><strong>波動度觀察：</strong> 優先選擇振幅大且在關鍵價位（如突破昨日高點、回測均線）有支撐/壓力反應的個股。</li>
        <li><strong>嚴守紀律：</strong> 進場前務必設定好停損點（如 -1.5% 或跌破開盤低點），絕不留單過夜。</li>
    </ol>

    <h2>四、 審計軌跡 (Audit Trail)</h2>
    <div class="audit">
        • <strong>資料日期：</strong> $date<br>
        • <strong>Hermes Skill 版本：</strong> <code>report-builder v1.0.0</code><br>
        • <strong>篩選依據：</strong> 經 <code>risk-filter</code> 完全過濾，排除處置股、變更交易方法及流動性不足之標的。
    </div>

</body>
</html>
"""


def load_mock_data():
    """模擬上游階段 (twse-free-daily & risk-filter) 傳入的資料"""
    # 實務上這些資料可以透過 sys.argv 傳入 json 檔案路徑讀取
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "market_summary": {
            "index": "21,500.25",
            "change": "+120.50 (+0.56%)",
            "volume": "4,120",
            "hot_sectors": "半導體、AI 伺服器、重電族群",
            "opportunity_level": "中高（適合積極偏多操作）",
            "comment": "大盤放量突破短均，多頭結構完整，熱門族群輪動流暢，適合尋找強勢股順勢當沖。"
        },
        "candidates": [
            {"rank": 1, "code": "2330", "name": "台積電", "close": "840.0", "change": "+2.4%", "amplitude": "3.1%", "volume": "32,450", "ratio": "1.4x", "reason": "權值股領漲且量能同步放大，尾盤有買盤強拉，隔日開盤易有延續性。"},
            {"rank": 2, "code": "2317", "name": "鴻海", "close": "175.0", "change": "+4.2%", "amplitude": "5.0%", "volume": "78,210", "ratio": "1.8x", "reason": "帶量突破箱型整理上緣，法人大買，內外盤內資追價意願強烈。"},
            {"rank": 3, "code": "2382", "name": "廣達", "close": "255.0", "change": "+1.8%", "amplitude": "4.2%", "volume": "21,040", "ratio": "1.1x", "reason": "AI 伺服器族群回溫，回測季線有撐，盤中振幅大適合現股當沖。"},
            {"rank": 4, "code": "1513", "name": "中興電", "close": "182.5", "change": "-1.5%", "amplitude": "6.2%", "volume": "15,400", "ratio": "1.5x", "reason": "重電族群劇烈震盪，雖收黑但留長下影線，隔日若開高有機會軋空。"}
        ]
    }


def generate_reports(input_data, output_dir="."):
    """根據輸入資料生成 Markdown 與 HTML 報告"""
    os.makedirs(output_dir, exist_ok=True)
    date_str = input_data["date"].replace("-", "")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    market = input_data["market_summary"]
    candidates = input_data["candidates"]
    
    # 1. 建立 Markdown 的表格資料
    md_rows = []
    for c in candidates:
        row = f"| {c['rank']} | {c['code']} | {c['name']} | {c['close']} | {c['change']} | {c['amplitude']} | {c['volume']} | {c['ratio']} | {c['reason']} |"
        md_rows.append(row)
    md_candidate_rows = "\n".join(md_rows)
    
    # 2. 建立 HTML 的表格資料
    html_rows = []
    for c in candidates:
        # 根據漲跌給予不同顏色樣式
        color_class = "up-color" if "+" in c['change'] else "down-color" if "-" in c['change'] else ""
        row = f"""            <tr>
                <td class="text-center">{c['rank']}</td>
                <td class="text-center">{c['code']}</td>
                <td class="text-center"><strong>{c['name']}</strong></td>
                <td class="text-center">{c['close']}</td>
                <td class="text-center <span class="math inline">\(color_class">{c['change']}</td>
                <td class="text-center">{c['amplitude']}</td>
                <td class="text-center">{c['volume']}</td>
                <td class="text-center">{c['ratio']}</td>
                <td>{c['reason']}</td>
            </tr>"""
        html_rows.append(row)
    html_candidate_rows = "\n".join(html_rows)
    
    # 3. 填入模板字典
    template_data = {
        "date": input_data["date"],
        "timestamp": timestamp_str,
        "market_index": market["index"],
        "market_change": market["change"],
        "market_volume": market["volume"],
        "hot_sectors": market["hot_sectors"],
        "opportunity_level": market["opportunity_level"],
        "market_comment": market["comment"],
        "candidate_count": len(candidates),
        "candidate_rows": md_candidate_rows,
        "html_candidate_rows": html_candidate_rows
    }
    
    # 4. 渲染並寫入檔案
    md_content = Template(MD_TEMPLATE).safe_substitute(template_data)
    html_content = Template(HTML_TEMPLATE).safe_substitute(template_data)
    
    md_filename = f"Daily_Daytrade_Report_{date_str}.md"
    html_filename = f"Daily_Daytrade_Report_{date_str}.html"
    
    md_path = os.path.join(output_dir, md_filename)
    html_path = os.path.join(output_dir, html_filename)
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"[Success] Markdown 報告已生成: {md_path}")
    print(f"[Success] HTML 報告已生成: {html_path}")


if __name__ == "__main__":
    print("=== Hermes 報告生成器啟動 ===")
    
    # 如果有外部帶入的 JSON 檔案則讀取，否則使用內建模擬資料
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"成功讀取外部資料來源: {sys.argv[1]}")
    else:
        print("未偵測到外部輸入檔案，載入模擬資料進行生成...")
        data = load_mock_data()
        
    # 執行報告生成（預設輸出在當前目錄下）
    generate_reports(data, output_dir=".")