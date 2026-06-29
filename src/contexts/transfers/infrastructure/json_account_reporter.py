from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from contexts.transfers.application.reporter import AccountReporter
from contexts.transfers.domain.account import Account


class JsonAccountReporter(AccountReporter):
    """JSON adapter for the AccountReporter output interface.

    Writes a JSON array with one ``{account_number, balance}`` object per account
    to a new timestamped ``account_balance_{datetime}.json`` under the given directory, and
    returns its path.
    """

    def __init__(self, json_path: str | Path = "storage/reports/"):
        self._path = Path(json_path)

    def write(self, accounts: list[Account]) -> Path:
        formatted_now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        filename = "account_balance_" + formatted_now + ".json"
        # Create the output dir if it doesn't exist yet (e.g. on a fresh clone).
        self._path.mkdir(parents=True, exist_ok=True)
        full_path = self._path / filename
        records = [
            {
                "AccountNumber": account.number.value,
                "Balance": str(account.balance.amount),
            }
            for account in accounts
        ]
        with full_path.open("w") as file:
            json.dump(records, file, indent=2)
        return full_path
