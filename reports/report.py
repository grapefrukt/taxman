from abc import ABC, abstractmethod
import pandas as pd


class Report(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def generate(self, df: pd.DataFrame) -> str:
        pass

    def format_currency(self, value) -> str:
        return '{:16,.0f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_units(self, value) -> str:
        return '{:10,.0f}'.format(value).replace(',', ' ').replace('.', ',')