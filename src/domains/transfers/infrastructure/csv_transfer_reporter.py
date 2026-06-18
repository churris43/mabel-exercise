
from __future__ import annotations

import csv
import uuid
from decimal import Decimal
from pathlib import Path
from datetime import datetime

from domains.transfers.application.reporter import TransferReporter
from domains.transfers.domain.transfer import Transfer

class CsvTransferReporter(TransferReporter):
    """CSV adapter for the TransferReporter output port.

    Writes one row per transfer (with header) to a new timestamped
    ``transfer_report*.csv`` under the given directory, and returns its path.
    """

    def __init__(self, csv_path: str | Path = "storage/reports/"):
        self._path = Path(csv_path)
        
    def write(self, transfers: list[Transfer]) -> Path:
        formatted_now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        filename = "transfer_report_" + formatted_now + ".csv"
        # Create the output dir if it doesn't exist yet (e.g. on a fresh clone).
        self._path.mkdir(parents=True, exist_ok=True)
        full_path = self._path / filename
        with full_path.open("w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                    ["TransferID","FromAccountNumber","ToAccountNumber","Amount","Status","FailureReason"]
                )
            for transfer in transfers:
                writer.writerow(
                    [
                        # TODO: this id is minted fresh per write, so it can't be
                        # used to match a report row back to its transfer. Future:
                        # carry a TransferID on the source file and let Transfer
                        # own it, then write transfer.id here instead.
                        uuid.uuid4(),
                        transfer.from_account_number.value,
                        transfer.to_account_number.value,
                        str(transfer.amount),
                        transfer.status.value,
                        transfer.failure_reason or ""
                    ]
                )
        return full_path