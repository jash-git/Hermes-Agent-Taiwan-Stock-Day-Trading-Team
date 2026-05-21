
import csv

with open('raw_data/twse_fund_20260520.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    for i, h in enumerate(header):
        print(f"  [{i}] '{h}' repr={repr(h)}")
