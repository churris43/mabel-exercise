from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from domains.transfers.domain.account import Account
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.exceptions import AccountNumberNotFoundError
from domains.transfers.domain.money import Money
from domains.transfers.domain.repositories import AccountRepository

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

    def __init__(self, csv_path: str | Path, output_path: str | Path = "storage/reports/"):
        #todo: Create a .env file so the default output_path can be overriden
        self._path = Path(csv_path)
        self._output_path = Path(output_path)
        # Identity map keyed by account number value (account.number.value);
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
        # row is a raw csv.reader list of unknown length; the unpacking enforces
        # the "exactly two columns" rule at runtime (raises ValueError otherwise).
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
        # load() caches the accounts on first call (the in-memory identity map),
        # so repeated lookups reuse the same Account instances rather than
        # re-reading the file — and any in-place debit/credit stays visible here.
        try:
            return self.load()[number.value]
        except KeyError:
            # Only a missing key means "not found"; other errors propagate as-is.
            # `from None` hides the internal KeyError from the traceback, so the
            # caller sees just AccountNumberNotFoundError, not the dict lookup detail.
            raise AccountNumberNotFoundError() from None