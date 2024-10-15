from abc import ABC, abstractmethod
import pandas as pd
import os


class Report(ABC):
    def __init__(self, config):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def modify_months(self, months, platforms):
        pass

    @abstractmethod
    def generate(self, months, platforms, df: pd.DataFrame) -> str:
        pass

    @property
    def data_path(self) -> str:
        return f"{self.config['data_path']}/reports/{self.name}"

    def write(self, month, platform, report):
        # make sure output folder exists
        directory = f'{self.data_path}'
        os.makedirs(directory, exist_ok=True)
        directory = f'{directory}/{platform}'
        os.makedirs(directory, exist_ok=True)

        with open(f"{directory}/{month}.txt", "w") as file:
            file.write(report)

    def format_currency_decimals(self, value) -> str:
        return '{:16,.2f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_currency(self, value) -> str:
        return '{:16,.0f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_units(self, value) -> str:
        return '{:10,.0f}'.format(value).replace(',', ' ').replace('.', ',')