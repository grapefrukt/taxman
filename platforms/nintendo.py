import pandas as pd
from platforms.platform import *


class PlatformNintendo(Platform):
    @property
    def name(self) -> str:
        return 'nintendo'

    def download(self, month):
        pass

    def _parse(self, month):
        cols = ['Title', 'Sales Units', 'Final Payable Amount', 'Sales Period']
        df = pd.read_csv(self.month_to_path(month), usecols=cols)

        df = df.rename(columns={
            'Title': 'title',
            'Sales Units': 'units',
            'Final Payable Amount': 'sek',
            'Sales Period': 'month'
        })

        return ParseResult.OK, df
