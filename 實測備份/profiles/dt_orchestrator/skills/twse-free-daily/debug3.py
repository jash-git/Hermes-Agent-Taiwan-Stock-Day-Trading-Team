
import csv

with open('raw_data/twse_fund_20260520.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    header = [h.strip() for h in header]
    
    foreign_idx = header.index('外陸資買賣超股數(不含外資自營商)')
    invest_idx = header.index('投信買賣超股數')
    dealer_idx = header.index('自營商買賣超股數')
    total_idx = header.index('三大法人買賣超股數')
    code_idx = header.index('證券代號')
    name_idx = header.index('證券名稱')
    
    total_3 = 0; total_foreign = 0; total_invest = 0; total_dealer = 0
    count = 0
    
    for row in reader:
        if len(row) < len(header):
            continue
        d = dict(zip(header, [c.strip() for c in row]))
        try:
            t = int(d['三大法人買賣超股數'].replace(',',''))
            fr = int(d['外陸資買賣超股數(不含外資自營商)'].replace(',',''))
            iv = int(d['投信買賣超股數'].replace(',',''))
            dl = int(d['自營商買賣超股數'].replace(',',''))
            total_3 += t
            total_foreign += fr
            total_invest += iv
            total_dealer += dl
            count += 1
        except Exception as e:
            if count < 3:
                print(f"Error on row {count}: {e}, code={d.get('證券代號','?')}")
            continue
    
    print(f"Processed {count} rows")
    print(f"Total3={total_3:,}, Foreign={total_foreign:,}, Invest={total_invest:,}, Dealer={total_dealer:,}")
