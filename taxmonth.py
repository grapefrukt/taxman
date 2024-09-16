from datetime import date
from dateutil.relativedelta import relativedelta

class TaxMonth:
    def __init__(self, year: int, month: int):
        self.date = date(year, month, 1)

    def __str__(self):
        # Format the year and month nicely when printed
        return f"{self.year}-{self.month:02}"

    @property
    def year(self):
        return self.date.year

    @property
    def month(self):
        return self.date.month

    def to_datetime(self):
        # Convert the YearMonth to a datetime object (with day set to 1)
        return self.date

    @classmethod
    def from_datetime(cls, dt: date):
        # Create a YearMonth object from a datetime object
        return cls(dt.year, dt.month)

    @classmethod
    def from_string(cls, date_str: str):
        # Split the string by the hyphen
        year, month = date_str.split('-')
        year = int(year)
        month = int(month)
        return cls(year, month)

    def add_months(self, months: int):
        new_date = self.date + relativedelta(months=months)
        return TaxMonth(new_date.year, new_date.month)