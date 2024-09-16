import pandas as pd
import re

paths = ['2023-12.htm', '2024-01.htm', '2024-02.htm', '2024-03.htm', '2024-04.htm', '2024-05.htm', '2024-06.htm', '2024-07.htm']

for path in paths:
	tables = pd.read_html('steam/' + path)
	table = tables[0]
	table = table.sort_values(by=('Product (Id#)', 'Product (Id#)'))
	
	first = True
	sum_total = 0
	for index, row in table.iterrows() :
		label = ''
		if first : label = path.replace('.htm', '')
		name = str(row['Product (Id#)'][0])
		name = re.sub(r'\(.*\)', '', name).lower().strip()
		value = row['Revenue Share'][0].replace(',', '').replace('.', ',').replace('$', '')
		if name == 'nan' : 
			sum_total = value
			continue
		print(label, ';', name, ';', value)
		first = False

	print(';', ';', sum_total)
	print('')