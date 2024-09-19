import pandas as pd
from platforms.platform import *


class PlatformPlayPass(Platform):
    @property
    def name(self) -> str:
        return 'play-pass'

    def download(self, month):
        pass

    def _parse(self, month):
        df = pd.read_csv(self.month_to_path(month))
        # todo: update to use usecols instead
        cols = ['Start Date', 'Product Id', 'Amount (Merchant Currency)']
        df = df.filter(cols)
        df['units'] = 0

        remap = {
            'com.grapefrukt.games.bore': 'holedown',
            'com.grapefrukt.games.rymdkapsel1': 'rymdkapsel',
        }
        df = df.replace({'Product Id': remap})
        df['Start Date'] = df['Start Date'].apply(self.shorten_date)

        df = df.rename(columns={
            'Start Date': 'month',
            'Product Id': 'title',
            'Amount (Merchant Currency)': 'sek',
        })

        return ParseResult.OK, df

    def shorten_date(self, str) -> str:
        return str[:7]
