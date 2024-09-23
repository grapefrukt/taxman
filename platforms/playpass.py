import pandas as pd
from platforms.platform import *


class PlatformPlayPass(Platform):
    @property
    def name(self) -> str:
        return 'play-pass'

    def download(self, month):
        pass

    def _parse(self, month):
        cols = ['Start Date', 'Product Id', 'Amount (Merchant Currency)']
        df = pd.read_csv(self.month_to_path(month), usecols=cols)
        df['units'] = 0

        df = df.replace({'Product Id': self.title_remap})
        df = df.rename(columns={
            'Product Id': 'title',
            'Amount (Merchant Currency)': 'sek',
        })

        return ParseResult.OK, df

    def shorten_date(self, str) -> str:
        return str[:7]
