from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from domains.transfers.application.reporter import TransferReporter
from domains.transfers.domain.transfer import Transfer


class JsonTransferReporter(TransferReporter):
    """JSON adapter for the TransferReporter output port.

    Writes a JSON array with one object per transfer to a new timestamped
    ``transfer_report*.json`` under the given directory, and returns its path.
    """

    def __init__(self, json_path: str | Path = "storage/reports/"):
        self._path = Path(json_path)

    def write(self, transfers: list[Transfer]) -> Path:
        formatted_now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        filename = "transfer_report_" + formatted_now + ".json"
        # Create the output dir if it doesn't exist yet (e.g. on a fresh clone).
        self._path.mkdir(parents=True, exist_ok=True)
        full_path = self._path / filename
        records = [
            {
                # TODO: this id is minted fresh per write, so it can't be
                # used to match a report row back to its transfer. Future:
                # carry a TransferID on the source file and let Transfer
                # own it, then write transfer.id here instead.
                "TransferID": str(uuid.uuid4()),
                "FromAccountNumber": transfer.from_account_number.value,
                "ToAccountNumber": transfer.to_account_number.value,
                "Amount": str(transfer.amount),
                "Status": transfer.status.value,
                "FailureReason": transfer.failure_reason or "",
            }
            for transfer in transfers
        ]
        with full_path.open("w") as file:
            json.dump(records, file, indent=2)
        return full_path
