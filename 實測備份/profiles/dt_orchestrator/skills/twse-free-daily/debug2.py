
import csv

with open('raw_data/twse_fund_20260520.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    header = [h.strip() for h in header]
    row = next(reader)
    d = dict(zip(header, [c.strip() for c in row]))
    
    # Check
    total_idx = header.index('三大法人買賣超股數')
    print(f"total_idx = {total_idx}")
    print(f"row[total_idx] = '{row[total_idx]}'")
    print(f"d['三大法人買賣超股數'] = '{d.get('三大法人買賣超股數', 'MISSING')}'")
    print(f"d keys sample: {list(d.keys())[:3]}")
    print(f"row[4] = '{row[4]}'")  # 外陸資買賣超
