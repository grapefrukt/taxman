from abc import ABC, abstractmethod
from enum import Enum
import os.path
from taxmonth import TaxMonth

class ParseResult(Enum):
	UNKNOWN  = 1
	OK       = 2 # file was parsed successfully
	EXCLUDED = 3 # file was not present, but wasn't supposed to be (sometimes happens when there are no sales for a month)
	MISSING  = 4 # file was not present, in a bad way


class Platform(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@abstractmethod
	def download(self, month:TaxMonth) -> ParseResult:
		pass

	def parse(self, month:TaxMonth) -> ParseResult:
		if not self.check_month_present(month) : 
			return ParseResult.MISSING
		if self.check_month_excluded(month) : 
			return ParseResult.EXCLUDED
		return self._parse(month)

	@abstractmethod
	def _parse(self, month:TaxMonth) -> ParseResult:
		pass

	def check_month_present(self, month:TaxMonth, index = 0) -> bool:
		return os.path.isfile(self.month_to_path(month))

	def check_month_excluded(self, month:TaxMonth, index = 0) -> bool:
		with open(self.month_to_path(month), 'r') as file:
			return 'EXCLUDED' in file.read().rstrip().lstrip()

	def month_to_path(self, month:TaxMonth, index = 0) -> str:
		return f'data/{self.name}/{month}.csv'
