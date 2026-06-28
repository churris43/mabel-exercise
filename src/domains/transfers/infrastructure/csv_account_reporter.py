import csv
from datetime import datetime
from pathlib import Path

from domains.transfers.application.reporter import AccountReporter
from domains.transfers.domain.account import Account

class CsvAccountReporter(AccountReporter):
    """CSV adapter for the AccountReporter output port.

    Writes one ``account_number,balance`` row per account to a new timestamped
    ``account_balance*.csv`` under the given directory, and returns its path.
    No header, so the output round-trips back through CsvAccountRepository.
    """

    def __init__(self, csv_path: str | Path = "storage/reports/"):
        self._path = Path(csv_path)

    def write(self, accounts: list[Account]) -> Path:
        formatted_now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        filename = "account_balance_" + formatted_now + ".csv"
        # Create the output dir if it doesn't exist yet (e.g. on a fresh clone).
        self._path.mkdir(parents=True, exist_ok=True)
        full_path = self._path / filename
        with full_path.open("w", newline="") as file:
            writer = csv.writer(file)
            for account in accounts:
                writer.writerow([account.number.value, str(account.balance.amount)])
        return full_path