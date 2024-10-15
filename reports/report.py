from abc import ABC, abstractmethod
import pandas as pd


class Report(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def modify_months(self, months, platforms):
        pass

    @abstractmethod
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        pass

    def format_currency_decimals(self, value) -> str:
        return '{:16,.2f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_currency(self, value) -> str:
        return '{:16,.0f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_units(self, value) -> str:
        return '{:10,.0f}'.format(value).replace(',', ' ').replace('.', ',')