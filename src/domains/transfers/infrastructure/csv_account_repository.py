from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from datetime import datetime

from domains.transfers.domain.repositories import AccountRepository
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.account import Account
from domains.transfers.domain.money import Money
from domains.transfers.domain.exceptions import AccountNumberNotFoundError

class CsvAccountRepository(AccountRepository):
    """CSV-backed AccountRepository.

    Read side is a true repository: it loads accounts from ``csv_path`` and
    serves them by number via an in-memory identity map.

    Note that ``save()`` does not persist back to ``csv_path`` — it exports a
    snapshot of the (possibly mutated) balances to a new timestamped file under
    ``output_path``. The source CSV is treated as immutable input, so saved
    balances are never read back; a fresh instance always reloads the original
    ``csv_path``.
    """

    def __init__(self, csv_path: str, output_path: str | Path = "storage/reports/"):
        self._path = Path(csv_path)
        self._output_path = Path(output_path)
        self._accounts: dict[str, Account] | None = None
        
    
    def load(self) -> dict[str, Account]:
        if self._accounts is None:
            self._accounts = self._read_file()
        return self._accounts
    
    def _read_file(self) -> dict[str, Account]:
        accounts: dict[str, Account] = {}
        with self._path.open(newline="") as file:
            for row in csv.reader(file):
                if not row:
                    continue
                account = self._account_from_row(row)
                accounts[account.number.value] = account
                
        return accounts
    
    
    @staticmethod
    def _account_from_row(row: list[str]) -> Account:
        raw_number, raw_balance = (cell.strip() for cell in row)
        number = AccountNumber(raw_number)
        balance = Money(Decimal(raw_balance))
        return Account(number, balance)
    
    def save(self) -> Path | None:
        if self._accounts is None:
            return None
        formatted_now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        filename = "account_balance_" + formatted_now + ".csv"
        # Create the output dir if it doesn't exist yet (e.g. on a fresh clone).
        self._output_path.mkdir(parents=True, exist_ok=True)
        full_path = self._output_path / filename
        with full_path.open("w", newline="") as file:
            writer = csv.writer(file)
            for account in self._accounts.values():
                writer.writerow([account.number.value, str(account.balance.amount)])
        return full_path
    
    def get_by_number(self, number: AccountNumber):
        try:
            return self.load()[number.value]
        except KeyError:
            # Only a missing key means "not found"; other errors propagate as-is.
            # `from None` hides the internal KeyError from the traceback, so the
            # caller sees just AccountNumberNotFoundError, not the dict lookup detail.
            raise AccountNumberNotFoundError() from None