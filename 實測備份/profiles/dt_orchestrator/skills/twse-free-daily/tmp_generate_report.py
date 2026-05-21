#!/usr/bin/env python3
import json
import os

BASE = "/home/vblinux/.hermes/profiles/dt_orchestrator/skills/twse-free-daily"
json_path = os.path.join(BASE, "outputs/report_summary_20260521.json")
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

date = data.get('date', '20260521')
# Format date as YYYY/MM/DD for display
display_date = f"{date[:4]}/{date[4:6]}/{date[6:]}"

lines = []
lines.append(f"# 台股盤後分析報告 ({display_date})")
lines.append("")
lines.append("## 大盤指數")
for idx in data.get('indices', []):
    name = idx.get('name')
    close = idx.get('close')
    change = idx.get('change')
    pct = idx.get('pct')
    lines.append(f"- {name}: {close:.2f} ({change:+.2f}, {pct:+.2f}%)")
lines.append("")
lines.append("## 市場統計")
stats = data.get('market_stats', {})
lines.append(f"- 成交金額: {stats.get('value',0):,} 新台幣")
lines.append(f"- 成交股數: {stats.get('volume',0):,} 股")
lines.append(f"- 成交筆數: {stats.get('transactions',0):,} 筆")
lines.append("")
lines.append("## 漲跌家數")
updown = data.get('updown', {})
lines.append(f"- 加權指數上漲家數: {updown.get('twse_up',0)} 家")
lines.append(f"- 加權指數上漲家數 (含漲停): {updown.get('twse_up_limit',0)} 家")
lines.append(f"- 加權指數下跌家數: {updown.get('twse_down',0)} 家")
lines.append(f"- 加權指數下跌家數 (含跌停): {updown.get('twse_down_limit',0)} 家")
lines.append(f"- 加權指數持平家數: {updown.get('twse_flat',0)} 家")
lines.append(f"- 櫃買上漲家數: {updown.get('tpex_up',0)} 家")
lines.append(f"- 櫃買上漲家數 (含漲停): {updown.get('tpex_up_limit',0)} 家")
lines.append(f"- 櫃買下跌家數: {updown.get('tpex_down',0)} 家")
lines.append(f"- 櫃買下跌家數 (含跌停): {updown.get('tpex_down_limit',0)} 家")
lines.append(f"- 櫃買持平家數: {updown.get('tpex_flat',0)} 家")
lines.append("")
lines.append("## 類股指數 (漲幅前五)")
sector_top = data.get('sector_top5', [])
for s in sector_top:
    lines.append(f"- {s.get('name')}: {s.get('close'):.2f} ({s.get('change'):+.2f}, {s.get('pct'):+.2f}%)")
lines.append("")
lines.append("## 類股指數 (跌幅前五)")
sector_bottom = data.get('sector_bottom5', [])
for s in sector_bottom:
    lines.append(f"- {s.get('name')}: {s.get('close'):.2f} ({s.get('change'):+.2f}, {s.get('pct'):+.2f}%)")
lines.append("")
lines.append("## 三大法人買賣超彙總 (單位: 新台幣元)")
fund = data.get('fund_totals', {})
lines.append(f"- 外資: {fund.get('foreign',0):+,}")
lines.append(f"- 投信: {fund.get('invest',0):+,}")
lines.append(f"- 自營商: {fund.get('dealer',0):+,}")
lines.append(f"- 三大法人合計: {fund.get('total3',0):+,}")
lines.append("")
lines.append("## 外資及自營商買超前十名")
buy10 = data.get('fund_buy_top10', [])
for i, f in enumerate(buy10, 1):
    lines.append(f"{i}. {f.get('code')} {f.get('name')} : 買超 {f.get('total3'):+,}")
lines.append("")
lines.append("## 外資及自營商賣超前十名")
sell10 = data.get('fund_sell_top10', [])
for i, f in enumerate(sell10, 1):
    lines.append(f"{i}. {f.get('code')} {f.get('name')} : 賣超 {abs(f.get('total3',0)):+,}")
lines.append("")
lines.append("## 漲停股票 (前30名)")
limit_up = data.get('limit_up_stocks', [])
for i, s in enumerate(limit_up[:30], 1):
    lines.append(f"{i}. {s.get('code')} {s.get('name')} : 收盤 {s.get('close'):.2f} (漲幅 {s.get('chg_pct'):.2f}%)")
lines.append("")
lines.append("## 成交值前十大股票")
turnover = data.get('turnover_top10', [])
for i, t in enumerate(turnover, 1):
    lines.append(f"{i}. {t.get('code')} {t.get('name')} : 收盤 {t.get('close'):.2f} ({t.get('chg_pct'):+.2f}%), 成交值 {t.get('value_b'):.1f} 億")
lines.append("")
lines.append("## 盤勢總結")
# Simple summary based on index and fund flow
idx0 = data.get('indices', [{}])[0]
idx_change = idx0.get('change', 0)
foreign = fund.get('foreign',0)
invest = fund.get('invest',0)
dealer = fund.get('dealer',0)
summary = []
if idx_change < 0:
    summary.append("大盤今日下跌")
else:
    summary.append("大盤今日上漲")
if foreign < 0:
    summary.append("外資為賣超")
else:
    summary.append("外資為買超")
if invest < 0:
    summary.append("投信為賣超")
else:
    summary.append("投信為買超")
if dealer < 0:
    summary.append("自營商為賣超")
else:
    summary.append("自營商為買超")
lines.append("、".join(summary) + "。")
lines.append("")
lines.append("## 明日當沖標的建議 (參考今日前20名)")
daytrade = data.get('daytrade_top20', [])
for i, d in enumerate(daytrade[:20], 1):
    lines.append(f"{i}. {d.get('code')} {d.get('name')} ({d.get('market')}) : 收盤 {d.get('close'):.2f} ({d.get('chg_pct'):+.2f}%), 成交 {d.get('volume_lots'):,} 口, 振幅 {d.get('amplitude'):.2f}%, 評分 {d.get('score'):.2f}")
lines.append("")
lines.append("--")
lines.append("報告生成時間: 約 2026-05-21 17:00 (自動產出)")
output_path = os.path.join(BASE, "reports/twse_20260521_analysis.md")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print(f"Report written to {output_path}")