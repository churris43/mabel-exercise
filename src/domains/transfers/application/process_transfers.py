from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domains.transfers.domain.transfer import Transfer
from domains.transfers.domain.transfer_service import TransferService
from domains.transfers.infrastructure.csv_account_repository import CsvAccountRepository
from domains.transfers.infrastructure.csv_transfer_source import CsvTransferSource
from domains.transfers.infrastructure.csv_transfer_reporter import CsvTransferReporter


@dataclass
class TransferResult:
    """Outcome of one ProcessTransfers run: the processed transfers and the
    paths of the files written for them."""

    transfers: list[Transfer]
    balances_path: Path | None  # None when there were no accounts to save
    report_path: Path


class ProcessTransfers:
    """One day's run: load balances and transfers from CSV, process them, and
    write the updated balances and a transfer report.

    This is the single entry point wired up by main.py. It owns the I/O
    (which CSV adapters to use, where output goes); TransferService stays
    focused on the pure domain processing.
    """

    def __init__(
        self,
        account_csv_path: str | Path,
        transfers_csv_path: str | Path,
        output_path: str | Path = "storage/reports/",
    ):
        self._account_repo = CsvAccountRepository(account_csv_path, output_path)
        self._transfer_repo = CsvTransferSource(transfers_csv_path)
        self._reporter = CsvTransferReporter(output_path)

    def run(self) -> TransferResult:
        transfers = self._transfer_repo.load()
        results = TransferService(self._account_repo).process_batch(transfers)
        balances_path = self._account_repo.save()
        report_path = self._reporter.write(results)
        return TransferResult(results, balances_path, report_path)
