from datetime import datetime
from io import StringIO
import pandas as pd
from platforms.platform import *
import re

class PlatformAppStore(Platform):
	@property
	def name(self) -> str:
		return 'appstore'

	# app store always needs two files to get the numbers we need
	def check_month_present(self, month:TaxMonth, index = -1) -> bool:
		if index == -1 :
			one = self.check_month_present(month, 0)
			two = self.check_month_present(month, 1)
			if one is not ParseResult.OK : return one
			if two is not ParseResult.OK : return two
			return ParseResult.OK
		else:
			return super().check_month_present(month, index)

	def download(self, month):
		pass

	def _parse(self, month):
		csv_payout = self.preprocess_payout(self.month_to_path(month, 0))
		
		io_payout = StringIO(csv_payout)
		df_payout = pd.read_csv(io_payout, usecols=['Country or Region (Currency)', 'Earned', 'Proceeds'])

		df_payout['Country or Region (Currency)'] = df_payout['Country or Region (Currency)'].apply(self.region_to_currency)

		df_payout = df_payout.rename(columns={
			'Country or Region (Currency)' : 'currency',
			'Earned' : 'earned',
			'Proceeds' : 'sek',
		})

		df_payout['exchange rate'] = df_payout['sek'] / df_payout['earned']
		
		print(df_payout)
		
		csv_sales = self.preprocess_sales(self.month_to_path(month, 1))
		io_sales = StringIO(csv_sales)
		df_sales  = pd.read_csv(io_sales, usecols=['Vendor Identifier', 'Quantity', 'Partner Share', 'Customer Currency'], sep='\t')

		remap = {
			'com.grapefrukt.games.bore' : 'holedown',
			'com.grapefrukt.games.twofold' : 'twofold',
			'com.grapefrukt.games.tilebreaker' : 'subpar pool',
			'com.grapefrukt.games.rymdkapsel1' : 'rymdkapsel',
			'extended-universe' : 'extended universe bundle',
		}

		df_sales = df_sales.rename(columns={
			'Vendor Identifier' : 'title',
			'Customer Currency' : 'currency',
			'Partner Share' : 'earned',
			'Quantity' : 'units',
		})

		df_sales = df_sales.replace({'title': remap})

		df_sales = df_sales.groupby(['title', 'currency'])
		df_sales = df_sales.agg({
			'units':'sum', 
			'earned':'sum',
		})
		df_sales.reset_index()

		print(df_sales)

		return

		# the description column contains a unique id per transaction, we group by that to get a sum for each transaction
		df = df.groupby('Description')
		df = df.agg({
			'Amount (Merchant Currency)':'sum', 
			'Product Title':'first',
			'Transaction Date': 'first'
		})

		# after the groupby and agg we turn this back into a normal dataframe
		df = df.reset_index()

		# we're now done with the description column and can drop it
		df = df.drop(columns=['Description'])
		# each row represents one sale
		df['units'] = 1

		df['platform'] = self.name
		df['Transaction Date'] = df['Transaction Date'].apply(self.format_date)
		df = df.rename(columns={
			'Product Title' : 'title',
			'Transaction Date' : 'month',
			'Product Id' : 'title',
			'Amount (Merchant Currency)' : 'sek',
		})

		return ParseResult.OK, df

	def preprocess_payout(self, path) -> str :
		processed = ''
		line_count = -1
		with open(path, 'r', encoding='utf8') as file:
			for line in file :
				line_count += 1
				# skip the first two lines, they're not interesting
				if line_count < 2 : continue 
				# once we reach an "empty" line, we bail
				if ',,,,,,,,,,,,' in line : break
				processed += line

		return processed

	def preprocess_sales(self, path) -> str :
		processed = ''
		with open(path, 'r', encoding='utf8') as file:
			for line in file :
				# once we reach the line that starts with 'Total_Rows' we bail
				if 'Total_Rows' in line : break
				processed += line

		return processed

	# the currency is in parenthesis at the end of the region, this function strips out just the currency abbreviation
	def region_to_currency(self, str) -> str :
		return str[-4:-1]

	def format_date(self, str) -> str :
		return datetime.strptime(str, '%b %d, %Y').strftime('%Y-%m')
