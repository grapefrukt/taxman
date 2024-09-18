import pandas as pd
from platforms.platform import *
import re

class PlatformSteam(Platform):
	@property
	def name(self) -> str:
		return 'steam'

	@property
	def data_extension(self) -> str:
		return '.htm'

	def download(self, month):
		pass

	def _parse(self, month):
		df = pd.read_html(self.month_to_path(month))
		df = df[0]

		# the table has multiple headers, this is annoying so we use this magic incantation to collapse them
		df.columns = df.columns.map('{0[1]}'.format)
		
		cols = ['Product (Id#)', 'Net Units Sold', 'Total']
		df = df.filter(cols)

		# rename some columns to better names
		df = df.rename(columns={
			'Product (Id#)' : 'title',
			'Net Units Sold' : 'units',
			'Total' : 'earned',
		})

		# the table has a summary row at the end with some missing values, this drops all lines with missing values
		df = df.dropna()

		df['title'] = df['title'].apply(self.remove_package_id)
		
		print(df)


		df2 = pd.read_csv(f'data/{self.name}/payments.csv', sep='\t')

		print(df2)

		return

		df['units'] = 0

		remap = {
			'com.grapefrukt.games.bore' : 'holedown',
			'com.grapefrukt.games.rymdkapsel1' : 'rymdkapsel',
		}
		df = df.replace({'Product Id': remap})
		df['Start Date'] = df['Start Date'].apply(self.shorten_date)

		df = df.rename(columns={
			'Start Date' : 'month',
			'Product Id' : 'title',
			'Amount (Merchant Currency)' : 'sek',
		})

		return ParseResult.OK, df

	def remove_package_id(self, str) -> str :
		return re.sub(r'\(\d+\)', '', str).lower().strip()
		#return re.sub(r' \(\d+\)', '', str)
