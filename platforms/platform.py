from abc import ABC, abstractmethod
from enum import Enum
import os.path
import pandas as pd
from taxmonth import TaxMonth

class ParseResult(Enum):
	UNKNOWN  = 1
	OK       = 2 # file was parsed successfully
	EXCLUDED = 3 # file was not present, but wasn't supposed to be (sometimes happens when there are no sales for a month)
	MISSING  = 4 # file was not present, in a bad way

class Platform(ABC):
	def __init__(self, config):
		self.config = config

	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@property
	def data_extension(self) -> str:
		return '.csv'

	@property
	def data_path(self) -> str:
		return f"{self.config['data_path']}/{self.name}"

	@abstractmethod
	def download(self, month:TaxMonth) -> ParseResult:
		pass

	def parse(self, month:TaxMonth) -> (ParseResult, pd.DataFrame):
		if not self.check_month_present(month) : 
			return ParseResult.MISSING, None
		if self.check_month_excluded(month) : 
			return ParseResult.EXCLUDED, None
		return self._parse(month)

	@abstractmethod
	def _parse(self, month:TaxMonth) -> (ParseResult, pd.DataFrame):
		pass

	# if index is -1 we check all files that will be needed for this mont
	# if index is 0 we check the first file and so on
	# for most platforms except appstore, we need one or sometimes more files
	# for appstore we always need two
	def check_month_present(self, month:TaxMonth, index = -1) -> bool:
		return os.path.isfile(self.month_to_path(month, index))

	def check_month_excluded(self, month:TaxMonth, index = 0) -> bool:
		with open(self.month_to_path(month), 'r', encoding='utf8') as file:
			return 'EXCLUDED' in file.readline().rstrip().lstrip()

	def month_to_path(self, month:TaxMonth, index = 0) -> str:
		if index > 0 : return f"{self.data_path}/{month}-{index}.csv"
		return f"{self.data_path}/{month}{self.data_extension}"
