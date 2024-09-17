from platforms.platform import *
import pandas as pd

class PlatformNintendo(Platform):
	@property
	def name(self) -> str:
		return 'nintendo'

	def download(self, month):
		pass

	def _parse(self, month):
		table = pd.read_csv(self.month_to_path(month))
		cols = ['Sales Units', 'Final Payable Amount']
		table = table.sort_values(by='Title')
		table = table.groupby(('Title'))
		table = table[cols].sum(numeric_only=True).reset_index()

		#for index, row in table.iterrows() :
		#	label = ''
		#	if first : label = f'{result.group(1)}-{result.group(2)}'
		#	print(f"{label};{row['Title']};{row['Sales Units']};{row['Final Payable Amount']:,2f}")
		#	first = False


		return ParseResult.OK
