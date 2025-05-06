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
    
    def modify_months(self, months, platforms):
        return months

    def set_arguments(self, arguments):
        self.arguments = arguments

    @abstractmethod
    def generate(self, months, platforms, df: pd.DataFrame):
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
        if value == '' : return ''
        return '{:0,.2f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_currency(self, value) -> str:
        if value == '' : return ''
        return '{:0,.0f} SEK'.format(value).replace(',', ' ').replace('.', ',')

    def format_units(self, value) -> str:
        return '{:0,.0f}'.format(value).replace(',', ' ').replace('.', ',')