import pandas as pd
import re

paths = ['2023-12-05T095543 DigitalSalesDetail_WEBBFARBROR_202311.csv', '2024-01-10T132805 DigitalSalesDetail_WEBBFARBROR_202312.csv', '2024-02-05T155845 DigitalSalesDetail_WEBBFARBROR_202401.csv', '2024-03-05T112108 DigitalSalesDetail_WEBBFARBROR_202402.csv', '2024-04-03T113912 DigitalSalesDetail_WEBBFARBROR_202403.csv', '2024-05-07T125037 DigitalSalesDetail_WEBBFARBROR_202404.csv', 'DigitalSalesDetail_WEBBFARBROR_202405.csv', 'DigitalSalesDetail_WEBBFARBROR_202406.csv', 'DigitalSalesDetail_WEBBFARBROR_202407.csv' ]


for path in paths:
	table = pd.read_csv('nintendo/' + path)
	cols = ['Sales Units', 'Final Payable Amount']
	table = table.sort_values(by='Title')
	table = table.groupby(('Title'))
	table = table[cols].sum(numeric_only=True).reset_index()

	result = re.search(r'.*(\d{4})(\d{2})\.csv', path)

	first = True
	for index, row in table.iterrows() :
		label = ''
		if first : label = f'{result.group(1)}-{result.group(2)}'
		print(f"{label};{row['Title']};{row['Sales Units']};{row['Final Payable Amount']:,2f}")
		first = False
