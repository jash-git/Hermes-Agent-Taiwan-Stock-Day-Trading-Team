Hermes Agent 台股當沖標的篩選交易團隊(Hermes Agent Taiwan Stock Day Trading Team)

資料來源:
https://grok.com/share/bGVnYWN5LWNvcHk_069049f2-0a17-4603-ba23-347fa021ca0f
https://grok.com/share/bGVnYWN5LWNvcHk_6f2a9b8d-ef7f-4890-aa65-d0f011507372
https://gemini.google.com/share/262f8f66f8ea
	https://gemini.google.com/share/59173be6331d
https://gemini.google.com/share/ba74917a7b0a
	https://gemini.google.com/share/e32ee3c4251d
https://gemini.google.com/share/3715d1ea7a13
	https://gemini.google.com/share/e6ab294c67ce
https://chatgpt.com/share/6a0d5317-1000-8323-ae0f-88c4cb1ddc09
https://chatgpt.com/share/6a0d6173-ca90-8323-9426-c7f37a25bc03
	

提示詞備份:
	
我想要用 hermes agent 為基礎 設計一個以今天收盤交易資訊決定明日台股當沖交易團隊

幫我規劃後將所有會修改和產生的檔案(Profile/SOUL.md,SKILL.md,*.py)與對應於hermes目錄結構先繪製出來

其中 如果需要使用PYHTON設計TOOL  給 agent使用 我希望是使用特定SKILL明確指定方式 

====
	
hermes/
├─ profiles/
│ ├─ dt_orchestrator/
│ │ └─ SOUL.md
│ ├─ dt_analyst/
│ │ └─ SOUL.md
│ ├─ dt_screener/
│ │ └─ SOUL.md
│ └─ dt_writer/
│   └─ SOUL.md
│
├─ skills/
│ ├─ twse-free-daily/
│ │ ├─ SKILL.md
│ │ └─ tools/
│ │   ├─ fetch_twse_daily.py
│ │   ├─ fetch_daytrading_list.py
│ │   ├─ normalize_market_data.py
│ │   └─ rank_intraday_candidates.py
│ │
│ ├─ risk-filter/
│ │ ├─ SKILL.md
│ │ └─ tools/
│ │   └─ apply_risk_rules.py
│ │
│ └─ report-builder/
│   ├─ SKILL.md
│   └─ tools/
│     └─ build_report.py
│
├─ memory/
├─ configs/
└─ README.md

===

上面是你上次 規劃的 Hermes Agent 透過完全免費方式抓取最近一天的台股收盤交易資訊挑選出下一個交易日可當沖標的之交易團隊

現在就之前規劃內容理解之後 提供出可直接使用的 SOUL.md 內容

===

上面是你上次 規劃的 Hermes Agent 透過完全免費方式抓取最近一天的台股收盤交易資訊挑選出下一個交易日可當沖標的之交易團隊

現在就之前規劃內容理解之後 提供出可直接使用的 SKILL.md 內容

===

上面是你上次 規劃的 Hermes Agent 透過完全免費方式抓取最近一天的台股收盤交易資訊挑選出下一個交易日可當沖標的之交易團隊

以下是twse-free-daily/SKILL.md 內容

...
...

按照規劃 提供可直接使用的

fetch_twse_daily.py

fetch_daytrading_list.py

normalize_market_data.py

rank_intraday_candidates.py 的完整內容

===

上面4支 程式 相依函示庫安裝語法為何
	pip install requests pandas numpy
	
===

上面是你上次 規劃的 Hermes Agent 透過完全免費方式抓取最近一天的台股收盤交易資訊挑選出下一個交易日可當沖標的之交易團隊

以下是risk-filter/SKILL.md 內容

...
...

按照規劃 提供可直接使用的
apply_risk_rules.py

===

上面程式 相依函示庫安裝語法為何
	pip install pandas
	
===

上面是你上次 規劃的 Hermes Agent 透過完全免費方式抓取最近一天的台股收盤交易資訊挑選出下一個交易日可當沖標的之交易團隊

以下是report-builder/SKILL.md 內容

...
...

按照規劃 提供可直接使用的
build_report.py

===

上面程式 相依函示庫安裝語法為何
	由於這個 build_report.py 在設計時完全採用了 Python 的內建標準庫（如 os, sys, json, datetime, string），因此不需要安裝任何第三方相依函示庫
	
	
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# 01. hermes setup 
	設定 模型+API KEY : sk-or-v1-606ec3c3bb00d4763f9c1ddcc0e40f16…OOOOOOc2ace28a4ea4563263de3e05df85feab
	提問: 你是誰
	提問: 安裝下列PYTHON 套件 requests pandas numpy 給自己使用
		sudo apt install python3-pip python3-venv -y

		python3 -m venv myenv
		source myenv/bin/activate
		
		pip install --upgrade pip
		pip install requests pandas numpy
# 02.建立資料夾
mkdir -p ~/.hermes/skills/twse-free-daily
mkdir -p ~/.hermes/skills/twse-free-daily/tools
mkdir -p ~/.hermes/skills/risk-filter
mkdir -p ~/.hermes/skills/risk-filter/tools
mkdir -p ~/.hermes/skills/report-builder
mkdir -p ~/.hermes/skills/report-builder/tools
只把skills放在最外面

# 03.建立 profiles
hermes profile create dt_orchestrator --clone
hermes profile create dt_analyst --clone
hermes profile create dt_screener --clone
hermes profile create dt_writer --clone
hermes profile list

# 04.檔案內容複製
	SOUL.md則覆蓋對應檔案
	
# 05. VM重開機 [讓系統重新抓取SKILL和SOUL.md]

# 06. 測試主控
	hermes -p dt_orchestrator chat
		提示詞: 
				按照定義分工標準流程 進行今天的台股盤後分析，並提出明天可以進行當沖交易的標的給我
				如果還無法取得今天的台股盤後分析資料，請直接先終止後續動作並將情況告知
				
				按照定義分工標準流程 進行2026/05/20的台股盤後分析，並提出2026/05/21可以進行當沖交易的標的給我
				
				你是如何完成工作的