from typing import NamedTuple
from decimal import Decimal


class TransactionCollection:
    def __init__(self):
        self.sum = Decimal(0)
        self.count = int(0)
        self.paid = Decimal(0)

    def __str__(self):
        return f'sum: {self.sum}, count: {self.count}, paid: {self.paid}'


class TaxMonth(NamedTuple):
    year: str
    month: str

    def key(self):
        return f'{self.year}-{self.month}'


def format_currency(value):
    return '{:16,.2f} SEK'.format(value).replace(',', ' ').replace('.', ',')


def format_count(value):
    return '{:10,.0f} units'.format(value).replace(',', ' ').replace('.', ',')
