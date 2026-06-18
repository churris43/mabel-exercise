import csv
from decimal import Decimal
from pathlib import Path

from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.transfer import Transfer
from domains.transfers.domain.money import Money
from domains.transfers.domain.repositories import TransferSource

class CsvTransferSource(TransferSource):
    """CSV adapter for the TransferSource input port.

    Reads transfers from a CSV with columns ``from_account_number,
    to_account_number, amount`` (one transfer per row) and returns them as
    Transfer objects. Empty rows are skipped; any other malformed row aborts the
    load (see the note in ``load``).
    """

    def __init__(self, csv_path: str):
        self._path = Path(csv_path)
        
    
    def load(self) -> list[Transfer]:
        transfers: list[Transfer] = []
        with self._path.open(newline="") as file:
            # NOTE: this fails fast. A malformed row (invalid account number, bad
            # amount, wrong column count) raises and aborts the whole load — the
            # remaining rows are not processed. It does not skip the bad row and
            # continue. Empty rows are the only thing tolerated (skipped below).
            for row in csv.reader(file):
                if not row:
                    continue
                transfer = self._transfer_from_row(row)
                transfers.append(transfer)
        return transfers
    

    @staticmethod
    def _transfer_from_row(row: list[str]) -> Transfer:
        raw_from_account_number, raw_to_account_number, amount = (cell.strip() for cell in row)
        from_account_number = AccountNumber(raw_from_account_number)
        to_account_number = AccountNumber(raw_to_account_number)
        amount = Money(Decimal(amount))
        return Transfer(from_account_number, to_account_number, amount)