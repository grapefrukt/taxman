import pandas as pd
import math
import yaml
from reports.report import *

class ReportRevshare(Report):

    @property
    def name(self) -> str:
        return 'revshare'
    
    def generate(self, months, platforms, df: pd.DataFrame):
        pd.set_option('display.max_rows', 500)
        pd.set_option('future.no_silent_downcasting', True)

        with open(f"{self.config['data_path']}/revshare.yaml", 'r') as file:
            self.revshare_map = yaml.safe_load(file)
        
        df = df.sort_values(self.arguments, ascending=True)
        df = df.reset_index()

        df = df[~df.title.str.contains('brazil withholding tax')]
        df = df[~df.title.str.contains('taiwan withholding tax')]
        
        table = pd.pivot_table(df, values=['sek'], index=['year', 'month', 'title'], columns=['platform'], aggfunc='sum', fill_value=0)
        df = table.reset_index()

        df['percentage'] = df['title'].map(self.percentage)
        df['revshare'] = df.apply(self.revshare, axis=1)

        cols_to_sum = []
        for col in list(df.columns.values):
            if col[0] == 'title' : continue
            if col[0] in ['year', 'month'] : 
                df[col] = df[col].map(lambda a: self.format_date(a))
                continue
            if col[0] == 'percentage' : 
                df[col] = df[col].map(lambda a: self.format_percent(a))
                continue

            df.at['total', col] = df[col].sum()
            df[col] = df[col].map(lambda a: self.format_currency(a))

        df.loc['total'] = df.loc['total'].fillna('')

        print(df)

        self.write(f'{months[0]} to {months[-1]}', '', df.to_csv())

    def percentage(self, title) :
        return self.revshare_map[title]
        
    def revshare(self, row) :
        total = 0
        for value in row['sek']:
            if value == '' : continue
            total += value
        return total * row['percentage']

    def format_currency(self, value) -> str:
        if value == '' : return ''
        if value == 0 : return ''
        return '{:0,.0f} kr'.format(value).replace(',', ' ').replace('.', ',')

    def format_percent(self, value) -> str:
        if value == '' : return ''
        if math.isnan(value) : return ''
        return f"{value:.0%}"

    def format_date(self, value) -> str:
        return f"{value:.0f}"