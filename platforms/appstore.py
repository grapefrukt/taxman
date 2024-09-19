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
		df_exchange = pd.read_csv(io_payout, usecols=['Country or Region (Currency)', 'Earned', 'Proceeds'])
		
		# rename the fields to be shorter
		df_exchange = df_exchange.rename(columns={
			'Country or Region (Currency)' : 'currency',
			'Earned' : 'earned',
			'Proceeds' : 'sek',
		})

		# shorten the region/currency field to be just currency
		df_exchange['currency'] = df_exchange['currency'].apply(self.region_to_currency)

		# some currencies (usd) appear multiple times, idk if they use a slightly different exchange rate
		# or if it's rounding, for our purposes, we can sum these and use them as one and the same
		df_exchange = df_exchange.groupby('currency')
		df_exchange = df_exchange.agg({
			'earned':'sum', 
			'sek':'sum',
		})

		# calculate the exchange rate per currency, this is why we loaded this data in the first place
		df_exchange['exchange rate'] = df_exchange['sek'] / df_exchange['earned']

		#print(df_exchange)
		
		csv_sales = self.preprocess_sales(self.month_to_path(month, 1))
		io_sales = StringIO(csv_sales)
		df_sales  = pd.read_csv(io_sales, usecols=['Vendor Identifier', 'Quantity', 'Extended Partner Share', 'Partner Share Currency'], sep='\t')

		# rename the fields to be shorter
		df_sales = df_sales.rename(columns={
			'Vendor Identifier' : 'title',
			'Partner Share Currency' : 'currency',
			'Extended Partner Share' : 'earned',
			'Quantity' : 'units',
		})

		# remap the game titles
		df_sales = df_sales.replace({'title': {
			'com.grapefrukt.games.bore' : 'holedown',
			'com.grapefrukt.games.twofold' : 'twofold',
			'tilebreaker' : 'subpar pool',
			'com.grapefrukt.games.rymdkapsel1' : 'rymdkapsel',
			'extended-universe' : 'extended universe bundle',
		}})

		# now we summarize the units and earnings per game per currency
		# we have to do it beforehand, because they may be cases where all sales for a currency were returned
		# in that case, the returned currency won't be in our lookup table and we'll have errors
		# this way, those transactions will zero out and we'll know it's okay that currency is missing
		df_sales = df_sales.groupby(['title', 'currency'])
		df_sales = df_sales.agg({
			'units':'sum', 
			'earned':'sum',
		})
		df_sales.reset_index(inplace=True)

		# use the payout lookup to work out how much each game earned in each currency
		df_sales['sek'] = df_sales.apply(lambda row: self.exchange_rate(row, df_exchange), axis=1)

		# then we collapse all the per-game-per-currency earnings down into just per game
		df_sales = df_sales.groupby(['title'])
		df_sales = df_sales.agg({	
			'units':'sum', 
			'sek' : 'sum',
		})
		
		# tag all rows with this month too
		df_sales['month'] = month

		# reset the index so we can merge with everything else later
		df_sales.reset_index(inplace=True)

		return ParseResult.OK, df_sales

	def exchange_rate(self, row, df_payout) :
		# if something is sold in a currency and then all of it is returned
		# that currency will be in the sales table, but not in the payout table (because that currency never got paid out)
		# it may also be that there's tax or something funky meaning had a negative pay out despite no sales
		# if the earned field is zero, we can safely return a zero exchange rate here
		if row['earned'] == 0 : return 0

		if not row['currency'] in df_payout.index :
			print(f"missing exchange data for {row['currency']}, {row['earned']}")
		# because this is an approximate value, we have to round it off here
		return round(row['earned'] * df_payout.loc[row['currency']]['exchange rate'], 2)

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