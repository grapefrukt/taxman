from abc import ABC, abstractmethod
from enum import Enum
import os.path
import pandas as pd
from taxmonth import TaxMonth


class ParseResult(Enum):
    UNKNOWN = 1
    OK = 2  # file was parsed successfully
    # file was not present, but wasn't supposed to be (sometimes happens when there are no sales for a month)
    EXCLUDED = 3
    MISSING = 4  # file was not present, in a bad way


class Platform(ABC):
    def __init__(self, config):
        self.config = config
        try:
            self.exclude_before = TaxMonth.from_string(self.config[self.name]['exclude_before'])
        except KeyError:
            self.exclude_before = None

        if self.exclude_before is not None:
            print(f'{self.name} exludes everything before: {self.exclude_before} (not inclusive)')

    def __str__(self):
        return self.name

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

    @property
    def title_remap(self) -> str:
        return self.config['title_remap']

    @abstractmethod
    def download(self, month: TaxMonth) -> ParseResult:
        pass

    def parse(self, month: TaxMonth) -> (ParseResult, pd.DataFrame):
        if self.check_month_excluded(month):
            return ParseResult.EXCLUDED, None
        if not self.check_month_present(month):
            return ParseResult.MISSING, None
        return self._parse(month)

    @abstractmethod
    def _parse(self, month: TaxMonth) -> (ParseResult, pd.DataFrame):
        pass

    # if index is -1 we check all files that will be needed for this mont
    # if index is 0 we check the first file and so on
    # for most platforms except appstore, we need one or sometimes more files
    # for appstore we always need two
    def check_month_present(self, month: TaxMonth, index=None) -> bool:
        return os.path.isfile(self.month_to_path(month, index))

    def check_month_excluded(self, month: TaxMonth, index=None) -> bool:
        # the platform may be configured to exclude everything before some month
        if self.exclude_before is not None:
            if month.is_before(self.exclude_before):
                return True

        # otherwise, the specific file may be flagged to exclude, if so, we
        # have to make sure there is a file in the first place, if there is no file
        # we return that the file is not excluded
        if not self.check_month_present(month, index):
            return False

        # otherwise we read the first line, if that line has EXCLUDED in it,
        # we return that it is indeed excluded
        with open(self.month_to_path(month), 'r', encoding='utf8') as file:
            return 'EXCLUDED' in file.readline().rstrip().lstrip()

    def month_to_path(self, month: TaxMonth, index=None) -> str:
        if index is not None:
            return f"{self.data_path}/{month}-{index}.csv"
        return f"{self.data_path}/{month}{self.data_extension}"
