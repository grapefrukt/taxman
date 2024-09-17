from datetime import datetime
import pandas as pd
from platforms.platform import *

class PlatformPlayStore(Platform):
	@property
	def name(self) -> str:
		return 'play-store'

	def download(self, month):
		pass

	def _parse(self, month):
		df = pd.read_csv(self.month_to_path(month))
		cols = ['Description', 'Transaction Date', 'Product Title', 'Amount (Merchant Currency)']
		df = df.filter(cols)
		
		df = df.groupby('Description')
		df = df.agg({
			'Amount (Merchant Currency)':'sum', 
			'Product Title':'first',
			'Transaction Date': 'first'
		})
		df = df.reset_index()

		df = df.drop(columns=['Description'])
		df['units'] = 1

		df['platform'] = self.name
		df['Transaction Date'] = df['Transaction Date'].apply(self.format_date)
		df = df.rename(columns={
			'Product Title' : 'title',
			'Transaction Date' : 'month',
			'Product Id' : 'title',
			'Amount (Merchant Currency)' : 'sek',
		})

		print(df)

		return ParseResult.OK, df

	def format_date(self, str) -> str :
		return datetime.strptime(str, '%b %d, %Y').strftime('%Y-%m')
