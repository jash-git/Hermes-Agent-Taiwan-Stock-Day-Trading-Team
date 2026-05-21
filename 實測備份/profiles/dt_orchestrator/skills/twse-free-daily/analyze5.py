
import csv

with open('raw_data/twse_fund_20260520.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    
    total_3 = 0
    total_foreign = 0
    total_invest = 0
    total_dealer = 0
    
    foreign_idx = header.index('外陸資買賣超股數(不含外資自營商)')
    invest_idx = header.index('投信買賣超股數')
    dealer_idx = header.index('自營商買賣超股數')
    total_idx = header.index('三大法人買賣超股數')
    
    for row in reader:
        if len(row) < len(header):
            continue
        try:
            t = int(row[total_idx].replace(',',''))
            fr = int(row[foreign_idx].replace(',',''))
            iv = int(row[invest_idx].replace(',',''))
            dl = int(row[dealer_idx].replace(',',''))
            total_3 += t
            total_foreign += fr
            total_invest += iv
            total_dealer += dl
        except:
            continue

print(f"三大法人合計買賣超: {total_3:,} 股")
print(f"外資及陸資(不含外資自營商): {total_foreign:,} 股")
print(f"投信: {total_invest:,} 股")
print(f"自營商(含避險): {total_dealer:,} 股")
